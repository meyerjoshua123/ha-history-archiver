import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .database import Database
from .entity_manager import EntityManager

_LOGGER = logging.getLogger(__name__)


class Scheduler:
    """Global sampling scheduler."""

    def __init__(
        self,
        hass: HomeAssistant,
        db: Database,
        entity_manager: EntityManager,
        interval_seconds: int,
    ) -> None:
        self._hass = hass
        self._db = db
        self._entity_manager = entity_manager
        self._interval = timedelta(seconds=interval_seconds)
        self._unsub = None

    async def async_start(self) -> None:
        _LOGGER.info("Starting History Archiver scheduler at %ss", self._interval.total_seconds())
        self._unsub = async_track_time_interval(
            self._hass, self._async_tick, self._interval
        )

    async def async_stop(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    async def _async_tick(self, now: datetime) -> None:
        """Sample all entities at the global interval."""
        # Sync entities from registries (new devices/entities)
        await self._entity_manager.async_sync_entities()

        # For now, we sample all entities that exist in our DB.
        rows = await self._db.async_fetchall("SELECT entity_id FROM entities")
        entity_ids = [r[0] for r in rows]

        states = self._hass.states

        for entity_id in entity_ids:
            state = states.get(entity_id)
            if state is None:
                continue
            try:
                value = float(state.state)
            except (ValueError, TypeError):
                continue
            await self._entity_manager.async_record_sample(entity_id, value)
