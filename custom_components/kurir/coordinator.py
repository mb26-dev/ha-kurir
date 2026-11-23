"""Data coordinator for Kurir: keeps the parcel list and polls the couriers."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .carriers import (
    CourierBlocked,
    CourierError,
    TrackResult,
    detect_carrier,
    fetch_etrackings,
    fetch_flash,
    fetch_spx,
    normalize_tracking_number,
    spx_country,
)
from .const import (
    CARRIER_FLASH,
    CARRIER_NAMES,
    CARRIER_SPX,
    CONF_COUNTRY,
    CONF_ETRACKINGS_KEY,
    CONF_ETRACKINGS_MONTHLY_LIMIT,
    CONF_ETRACKINGS_SECRET,
    CONF_KEEP_DELIVERED_DAYS,
    CONF_SCAN_INTERVAL,
    DEFAULT_ETRACKINGS_MONTHLY_LIMIT,
    DEFAULT_KEEP_DELIVERED_DAYS,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
    ETRACKINGS_COURIERS,
    EVENT_PARCEL_UPDATE,
    FLASH_HOSTS,
    FLASH_MAX_BATCH,
    SPX_HOSTS,
    STATUS_DELIVERED,
    STATUS_PENDING,
    STATUS_UNKNOWN,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

# A parcel is sent to the paid eTrackings fallback at most this often.
ETRACKINGS_MIN_GAP = timedelta(hours=6)


class KurirCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Holds all parcels of one Kurir entry and refreshes them."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        minutes = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
            config_entry=entry,
        )
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self.parcels: dict[str, dict[str, Any]] = {}
        self.etrackings_usage: dict[str, Any] = {"month": "", "count": 0}
        self.flash_blocked = False
        self.last_errors: list[str] = []
        self._removal_listeners: list[Any] = []

    # ------------------------------------------------------------------ config

    @property
    def country(self) -> str:
        return self.config_entry.data.get(CONF_COUNTRY, "th")

    @property
    def etrackings_key(self) -> tuple[str, str] | None:
        key = self.config_entry.data.get(CONF_ETRACKINGS_KEY) or ""
        secret = self.config_entry.data.get(CONF_ETRACKINGS_SECRET) or ""
        return (key, secret) if key and secret else None

    @property
    def etrackings_limit(self) -> int:
        return int(self.config_entry.options.get(CONF_ETRACKINGS_MONTHLY_LIMIT, DEFAULT_ETRACKINGS_MONTHLY_LIMIT))

    @property
    def keep_delivered_days(self) -> int:
        return int(self.config_entry.options.get(CONF_KEEP_DELIVERED_DAYS, DEFAULT_KEEP_DELIVERED_DAYS))

    # ----------------------------------------------------------------- storage

    async def async_load(self) -> None:
        """Load parcels from storage."""
        stored = await self._store.async_load() or {}
        self.parcels = stored.get("parcels", {})
        self.etrackings_usage = stored.get("etrackings_usage", {"month": "", "count": 0})

    async def _async_save(self) -> None:
        await self._store.async_save({"parcels": self.parcels, "etrackings_usage": self.etrackings_usage})

    async def async_remove_store(self) -> None:
        """Delete the storage file (entry removed)."""
        await self._store.async_remove()

    # ----------------------------------------------------------------- parcels

    @callback
    def async_add_removal_listener(self, listener: Any) -> None:
        """Register a callback(tracking_number) that runs when a parcel is removed."""
        self._removal_listeners.append(listener)

    async def async_add_parcel(self, tracking_number: str, name: str = "", carrier: str | None = None) -> bool:
        """Add a parcel. Returns False if it was already tracked (its name is updated)."""
        tn = normalize_tracking_number(tracking_number)
        if not tn:
            raise ValueError("Empty tracking number")
        carrier = carrier or detect_carrier(tn)
        if not carrier:
            raise ValueError(
                f"Cannot tell the courier of {tn}; pass carrier "
                f"(flash, spx, or an eTrackings courier: {', '.join(sorted(ETRACKINGS_COURIERS))})"
            )
        if tn in self.parcels:
            if name:
                self.parcels[tn]["name"] = name
                await self._async_save()
                self.async_update_listeners()
            return False
        self.parcels[tn] = {
            "tracking_number": tn,
            "name": name or tn,
            "carrier": carrier,
            "added": dt_util.utcnow().isoformat(),
            "track": None,
            "etrackings_last": "",
        }
        await self._async_save()
        self.async_update_listeners()
        await self.async_request_refresh()
        return True

    async def async_remove_parcel(self, tracking_number: str) -> bool:
        """Stop tracking a parcel."""
        tn = normalize_tracking_number(tracking_number)
        if tn not in self.parcels:
            return False
        self.parcels.pop(tn)
        await self._async_save()
        for listener in self._removal_listeners:
            listener(tn)
        self.async_update_listeners()
        return True

    def track_of(self, tracking_number: str) -> TrackResult | None:
        """Last known tracking state of a parcel."""
        parcel = self.parcels.get(tracking_number) or {}
        track = parcel.get("track")
        return TrackResult.from_dict(track) if track else None

    # ----------------------------------------------------------------- polling

    def _etrackings_allowed(self) -> bool:
        month = dt_util.now().strftime("%Y-%m")
        if self.etrackings_usage.get("month") != month:
            self.etrackings_usage = {"month": month, "count": 0}
        return self.etrackings_key is not None and self.etrackings_usage["count"] < self.etrackings_limit

    async def _query_etrackings(self, session: Any, tn: str, carrier: str) -> TrackResult | None:
        parcel = self.parcels[tn]
        last = _parse(parcel.get("etrackings_last") or "")
        if last and dt_util.utcnow() - last < ETRACKINGS_MIN_GAP:
            return None
        if not self._etrackings_allowed():
            return None
        courier_key = ETRACKINGS_COURIERS.get(carrier)
        if not courier_key:
            return None
        key, secret = self.etrackings_key  # type: ignore[misc]
        parcel["etrackings_last"] = dt_util.utcnow().isoformat()
        self.etrackings_usage["count"] += 1
        return await fetch_etrackings(session, key, secret, courier_key, tn, carrier)

    def _cleanup_delivered(self) -> list[str]:
        """Drop parcels delivered longer ago than the keep period."""
        days = self.keep_delivered_days
        if days <= 0:
            return []
        cutoff = dt_util.utcnow() - timedelta(days=days)
        old: list[str] = []
        for tn, parcel in self.parcels.items():
            track = parcel.get("track") or {}
            if track.get("status") != STATUS_DELIVERED:
                continue
            when = _parse(track.get("delivered_at") or track.get("time") or "")
            if when and when < cutoff:
                old.append(tn)
        return old

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Poll all couriers for the parcels that are not delivered yet."""
        for tn in self._cleanup_delivered():
            self.parcels.pop(tn, None)
            for listener in self._removal_listeners:
                listener(tn)

        session = async_get_clientsession(self.hass)
        errors: list[str] = []
        results: dict[str, TrackResult] = {}
        open_parcels = {
            tn: p for tn, p in self.parcels.items() if (p.get("track") or {}).get("status") != STATUS_DELIVERED
        }

        # Flash Express: one batch request for up to 20 numbers.
        flash = [tn for tn, p in open_parcels.items() if p["carrier"] == CARRIER_FLASH]
        flash_host = FLASH_HOSTS.get(self.country) or FLASH_HOSTS["th"]
        self.flash_blocked = False
        for start in range(0, len(flash), FLASH_MAX_BATCH):
            batch = flash[start : start + FLASH_MAX_BATCH]
            try:
                results.update(await fetch_flash(session, flash_host, batch))
            except CourierBlocked:
                self.flash_blocked = True
                _LOGGER.debug("Flash Express answered with its browser check; trying eTrackings if configured")
                for tn in batch:
                    try:
                        res = await self._query_etrackings(session, tn, CARRIER_FLASH)
                    except CourierError as err:
                        errors.append(str(err))
                        break
                    if res:
                        results[tn] = res
            except CourierError as err:
                errors.append(str(err))

        # Shopee Express: one request per parcel, on the SPX host of its country.
        for tn, parcel in open_parcels.items():
            if parcel["carrier"] != CARRIER_SPX:
                continue
            host = SPX_HOSTS[spx_country(tn, self.country)]
            try:
                res = await fetch_spx(session, host, tn)
            except (CourierBlocked, CourierError) as err:
                errors.append(str(err))
                continue
            if res:
                results[tn] = res

        # Everything else goes through eTrackings, if a key is configured.
        for tn, parcel in open_parcels.items():
            if parcel["carrier"] in (CARRIER_FLASH, CARRIER_SPX):
                continue
            try:
                res = await self._query_etrackings(session, tn, parcel["carrier"])
            except CourierError as err:
                errors.append(str(err))
                continue
            if res:
                results[tn] = res

        for tn, res in results.items():
            parcel = self.parcels.get(tn)
            if parcel is None:
                continue
            old = parcel.get("track") or {}
            new = res.as_dict()
            parcel["track"] = new
            if old.get("status") != new["status"] or old.get("time") != new["time"]:
                self._fire_event(parcel, old.get("status"), res)

        self.last_errors = errors
        if errors:
            _LOGGER.debug("Kurir update finished with errors: %s", errors)
        await self._async_save()
        return self.parcels

    def _fire_event(self, parcel: dict[str, Any], previous_status: str | None, res: TrackResult) -> None:
        self.hass.bus.async_fire(
            EVENT_PARCEL_UPDATE,
            {
                "tracking_number": res.tracking_number,
                "name": parcel.get("name") or res.tracking_number,
                "carrier": res.carrier,
                "carrier_name": CARRIER_NAMES.get(res.carrier, res.carrier),
                "status": res.status,
                "previous_status": previous_status,
                "event": res.event,
                "location": res.location,
                "time": res.time,
            },
        )

    # ----------------------------------------------------------------- summary

    def summary(self) -> list[dict[str, Any]]:
        """Compact parcel list for the summary sensor and the card."""
        rows: list[dict[str, Any]] = []
        for tn, parcel in self.parcels.items():
            track = parcel.get("track") or {}
            rows.append(
                {
                    "tracking_number": tn,
                    "name": parcel.get("name") or tn,
                    "carrier": parcel.get("carrier"),
                    "carrier_name": CARRIER_NAMES.get(parcel.get("carrier") or "", parcel.get("carrier")),
                    "status": track.get("status") or (STATUS_PENDING if track == {} else STATUS_UNKNOWN),
                    "step": track.get("step", 1),
                    "event": track.get("event", ""),
                    "location": track.get("location", ""),
                    "time": track.get("time", ""),
                    "delivered_at": track.get("delivered_at", ""),
                    "events": (track.get("events") or [])[:8],
                }
            )
        order = {"failed_attempt": 0, "out_for_delivery": 1, "in_transit": 2, "packed": 3, "pending": 4, "unknown": 5, "returned": 6, "delivered": 7}
        rows.sort(key=lambda r: (order.get(r["status"], 9), _neg_time(r["time"])))
        return rows


def _parse(value: str) -> datetime | None:
    """Parse an ISO time; naive values are taken as Home Assistant local time."""
    try:
        parsed = dt_util.parse_datetime(value) if value else None
    except ValueError:
        return None
    if parsed is not None and parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed


def _neg_time(value: str) -> float:
    """Sort helper: newest first."""
    parsed = _parse(value)
    return -parsed.timestamp() if parsed else 0.0
