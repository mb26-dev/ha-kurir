"""Courier clients and parsers for Kurir.

The parsers are plain functions without Home Assistant imports, so they can be
tested on their own. The fetch functions take an aiohttp ClientSession.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from .const import (
    CARRIER_ETRACKINGS,
    CARRIER_FLASH,
    CARRIER_SPX,
    ETRACKINGS_URL,
    MAX_EVENTS_STORED,
    SPX_HOSTS,
    STATUS_DELIVERED,
    STATUS_FAILED_ATTEMPT,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_PACKED,
    STATUS_PENDING,
    STATUS_RETURNED,
    STATUS_STEP,
)

_LOGGER = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Home Assistant; Kurir parcel tracking)"

try:
    from aiohttp import ClientTimeout

    REQUEST_TIMEOUT: Any = ClientTimeout(total=20)
except ImportError:  # the parsers stay importable without aiohttp (tests)
    REQUEST_TIMEOUT = 20

# Thai province names -> English, used for Flash Express and Thai SPX hubs.
THAI_PROVINCES: dict[str, str] = {
    "กรุงเทพมหานคร": "Bangkok",
    "กรุงเทพฯ": "Bangkok",
    "กรุงเทพ": "Bangkok",
    "กระบี่": "Krabi",
    "กาญจนบุรี": "Kanchanaburi",
    "กาฬสินธุ์": "Kalasin",
    "กำแพงเพชร": "Kamphaeng Phet",
    "ขอนแก่น": "Khon Kaen",
    "จันทบุรี": "Chanthaburi",
    "ฉะเชิงเทรา": "Chachoengsao",
    "ชลบุรี": "Chonburi",
    "ชัยนาท": "Chai Nat",
    "ชัยภูมิ": "Chaiyaphum",
    "ชุมพร": "Chumphon",
    "เชียงราย": "Chiang Rai",
    "เชียงใหม่": "Chiang Mai",
    "ตรัง": "Trang",
    "ตราด": "Trat",
    "ตาก": "Tak",
    "นครนายก": "Nakhon Nayok",
    "นครปฐม": "Nakhon Pathom",
    "นครพนม": "Nakhon Phanom",
    "นครราชสีมา": "Nakhon Ratchasima",
    "นครศรีธรรมราช": "Nakhon Si Thammarat",
    "นครสวรรค์": "Nakhon Sawan",
    "นนทบุรี": "Nonthaburi",
    "นราธิวาส": "Narathiwat",
    "น่าน": "Nan",
    "บึงกาฬ": "Bueng Kan",
    "บุรีรัมย์": "Buriram",
    "ปทุมธานี": "Pathum Thani",
    "ประจวบคีรีขันธ์": "Prachuap Khiri Khan",
    "ปราจีนบุรี": "Prachinburi",
    "ปัตตานี": "Pattani",
    "พระนครศรีอยุธยา": "Ayutthaya",
    "พะเยา": "Phayao",
    "พังงา": "Phang Nga",
    "พัทลุง": "Phatthalung",
    "พิจิตร": "Phichit",
    "พิษณุโลก": "Phitsanulok",
    "เพชรบุรี": "Phetchaburi",
    "เพชรบูรณ์": "Phetchabun",
    "แพร่": "Phrae",
    "ภูเก็ต": "Phuket",
    "มหาสารคาม": "Maha Sarakham",
    "มุกดาหาร": "Mukdahan",
    "แม่ฮ่องสอน": "Mae Hong Son",
    "ยโสธร": "Yasothon",
    "ยะลา": "Yala",
    "ร้อยเอ็ด": "Roi Et",
    "ระนอง": "Ranong",
    "ระยอง": "Rayong",
    "ราชบุรี": "Ratchaburi",
    "ลพบุรี": "Lopburi",
    "ลำปาง": "Lampang",
    "ลำพูน": "Lamphun",
    "เลย": "Loei",
    "ศรีสะเกษ": "Sisaket",
    "สกลนคร": "Sakon Nakhon",
    "สงขลา": "Songkhla",
    "สตูล": "Satun",
    "สมุทรปราการ": "Samut Prakan",
    "สมุทรสงคราม": "Samut Songkhram",
    "สมุทรสาคร": "Samut Sakhon",
    "สระแก้ว": "Sa Kaeo",
    "สระบุรี": "Saraburi",
    "สิงห์บุรี": "Sing Buri",
    "สุโขทัย": "Sukhothai",
    "สุพรรณบุรี": "Suphan Buri",
    "สุราษฎร์ธานี": "Surat Thani",
    "สุรินทร์": "Surin",
    "หนองคาย": "Nong Khai",
    "หนองบัวลำภู": "Nong Bua Lamphu",
    "อ่างทอง": "Ang Thong",
    "อำนาจเจริญ": "Amnat Charoen",
    "อุดรธานี": "Udon Thani",
    "อุตรดิตถ์": "Uttaradit",
    "อุทัยธานี": "Uthai Thani",
    "อุบลราชธานี": "Ubon Ratchathani",
}

_THAI_CHARS = re.compile(r"[฀-๿]")
_PROVINCE_IN_ADDRESS = re.compile(r"จังหวัด\s*(\S+)")
# Courier texts sometimes carry the driver's phone number; never keep it.
_PERSONAL = re.compile(r"phone|tel\b|โทร|\d{6,}", re.IGNORECASE)
_CLOCK_ONLY = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")

# Patterns used to recognise tracking numbers in free text.
_TN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (CARRIER_SPX, re.compile(r"(?<![A-Z0-9])(SPX(?:TH|MY|ID|VN|PH|SG)[0-9A-Z]{8,16})(?![A-Z0-9])")),
    (CARRIER_FLASH, re.compile(r"(?<![A-Z0-9])(TH[0-9]{2}[0-9A-Z]{9,13})(?![A-Z0-9])")),
    ("thaipost", re.compile(r"(?<![A-Z0-9])([A-Z]{2}[0-9]{9}TH)(?![A-Z0-9])")),
    ("kerry", re.compile(r"(?<![A-Z0-9])(KER[A-Z0-9]{8,14})(?![A-Z0-9])")),
]

FLASH_ACTIONS: dict[str, str] = {
    "RECEIVED": "Picked up by courier",
    "RECEIVE_WAREHOUSE_SCAN": "Arrived at hub",
    "ARRIVAL_WAREHOUSE_SCAN": "Arrived at hub",
    "SHIPMENT_WAREHOUSE_SCAN": "Departed hub",
    "DELIVERY_TICKET_CREATION_SCAN": "Out for delivery",
    "DELIVERY_MARKER": "Delivery attempt failed",
    "DELIVERY_CONFIRM": "Delivered",
    "DETAIN_WAREHOUSE": "Held at hub",
    "DIFFICULTY_HANDOVER": "Delivery problem reported",
    "CONTINUE_TRANSPORT": "Back in transit",
}

SPX_EVENTS: dict[str, str] = {
    "F000": "Label created, waiting for pickup",
    "F200": "Arrived at origin warehouse",
    "F299": "Departed origin warehouse",
    "F300": "Handed to air forwarder",
    "F339": "Cleared export customs",
    "F341": "Departed origin port",
    "F360": "Arrived in destination country",
    "F399": "Cleared import customs",
    "F419": "Handed to domestic courier",
    "F510": "Arrived at hub",
    "F540": "Departed hub",
    "F598": "Driver assigned",
    "F599": "Arrived at local hub",
    "F600": "Out for delivery",
}

ETRACKINGS_STATUS: dict[str, str] = {
    "ON_PENDING": STATUS_PACKED,
    "ON_PRE_TRANSIT": STATUS_PACKED,
    "ON_PICKED_UP": STATUS_IN_TRANSIT,
    "ON_SHIPPING": STATUS_OUT_FOR_DELIVERY,
    "ON_DELIVERED": STATUS_DELIVERED,
    "ON_RETURNED": STATUS_RETURNED,
    "ON_RETURN": STATUS_RETURNED,
    "ON_PROBLEM": STATUS_FAILED_ATTEMPT,
}

_FAIL_WORDS = ("fail", "unsuccessful", "not delivered", "problematic", "unable to deliver")


class CourierBlocked(Exception):
    """The courier answered with a bot check instead of data."""


class CourierError(Exception):
    """The courier request failed."""


class CourierNotFound(CourierError):
    """The courier (or eTrackings) does not know this tracking number (yet)."""


@dataclass
class TrackEvent:
    """One scan event of a parcel."""

    time: str
    event: str
    location: str = ""


@dataclass
class TrackResult:
    """Normalised tracking state of one parcel."""

    tracking_number: str
    carrier: str
    status: str = STATUS_PENDING
    event: str = ""
    location: str = ""
    time: str = ""
    delivered_at: str = ""
    source: str = ""
    events: list[TrackEvent] = field(default_factory=list)

    @property
    def step(self) -> int:
        """Progress step 1-4 for the card."""
        return STATUS_STEP.get(self.status, 1)

    def as_dict(self) -> dict[str, Any]:
        """Serialisable form (storage and attributes)."""
        data = asdict(self)
        data["step"] = self.step
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrackResult:
        """Rebuild from storage."""
        events = [
            TrackEvent(time=e.get("time", ""), event=scrub_event(e.get("event", "")), location=scrub_location(e.get("location", "")))
            for e in data.get("events", [])
        ]
        return cls(
            tracking_number=data["tracking_number"],
            carrier=data.get("carrier", ""),
            status=data.get("status", STATUS_PENDING),
            event=scrub_event(data.get("event", "")),
            location=scrub_location(data.get("location", "")),
            time=data.get("time", ""),
            delivered_at=data.get("delivered_at", ""),
            source=data.get("source", ""),
            events=events,
        )


# --------------------------------------------------------------------------
# Tracking number helpers
# --------------------------------------------------------------------------


def scrub_location(text: str) -> str:
    """Drop places that carry personal data (a driver's phone number)."""
    return "" if text and _PERSONAL.search(text) else (text or "")


def scrub_event(text: str) -> str:
    """An event that is only a clock time (older eTrackings parsing) becomes 'In transit'."""
    return "In transit" if text and _CLOCK_ONLY.match(text.strip()) else (text or "")


def normalize_tracking_number(value: str) -> str:
    """Upper-case and strip spaces and dashes."""
    return re.sub(r"[\s\-]", "", str(value or "")).upper()


def detect_carrier(tracking_number: str) -> str | None:
    """Guess the carrier from the shape of a tracking number."""
    tn = normalize_tracking_number(tracking_number)
    for carrier, pattern in _TN_PATTERNS:
        match = pattern.search(tn)
        if match and match.group(1) == tn:
            return carrier
    return None


def find_tracking_numbers(text: str) -> list[tuple[str, str]]:
    """Return (tracking_number, carrier) pairs found in free text, in order, without duplicates."""
    found: list[tuple[int, str, str]] = []
    upper = str(text or "").upper()
    for carrier, pattern in _TN_PATTERNS:
        for match in pattern.finditer(upper):
            found.append((match.start(1), match.group(1), carrier))
    found.sort()
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for _, tn, carrier in found:
        if tn not in seen:
            seen.add(tn)
            result.append((tn, carrier))
    return result


def spx_country(tracking_number: str, default_country: str) -> str:
    """Country of an SPX number (SPXTH..., SPXMY...), falling back to the configured one."""
    tn = normalize_tracking_number(tracking_number)
    code = tn[3:5].lower() if tn.startswith("SPX") else ""
    return code if code in SPX_HOSTS else default_country


def _thai_place(text: str) -> str:
    """Translate a Thai province name contained in text, else return ''."""
    for thai, english in THAI_PROVINCES.items():
        if thai in text:
            return english
    return ""


def _is_failure(text: str) -> bool:
    low = text.lower()
    return any(word in low for word in _FAIL_WORDS)


# --------------------------------------------------------------------------
# Shopee Express (SPX)
# --------------------------------------------------------------------------


def _spx_location(record: dict[str, Any]) -> str:
    """Readable place for an SPX record: current location, else '→ next location'."""
    for key, prefix in (("current_location", ""), ("next_location", "→ ")):
        loc = record.get(key) or {}
        address = loc.get("full_address") or ""
        name = (loc.get("location_name") or "").strip()
        place = ""
        province = _PROVINCE_IN_ADDRESS.search(address)
        if province:
            place = THAI_PROVINCES.get(province.group(1), "") or _thai_place(province.group(1))
        if not place and name:
            if _THAI_CHARS.search(name):
                place = _thai_place(name)
            else:
                place = name.title() if name.isupper() else name
        if place:
            return f"{prefix}{place}"
    return ""


def parse_spx(tracking_number: str, payload: dict[str, Any]) -> TrackResult | None:
    """Parse the JSON of /shipment/order/open/order/get_order_info."""
    if not isinstance(payload, dict) or payload.get("retcode") != 0:
        return None
    info = (payload.get("data") or {}).get("sls_tracking_info") or {}
    records = info.get("records")
    if not isinstance(records, list):
        return None
    visible = [r for r in records if r.get("display_flag") == 1]
    result = TrackResult(tracking_number=tracking_number, carrier=CARRIER_SPX, source="SPX")
    if not visible:
        result.status = STATUS_PENDING
        return result

    max_milestone = max(int(r.get("milestone_code") or 0) for r in visible)
    events: list[TrackEvent] = []
    for record in visible[:MAX_EVENTS_STORED]:
        text = f"{record.get('tracking_name') or ''} {record.get('buyer_description') or ''}"
        code = record.get("tracking_code") or ""
        milestone = (record.get("milestone_name") or "").lower()
        low = text.lower()
        if _is_failure(text):
            name = "Delivery attempt failed"
        elif milestone == "delivered" or ("delivered" in low and "out for" not in low):
            name = "Delivered"
        elif "returned to" in low or "return to sender" in low or "returning to seller" in low:
            name = "Returned to sender"
        else:
            name = SPX_EVENTS.get(code) or (record.get("tracking_name") or "In transit")
        stamp = int(record.get("actual_time") or 0)
        when = datetime.fromtimestamp(stamp, tz=UTC).isoformat() if stamp else ""
        events.append(TrackEvent(time=when, event=name, location=_spx_location(record)))

    latest = events[0]
    latest_record = visible[0]
    if latest.event == "Delivery attempt failed":
        status = STATUS_FAILED_ATTEMPT
    elif latest.event == "Delivered":
        status = STATUS_DELIVERED
    elif latest.event == "Returned to sender":
        status = STATUS_RETURNED
    elif latest_record.get("tracking_code") == "F600" or int(latest_record.get("milestone_code") or 0) == 6:
        status = STATUS_OUT_FOR_DELIVERY
    elif max_milestone >= 2:
        status = STATUS_IN_TRANSIT
    else:
        status = STATUS_PACKED

    result.status = status
    result.events = events
    result.event = latest.event
    result.location = latest.location
    result.time = latest.time
    if status == STATUS_DELIVERED:
        result.delivered_at = latest.time
    return result


async def fetch_spx(session: Any, host: str, tracking_number: str) -> TrackResult | None:
    """Query one SPX parcel."""
    url = f"https://{host}/shipment/order/open/order/get_order_info"
    params = {"spx_tn": tracking_number, "language_code": "en"}
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT}
    try:
        async with session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                raise CourierError(f"SPX HTTP {resp.status}")
            if "json" not in resp.headers.get("Content-Type", ""):
                raise CourierBlocked("SPX answered without JSON")
            payload = await resp.json(content_type=None)
    except (CourierBlocked, CourierError):
        raise
    except Exception as err:  # noqa: BLE001 - network errors of any kind
        raise CourierError(f"SPX request failed: {err}") from err
    return parse_spx(tracking_number, payload)


