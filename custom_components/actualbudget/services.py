"""Services."""

from __future__ import annotations

from datetime import datetime

from actual.queries import get_transactions
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, ServiceResponse

from .actualbudget import from_config_entry

GET_TRANSACTIONS_SCHEMA = vol.Schema(
    {
        vol.Required("entry"): str,
        vol.Optional("account"): str,
        vol.Optional("category"): str,
        vol.Optional("start_date"): str,
        vol.Optional("end_date"): str,
        vol.Required("is_parent", default=False): bool,
    }
)


async def handle_get_transactions(call: ServiceCall) -> ServiceResponse:
    """Handle the action that gets transactions from Actual."""

    entry: ConfigEntry = call.hass.config_entries.async_get_entry(
        call.data.get("entry")
    )

    api = from_config_entry(call.hass, entry)

    start_date_string = call.data.get("start_date")
    end_date_string = call.data.get("end_date")

    start_date = (
        datetime.fromisoformat(start_date_string).date() if start_date_string else None
    )
    end_date = (
        datetime.fromisoformat(end_date_string).date() if end_date_string else None
    )

    def get_actual_transactions():
        actual = api.get_session()
        return get_transactions(
            actual.session,
            account=call.data.get("account"),
            category=call.data.get("category"),
            start_date=start_date,
            end_date=end_date,
            is_parent=call.data.get("is_parent"),
        )

    transactions = await call.hass.async_add_executor_job(get_actual_transactions)

    return {
        "transactions": [
            {
                "id": transaction.id,
                "payee": transaction.payee.name if transaction.payee else "",
                "category": transaction.category.name if transaction.category else "",
                "date": transaction.date,
                "amount": transaction.amount,
            }
            for transaction in transactions
        ]
    }
