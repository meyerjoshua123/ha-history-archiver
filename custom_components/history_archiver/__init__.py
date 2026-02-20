from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .database import initialize_database
from .profile_manager import ProfileManager


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize the SQLite database
    initialize_database(hass)

    # Create the profile manager
    hass.data[DOMAIN]["profiles"] = ProfileManager(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload the integration."""
    hass.data[DOMAIN].pop("profiles", None)
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
