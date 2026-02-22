from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_EXPORT_PATH,
    CONF_GLOBAL_INTERVAL,
    DEFAULT_GLOBAL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Your desired default export path
DEFAULT_UI_EXPORT_PATH = "config/www/community/ha-history-archiver"


class HistoryArchiverConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for History Archiver."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            interval = user_input.get(CONF_GLOBAL_INTERVAL)
            if not isinstance(interval, int) or interval < 1:
                errors[CONF_GLOBAL_INTERVAL] = "invalid_interval"

            if not errors:
                return self.async_create_entry(
                    title="History Archiver",
                    data={
                        CONF_GLOBAL_INTERVAL: interval,
                        CONF_EXPORT_PATH: user_input.get(
                            CONF_EXPORT_PATH, DEFAULT_UI_EXPORT_PATH
                        ),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_GLOBAL_INTERVAL,
                    default=DEFAULT_GLOBAL_INTERVAL,
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_EXPORT_PATH,
                    default=DEFAULT_UI_EXPORT_PATH,
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "recommended": "Recommended: 10s",
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return HistoryArchiverOptionsFlow(config_entry)


class HistoryArchiverOptionsFlow(config_entries.OptionsFlow):
    """Options flow for History Archiver."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            interval = user_input.get(CONF_GLOBAL_INTERVAL)
            if not isinstance(interval, int) or interval < 1:
                errors[CONF_GLOBAL_INTERVAL] = "invalid_interval"

            if not errors:
                return self.async_create_entry(
                    title="Options",
                    data={
                        CONF_GLOBAL_INTERVAL: interval,
                        CONF_EXPORT_PATH: user_input.get(
                            CONF_EXPORT_PATH,
                            self._config_entry.data.get(
                                CONF_EXPORT_PATH, DEFAULT_UI_EXPORT_PATH
                            ),
                        ),
                    },
                )

        current_interval = self._config_entry.options.get(
            CONF_GLOBAL_INTERVAL,
            self._config_entry.data.get(
                CONF_GLOBAL_INTERVAL, DEFAULT_GLOBAL_INTERVAL
            ),
        )
        current_export_path = self._config_entry.options.get(
            CONF_EXPORT_PATH,
            self._config_entry.data.get(CONF_EXPORT_PATH, DEFAULT_UI_EXPORT_PATH),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_GLOBAL_INTERVAL,
                    default=current_interval,
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_EXPORT_PATH,
                    default=current_export_path,
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "recommended": "Recommended: 10s",
            }
        )
