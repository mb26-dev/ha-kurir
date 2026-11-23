"""Sensors for Kurir: one summary sensor and one sensor per parcel."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import KurirConfigEntry
from .const import (
    CARRIER_NAMES,
    CONF_COUNTRY,
    COUNTRIES,
    DOMAIN,
    NAME,
    STATUS_DELIVERED,
    STATUS_PENDING,
    STATUS_STEP,
    STATUSES,
)
from .coordinator import KurirCoordinator

STATUS_ICONS = {
    "pending": "mdi:cart-outline",
    "packed": "mdi:package-variant-closed",
    "in_transit": "mdi:truck-delivery",
    "out_for_delivery": "mdi:truck-fast",
    "failed_attempt": "mdi:alert-circle-outline",
    "delivered": "mdi:package-variant-closed-check",
    "returned": "mdi:keyboard-return",
    "unknown": "mdi:package-variant",
}


async def async_setup_entry(
    hass: HomeAssistant, entry: KurirConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    """Create the summary sensor and one sensor per parcel; follow additions and removals."""
    coordinator = entry.runtime_data
    known: set[str] = set()

    async_add_entities([KurirSummarySensor(coordinator)])

    @callback
    def _add_new() -> None:
        new = [tn for tn in coordinator.parcels if tn not in known]
        if new:
            known.update(new)
            async_add_entities([KurirParcelSensor(coordinator, tn) for tn in new])

    @callback
    def _removed(tracking_number: str) -> None:
        known.discard(tracking_number)
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{entry.entry_id}_{tracking_number}")
        if entity_id:
            registry.async_remove(entity_id)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))
    coordinator.async_add_removal_listener(_removed)


def _device(coordinator: KurirCoordinator) -> DeviceInfo:
    entry = coordinator.config_entry
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=NAME,
        manufacturer="Kurir",
        model=f"Parcel tracking · {COUNTRIES.get(entry.data.get(CONF_COUNTRY, 'th'), '')}",
        entry_type=DeviceEntryType.SERVICE,
    )


class KurirSummarySensor(CoordinatorEntity[KurirCoordinator], SensorEntity):
    """Number of parcels on the way, with the full list for the Kurir card."""

    _attr_has_entity_name = True
    _attr_translation_key = "parcels"
    _attr_icon = "mdi:truck-fast"
    _attr_native_unit_of_measurement = "parcels"

    def __init__(self, coordinator: KurirCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_summary"
        self._attr_device_info = _device(coordinator)

    @property
    def native_value(self) -> int:
        return sum(1 for row in self.coordinator.summary() if row["status"] != STATUS_DELIVERED)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        rows = self.coordinator.summary()
        counts = {status: 0 for status in STATUSES}
        for row in rows:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        usage = self.coordinator.etrackings_usage
        return {
            "parcels": rows,
            "counts": counts,
            "flash_blocked": self.coordinator.flash_blocked,
            "etrackings_used_this_month": usage.get("count", 0) if self.coordinator.etrackings_key else None,
            "etrackings_limit": self.coordinator.etrackings_limit if self.coordinator.etrackings_key else None,
            "etrackings_quota_renews": self.coordinator.etrackings_period_end if self.coordinator.etrackings_key else None,
            "etrackings_today": (
                f"{usage.get('day_count', 0)}/{usage.get('day_quota', 0)}" if self.coordinator.etrackings_key else None
            ),
            "last_errors": self.coordinator.last_errors[:5],
        }


class KurirParcelSensor(CoordinatorEntity[KurirCoordinator], SensorEntity):
    """Status of one parcel."""

    _attr_has_entity_name = True
    _attr_translation_key = "parcel"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATUSES

    def __init__(self, coordinator: KurirCoordinator, tracking_number: str) -> None:
        super().__init__(coordinator)
        self._tn = tracking_number
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{tracking_number}"
        self._attr_device_info = _device(coordinator)

    @property
    def available(self) -> bool:
        return self._tn in self.coordinator.parcels

    @property
    def name(self) -> str:
        parcel = self.coordinator.parcels.get(self._tn) or {}
        return parcel.get("name") or self._tn

    @property
    def native_value(self) -> str:
        track = (self.coordinator.parcels.get(self._tn) or {}).get("track") or {}
        return track.get("status") or STATUS_PENDING

    @property
    def icon(self) -> str:
        return STATUS_ICONS.get(self.native_value, "mdi:package-variant")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        parcel = self.coordinator.parcels.get(self._tn) or {}
        track = parcel.get("track") or {}
        carrier = parcel.get("carrier") or ""
        return {
            "tracking_number": self._tn,
            "carrier": carrier,
            "carrier_name": CARRIER_NAMES.get(carrier, carrier),
            "step": track.get("step", STATUS_STEP.get(self.native_value, 1)),
            "event": track.get("event", ""),
            "location": track.get("location", ""),
            "event_time": track.get("time", ""),
            "delivered_at": track.get("delivered_at", ""),
            "source": track.get("source", ""),
            "added": parcel.get("added", ""),
            "events": (track.get("events") or [])[:10],
        }
