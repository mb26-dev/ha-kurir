"""Config and options flow for Kurir."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_COUNTRY,
    CONF_ETRACKINGS_KEY,
    CONF_ETRACKINGS_MONTHLY_LIMIT,
    CONF_ETRACKINGS_SECRET,
    CONF_KEEP_DELIVERED_DAYS,
    CONF_SCAN_INTERVAL,
    COUNTRIES,
    DEFAULT_ETRACKINGS_MONTHLY_LIMIT,
    DEFAULT_KEEP_DELIVERED_DAYS,
    DEFAULT_SCAN_INTERVAL_MIN,
    DOMAIN,
    MIN_SCAN_INTERVAL_MIN,
    NAME,
)

COUNTRY_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[SelectOptionDict(value=code, label=label) for code, label in COUNTRIES.items()],
        mode=SelectSelectorMode.DROPDOWN,
    )
)
SECRET = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))


def _country_default(hass_country: str | None) -> str:
    code = (hass_country or "").lower()
    return code if code in COUNTRIES else "th"


class KurirConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up Kurir."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        errors: dict[str, str] = {}
        if user_input is not None:
            key = (user_input.get(CONF_ETRACKINGS_KEY) or "").strip()
            secret = (user_input.get(CONF_ETRACKINGS_SECRET) or "").strip()
            if bool(key) != bool(secret):
                errors["base"] = "etrackings_incomplete"
            else:
                return self.async_create_entry(
                    title=NAME,
                    data={
                        CONF_COUNTRY: user_input[CONF_COUNTRY],
                        CONF_ETRACKINGS_KEY: key,
                        CONF_ETRACKINGS_SECRET: secret,
                    },
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_COUNTRY, default=_country_default(self.hass.config.country)): COUNTRY_SELECTOR,
                vol.Optional(CONF_ETRACKINGS_KEY, default=""): SECRET,
                vol.Optional(CONF_ETRACKINGS_SECRET, default=""): SECRET,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            key = (user_input.get(CONF_ETRACKINGS_KEY) or "").strip()
            secret = (user_input.get(CONF_ETRACKINGS_SECRET) or "").strip()
            if bool(key) != bool(secret):
                errors["base"] = "etrackings_incomplete"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={CONF_COUNTRY: user_input[CONF_COUNTRY], CONF_ETRACKINGS_KEY: key, CONF_ETRACKINGS_SECRET: secret},
                )
        schema = vol.Schema(
            {
                vol.Required(CONF_COUNTRY, default=entry.data.get(CONF_COUNTRY, "th")): COUNTRY_SELECTOR,
                vol.Optional(CONF_ETRACKINGS_KEY, default=entry.data.get(CONF_ETRACKINGS_KEY, "")): SECRET,
                vol.Optional(CONF_ETRACKINGS_SECRET, default=entry.data.get(CONF_ETRACKINGS_SECRET, "")): SECRET,
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return KurirOptionsFlow()


class KurirOptionsFlow(OptionsFlow):
    """Polling interval, keep period and eTrackings budget."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={k: int(v) for k, v in user_input.items()},
            )
        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MIN)
                ): NumberSelector(
                    NumberSelectorConfig(min=MIN_SCAN_INTERVAL_MIN, max=360, step=5, unit_of_measurement="min", mode=NumberSelectorMode.BOX)
                ),
                vol.Required(
                    CONF_KEEP_DELIVERED_DAYS, default=opts.get(CONF_KEEP_DELIVERED_DAYS, DEFAULT_KEEP_DELIVERED_DAYS)
                ): NumberSelector(NumberSelectorConfig(min=0, max=30, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)),
                vol.Required(
                    CONF_ETRACKINGS_MONTHLY_LIMIT,
                    default=opts.get(CONF_ETRACKINGS_MONTHLY_LIMIT, DEFAULT_ETRACKINGS_MONTHLY_LIMIT),
                ): NumberSelector(NumberSelectorConfig(min=0, max=10000, step=1, mode=NumberSelectorMode.BOX)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
