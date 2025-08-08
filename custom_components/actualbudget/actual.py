"""Actual API wrapper."""

from actual import Actual, Session
from actual.database import Transactions
from actual.queries import _transactions_base_query

from homeassistant.config_entries import ConfigEntry

from .const import (
    CONFIG_CERT,
    CONFIG_ENCRYPT_PASSWORD,
    CONFIG_ENDPOINT,
    CONFIG_FILE,
    CONFIG_PASSWORD,
)


def create_from_entry_config(entry: ConfigEntry):
    """Create an Actual instance from an entry config."""
    config = entry.data
    endpoint = config.get(CONFIG_ENDPOINT)
    password = config.get(CONFIG_PASSWORD)
    file = config.get(CONFIG_FILE)
    cert = config.get(CONFIG_CERT)
    if cert == "SKIP":
        cert = False
    encrypt_password = config.get(CONFIG_ENCRYPT_PASSWORD)
    return Actual(
        base_url=endpoint,
        password=password,
        file=file,
        cert=cert,
        encryption_password=encrypt_password,
    )


def get_transaction(session: Session, id: str) -> Transactions:
    """Get a transaction by id."""
    query = _transactions_base_query(session)
    query = query.filter(Transactions.id == id)
    return session.exec(query).first()
