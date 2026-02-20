import logging
import os
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_EXPORT_PATH,
    CONF_GLOBAL_INTERVAL,
    DATA_DB,
    DATA_ENTITY_MANAGER,
    DATA_EXPORT_ENGINE,
    DATA_PROFILE_MANAGER,
    DATA_SCHEDULER,
    DEFAULT_EXPORT_PATH,
    DEFAULT_GLOBAL_INTERVAL,
    DOMAIN,
)
from .database import Database
from .entity_manager import EntityManager
from .export_engine import ExportEngine
from .manual_export import ManualExportEngine
from .predefined_export import PredefinedExportEngine
from .profile_manager import ProfileManager
from .scheduler import Scheduler

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up History Archiver from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    global_interval = entry.options.get(
        CONF_GLOBAL_INTERVAL,
        entry.data.get(CONF_GLOBAL_INTERVAL, DEFAULT_GLOBAL_INTERVAL),
    )
    export_path = entry.options.get(
        CONF_EXPORT_PATH,
        entry.data.get(CONF_EXPORT_PATH, DEFAULT_EXPORT_PATH),
    )

    db = Database(hass)
    await db.async_initialize()

    entity_manager = EntityManager(hass, db)
    profile_manager = ProfileManager(hass, db)
    export_engine = ExportEngine(hass, db, export_path)
    scheduler = Scheduler(hass, db, entity_manager, global_interval)

    manual_export = ManualExportEngine(hass, db, profile_manager, export_engine)
    predefined_export = PredefinedExportEngine(hass, db, profile_manager, export_engine)

    hass.data[DOMAIN][DATA_DB] = db
    hass.data[DOMAIN][DATA_ENTITY_MANAGER] = entity_manager
    hass.data[DOMAIN][DATA_PROFILE_MANAGER] = profile_manager
    hass.data[DOMAIN][DATA_EXPORT_ENGINE] = export_engine
    hass.data[DOMAIN][DATA_SCHEDULER] = scheduler
    hass.data[DOMAIN]["manual_export"] = manual_export
    hass.data[DOMAIN]["predefined_export"] = predefined_export

    await scheduler.async_start()

    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    scheduler: Scheduler = hass.data[DOMAIN][DATA_SCHEDULER]
    await scheduler.async_stop()

    db: Database = hass.data[DOMAIN][DATA_DB]
    await db.async_close()

    hass.data.pop(DOMAIN, None)
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("History Archiver options updated, restarting scheduler")
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
