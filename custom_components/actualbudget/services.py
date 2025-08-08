"""Services."""

from __future__ import annotations

from datetime import datetime
import logging

from actual.queries import create_split, get_accounts, get_category, get_transactions
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, ServiceResponse

_LOGGER = logging.getLogger(__name__)

from .actual import create_from_entry_config, get_transaction
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

    _LOGGER.debug(f"transactions {transactions}")

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


CREATE_SPLIT_SCHEMA = vol.Schema(
    {
        vol.Required("entry"): str,
        vol.Required("transaction"): str,
        vol.Required("splits"): vol.All(
            [
                vol.Schema(
                    {
                        vol.Optional("category"): str,
                        vol.Required("amount"): int,
                    }
                )
            ],
            vol.Length(min=1),
        ),
    }
)


async def handle_create_splits(call: ServiceCall) -> ServiceResponse:
    """Handle the action to split a transaction to Actual."""

    entry: ConfigEntry = call.hass.config_entries.async_get_entry(
        call.data.get("entry")
    )

    def execute():
        with create_from_entry_config(entry) as actual:
            parent = get_transaction(actual.session, call.data.get("transaction"))
            splits_data = call.data.get("splits", [])

            created_splits = []

            for split_data in splits_data:
                split_transaction = create_split(
                    actual.session, transaction=parent, amount=0
                )
                split_transaction.amount = split_data["amount"]

                # If category is provided, set it; otherwise use parent's category
                if split_data.get("category"):
                    category = get_category(actual.session, split_data["category"])
                    if category:
                        split_transaction.category_id = category.id
                else:
                    split_transaction.category_id = parent.category_id

            # Mark parent as having splits and clear its category
            parent.is_parent = 1
            parent.category_id = None

            actual.commit()

            return {
                "transaction": [
                    {
                        "id": split.id,
                        "amount": split.amount,
                        "category": split.category.name if split.category else None,
                    }
                    for split in created_splits
                ]
            }

    return await call.hass.async_add_executor_job(execute)


GET_ACCOUNTS_SCHEMA = vol.Schema(
    {
        vol.Required("entry"): str,
        vol.Optional("account"): str,
    }
)


async def handle_get_accounts(call: ServiceCall) -> ServiceResponse:
    """Handle the action to get accounts from Actual."""

    entry: ConfigEntry = call.hass.config_entries.async_get_entry(
        call.data.get("entry")
    )

    def execute():
        with create_from_entry_config(entry) as actual:
            accounts = get_accounts(actual.session, call.data.get("account"))

            return {
                "accounts": [
                    {
                        "id": account.id,
                        "name": account.name,
                        "balance": float(account.balance),
                    }
                    for account in accounts
                ]
            }

    return await call.hass.async_add_executor_job(execute)