# --------------------------------------------------------------------------
# Flash Express
# --------------------------------------------------------------------------

_BRACKET = re.compile(r"【([^】]*)】")
_FLASH_TZ = timezone(timedelta(hours=7))


def _flash_time(value: str) -> str:
    """Flash reports local Thai time as 'YYYY-MM-DD HH:MM:SS'."""
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=_FLASH_TZ).isoformat()
    except (TypeError, ValueError):
        return ""


def _flash_place(message: str) -> str:
    names = _BRACKET.findall(message or "")
    if not names:
        return ""
    last = names[-1].strip()
    return THAI_PROVINCES.get(last) or _thai_place(last) or ("" if _THAI_CHARS.search(last) else last)


def parse_flash(payload: dict[str, Any]) -> dict[str, TrackResult]:
    """Parse the JSON of Flash Express /webApi/tools/tracking."""
    results: dict[str, TrackResult] = {}
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return results
    for item in data.get("list") or []:
        tn = normalize_tracking_number(item.get("pno_display") or item.get("pno") or "")
        if not tn:
            continue
        routes = item.get("routes") or []
        events = [
            TrackEvent(
                time=_flash_time(r.get("routed_at") or ""),
                event=FLASH_ACTIONS.get(r.get("route_action") or "")
                or (r.get("route_action") or "In transit").replace("_", " ").capitalize(),
                location=_flash_place(r.get("message") or ""),
            )
            for r in routes[:MAX_EVENTS_STORED]
        ]
        action = (routes[0].get("route_action") if routes else "") or ""
        state = int(item.get("state") or 0)
        if state == 5 or action == "DELIVERY_CONFIRM":
            status = STATUS_DELIVERED
        elif action == "DELIVERY_MARKER":
            status = STATUS_FAILED_ATTEMPT
        elif action == "DELIVERY_TICKET_CREATION_SCAN":
            status = STATUS_OUT_FOR_DELIVERY
        elif routes:
            status = STATUS_IN_TRANSIT
        else:
            status = STATUS_PACKED
        result = TrackResult(tracking_number=tn, carrier=CARRIER_FLASH, status=status, source="Flash", events=events)
        if events:
            result.event, result.location, result.time = events[0].event, events[0].location, events[0].time
        else:
            result.event = "Label created, waiting for pickup"
        if status == STATUS_DELIVERED:
            result.delivered_at = result.time
        results[tn] = result
    return results


