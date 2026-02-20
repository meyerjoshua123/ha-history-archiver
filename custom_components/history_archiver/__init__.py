from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .database import initialize_database
from .profile_manager import ProfileManager
from .entity_manager import EntityManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the History Archiver integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize SQLite database and tables
    initialize_database(hass)

    # Create managers
    hass.data[DOMAIN]["profiles"] = ProfileManager(hass)
    hass.data[DOMAIN]["entities"] = EntityManager(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    # Remove managers
    hass.data[DOMAIN].pop("profiles", None)
    hass.data[DOMAIN].pop("entities", None)

    # Remove config entry data
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return True
