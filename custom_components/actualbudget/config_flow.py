"""Config flow for actualbudget integration."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import voluptuous as vol

from homeassistant import config_entries

from .actualbudget import ActualBudget
from .const import (
    CONFIG_CERT,
    CONFIG_CURRENCY,
    CONFIG_ENCRYPT_PASSWORD,
    CONFIG_ENDPOINT,
    CONFIG_FILE,
    CONFIG_PASSWORD,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """actualbudget config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user interface."""
        dataSchema = vol.Schema(
            {
                vol.Required(CONFIG_ENDPOINT, default="http://localhost:5006"): str,
                vol.Required(CONFIG_PASSWORD): str,
                vol.Required(CONFIG_FILE): str,
                vol.Required(CONFIG_CURRENCY, default=self.hass.config.currency): str,
                vol.Optional(CONFIG_ENCRYPT_PASSWORD): str,
                vol.Optional(CONFIG_CERT): str,
            }
        )

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=dataSchema,
            )

        endpoint = user_input[CONFIG_ENDPOINT]
        domain = urlparse(endpoint).hostname
        port = urlparse(endpoint).port
        password = user_input[CONFIG_PASSWORD]
        file = user_input[CONFIG_FILE]
        cert = user_input.get(CONFIG_CERT)
        encrypt_password = user_input.get(CONFIG_ENCRYPT_PASSWORD)
        if cert == "SKIP":
            cert = False

        result = await self._test_connection(
            endpoint, password, file, cert, encrypt_password
        )
        if isinstance(result, str):
            return self.async_show_form(
                step_id="user", data_schema=dataSchema, errors={"base": result}
            )

        budgetName = result.get_metadata().get("budgetName")
        fileId = result.get_metadata().get("id")

        unique_id = user_input[CONFIG_ENDPOINT].lower() + "_" + fileId.lower()
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=budgetName if budgetName else f"{domain}:{port} {file}",
            data=user_input,
        )

    async def _test_connection(self, endpoint, password, file, cert, encrypt_password):
        """Return true if gas station exists."""
        api = ActualBudget(self.hass, endpoint, password, file, cert, encrypt_password)
        return await api.test_connection()