async def fetch_flash(session: Any, host: str, tracking_numbers: list[str]) -> dict[str, TrackResult]:
    """Query up to 20 Flash parcels in one request.

    Flash sometimes answers with a browser check page instead of JSON. Kurir does
    not try to get around it; CourierBlocked is raised and the caller decides.
    """
    url = f"https://{host}/webApi/tools/tracking"
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": USER_AGENT}
    body = {"search": ",".join(tracking_numbers)}
    try:
        async with session.post(url, json=body, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "json" not in ctype:
                raise CourierBlocked("Flash Express answered with a browser check page")
            if resp.status != 200:
                raise CourierError(f"Flash HTTP {resp.status}")
            payload = await resp.json(content_type=None)
    except (CourierBlocked, CourierError):
        raise
    except Exception as err:  # noqa: BLE001
        raise CourierError(f"Flash request failed: {err}") from err
    return parse_flash(payload)


# --------------------------------------------------------------------------
# eTrackings (optional, needs a free API key)
# --------------------------------------------------------------------------


def parse_etrackings(tracking_number: str, carrier: str, payload: dict[str, Any]) -> TrackResult | None:
    """Parse the JSON of eTrackings /api/v3/tracks/find."""
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return None
    details: list[dict[str, Any]] = []
    for day in data.get("timelines") or []:
        details.extend(day.get("details") or [])
    events: list[TrackEvent] = []
    for d in details[:MAX_EVENTS_STORED]:
        desc = d.get("description") or ""
        st = d.get("status") or ""
        if _is_failure(desc):
            name = "Delivery attempt failed"
        elif st == "ON_DELIVERED":
            name = "Delivered"
        elif st == "ON_SHIPPING":
            name = "Out for delivery"
        elif st == "ON_PICKED_UP":
            name = "Picked up by courier"
        else:
            low = desc.lower()
            first = desc.split(" - ")[0].split(",")[0].strip()
            if "in transit from" in low or "departed" in low or "left the" in low:
                name = "Departed hub"
            elif "arriv" in low:
                name = "Arrived at hub"
            elif first and not _CLOCK_ONLY.match(first) and not _PERSONAL.search(first) and not _THAI_CHARS.search(first):
                name = first
            else:
                name = "In transit"
        segs = [s.strip() for s in desc.split(" - Shipping by")[0].split(",")]
        segs = [s for s in segs if s and not _PERSONAL.search(s)]
        place = _thai_place(segs[-1]) if len(segs) > 1 else ""
        if not place and len(segs) > 1 and not _THAI_CHARS.search(segs[-1]):
            place = segs[-1]
        events.append(TrackEvent(time=d.get("dateTime") or "", event=name, location=place))
    latest_text = (details[0].get("description") or "") if details else ""
    status = ETRACKINGS_STATUS.get(data.get("status") or "", STATUS_IN_TRANSIT if details else STATUS_PACKED)
    if _is_failure(latest_text):
        status = STATUS_FAILED_ATTEMPT
    result = TrackResult(tracking_number=tracking_number, carrier=carrier, status=status, source="eTrackings", events=events)
    if events:
        result.event, result.location, result.time = events[0].event, events[0].location, events[0].time
    if status == STATUS_DELIVERED:
        result.delivered_at = result.time
    return result


async def fetch_etrackings(
    session: Any, api_key: str, key_secret: str, courier_key: str, tracking_number: str, carrier: str
) -> TrackResult | None:
    """Query one parcel at eTrackings (counts against the monthly quota)."""
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en",
        "Content-Type": "application/json",
        "Etrackings-Api-Key": api_key,
        "Etrackings-Key-Secret": key_secret,
    }
    body = {"courier": courier_key, "trackingNo": tracking_number}
    try:
        async with session.post(ETRACKINGS_URL, json=body, headers=headers, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status in (401, 403):
                raise CourierError("eTrackings rejected the API key")
            if resp.status == 404:
                raise CourierNotFound(f"eTrackings does not know {tracking_number} yet")
            if resp.status == 429:
                raise CourierError("eTrackings quota exhausted")
            if resp.status != 200:
                raise CourierError(f"eTrackings HTTP {resp.status}")
            payload = await resp.json(content_type=None)
    except CourierError:
        raise
    except Exception as err:  # noqa: BLE001
        raise CourierError(f"eTrackings request failed: {err}") from err
    return parse_etrackings(tracking_number, carrier or CARRIER_ETRACKINGS, payload)
