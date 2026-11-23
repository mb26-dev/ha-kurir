"""Constants for the Kurir integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "kurir"
NAME: Final = "Kurir"

CONF_COUNTRY: Final = "country"
CONF_ETRACKINGS_KEY: Final = "etrackings_api_key"
CONF_ETRACKINGS_SECRET: Final = "etrackings_key_secret"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_KEEP_DELIVERED_DAYS: Final = "keep_delivered_days"
CONF_ETRACKINGS_MONTHLY_LIMIT: Final = "etrackings_monthly_limit"

DEFAULT_SCAN_INTERVAL_MIN: Final = 60
MIN_SCAN_INTERVAL_MIN: Final = 30
DEFAULT_KEEP_DELIVERED_DAYS: Final = 3
DEFAULT_ETRACKINGS_MONTHLY_LIMIT: Final = 45

# Country code -> public SPX (Shopee Express) tracking host.
# All of them run the same tracking platform; Thailand, Malaysia, Vietnam,
# the Philippines and Singapore are verified, Indonesia is unverified.
SPX_HOSTS: Final = {
    "th": "spx.co.th",
    "my": "spx.com.my",
    "id": "spx.co.id",
    "vn": "spx.vn",
    "ph": "spx.ph",
    "sg": "spx.sg",
}

COUNTRIES: Final = {
    "th": "Thailand",
    "my": "Malaysia",
    "id": "Indonesia",
    "vn": "Vietnam",
    "ph": "Philippines",
    "sg": "Singapore",
}

# Flash Express public tracking endpoint (Thailand only for now).
FLASH_HOSTS: Final = {
    "th": "www.flashexpress.com",
}
FLASH_MAX_BATCH: Final = 20

ETRACKINGS_URL: Final = "https://api.etrackings.com/api/v3/tracks/find"

CARRIER_FLASH: Final = "flash"
CARRIER_SPX: Final = "spx"
CARRIER_ETRACKINGS: Final = "etrackings"

CARRIER_NAMES: Final = {
    CARRIER_FLASH: "Flash Express",
    CARRIER_SPX: "Shopee Express",
    CARRIER_ETRACKINGS: "eTrackings",
}

# eTrackings courier keys for carriers Kurir can only reach through eTrackings.
ETRACKINGS_COURIERS: Final = {
    CARRIER_FLASH: "flash-express",
    "jt": "jt-express",
    "kerry": "kerry-express",
    "thaipost": "thailand-post",
    "dhl": "dhl-ecommerce",
    "ninjavan": "ninja-van",
    "best": "best-express",
}

# Parcel status values (also used as sensor enum options).
STATUS_PENDING: Final = "pending"
STATUS_PACKED: Final = "packed"
STATUS_IN_TRANSIT: Final = "in_transit"
STATUS_OUT_FOR_DELIVERY: Final = "out_for_delivery"
STATUS_FAILED_ATTEMPT: Final = "failed_attempt"
STATUS_DELIVERED: Final = "delivered"
STATUS_RETURNED: Final = "returned"
STATUS_UNKNOWN: Final = "unknown"

STATUSES: Final = [
    STATUS_PENDING,
    STATUS_PACKED,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_FAILED_ATTEMPT,
    STATUS_DELIVERED,
    STATUS_RETURNED,
    STATUS_UNKNOWN,
]

# Progress step for the card: 1 ordered/pending, 2 packed, 3 shipped, 4 delivered.
STATUS_STEP: Final = {
    STATUS_PENDING: 1,
    STATUS_PACKED: 2,
    STATUS_IN_TRANSIT: 3,
    STATUS_OUT_FOR_DELIVERY: 3,
    STATUS_FAILED_ATTEMPT: 3,
    STATUS_DELIVERED: 4,
    STATUS_RETURNED: 3,
    STATUS_UNKNOWN: 1,
}

EVENT_PARCEL_UPDATE: Final = "kurir_parcel_update"

SERVICE_ADD_PARCEL: Final = "add_parcel"
SERVICE_ADD_FROM_TEXT: Final = "add_from_text"
SERVICE_REMOVE_PARCEL: Final = "remove_parcel"
SERVICE_REFRESH: Final = "refresh"

ATTR_TRACKING_NUMBER: Final = "tracking_number"
ATTR_NAME: Final = "name"
ATTR_CARRIER: Final = "carrier"
ATTR_TEXT: Final = "text"

STORAGE_VERSION: Final = 1
MAX_EVENTS_STORED: Final = 20

CARD_URL: Final = "/kurir/kurir-card.js"
