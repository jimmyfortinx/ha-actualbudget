"""The actualbudget integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, SupportsResponse

from .const import DOMAIN
from .services import (
    CREATE_SPLIT_SCHEMA,
    GET_ACCOUNTS_SCHEMA,
    GET_TRANSACTIONS_SCHEMA,
    handle_create_splits,
    handle_get_accounts,
    handle_get_transactions,
)

__version__ = "1.1.0"
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the component from a config entry."""

    hass.data[DOMAIN] = entry

    # Register the service
    hass.services.async_register(
        DOMAIN,
        "get_transactions",
        handle_get_transactions,
        schema=GET_TRANSACTIONS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        "create_splits",
        handle_create_splits,
        schema=CREATE_SPLIT_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        "get_accounts",
        handle_get_accounts,
        schema=GET_ACCOUNTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_setup_entry(hass, entry)
