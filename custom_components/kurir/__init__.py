"""Kurir - last-mile parcel tracking for Southeast Asia."""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .carriers import find_tracking_numbers
from .const import (
    ATTR_CARRIER,
    ATTR_NAME,
    ATTR_TEXT,
    ATTR_TRACKING_NUMBER,
    CARD_URL,
    DOMAIN,
    SERVICE_ADD_FROM_TEXT,
    SERVICE_ADD_PARCEL,
    SERVICE_REFRESH,
    SERVICE_REMOVE_PARCEL,
)
from .coordinator import KurirCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type KurirConfigEntry = ConfigEntry[KurirCoordinator]

ADD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TRACKING_NUMBER): cv.string,
        vol.Optional(ATTR_NAME, default=""): cv.string,
        vol.Optional(ATTR_CARRIER): cv.string,
    }
)
ADD_TEXT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Optional(ATTR_NAME, default=""): cv.string,
    }
)
REMOVE_SCHEMA = vol.Schema({vol.Required(ATTR_TRACKING_NUMBER): cv.string})


def _coordinator(hass: HomeAssistant) -> KurirCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED:
            return entry.runtime_data
    raise HomeAssistantError("Kurir is not set up")


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the card and the services."""
    card = Path(__file__).parent / "frontend" / "kurir-card.js"
    await hass.http.async_register_static_paths([StaticPathConfig(CARD_URL, str(card), True)])
    add_extra_js_url(hass, f"{CARD_URL}?v=0.1.1")

    async def add_parcel(call: ServiceCall) -> ServiceResponse:
        coord = _coordinator(hass)
        try:
            added = await coord.async_add_parcel(
                call.data[ATTR_TRACKING_NUMBER], call.data.get(ATTR_NAME, ""), call.data.get(ATTR_CARRIER)
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        return {"added": added}

    async def add_from_text(call: ServiceCall) -> ServiceResponse:
        coord = _coordinator(hass)
        found = find_tracking_numbers(call.data[ATTR_TEXT])
        added: list[str] = []
        for tn, carrier in found:
            if await coord.async_add_parcel(tn, call.data.get(ATTR_NAME, ""), carrier):
                added.append(tn)
        return {"found": [tn for tn, _ in found], "added": added}

    async def remove_parcel(call: ServiceCall) -> ServiceResponse:
        coord = _coordinator(hass)
        removed = await coord.async_remove_parcel(call.data[ATTR_TRACKING_NUMBER])
        return {"removed": removed}

    async def refresh(call: ServiceCall) -> None:
        await _coordinator(hass).async_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_PARCEL, add_parcel, schema=ADD_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_ADD_FROM_TEXT, add_from_text, schema=ADD_TEXT_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_PARCEL, remove_parcel, schema=REMOVE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, refresh)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: KurirConfigEntry) -> bool:
    """Set up Kurir from a config entry."""
    coordinator = KurirCoordinator(hass, entry)
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: KurirConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: KurirConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: KurirConfigEntry) -> None:
    """Delete stored parcels when the entry is removed."""
    coordinator = KurirCoordinator(hass, entry)
    await coordinator.async_remove_store()
