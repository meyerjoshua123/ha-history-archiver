from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import now as ha_now

from .const import DOMAIN


class Scheduler:
    """Main heartbeat engine for History Archiver."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._unsub: Optional[callback] = None

    # ---------------------------------------------------------
    # START SCHEDULER
    # ---------------------------------------------------------
    def start(self):
        """Start the repeating heartbeat."""
        # Run every 30 seconds for now (we will make this dynamic later)
        interval = 30

        self._unsub = async_track_time_interval(
            self.hass,
            self._heartbeat,
            timedelta(seconds=interval),
        )

    # ---------------------------------------------------------
    # STOP SCHEDULER
    # ---------------------------------------------------------
    def stop(self):
        """Stop the heartbeat."""
        if self._unsub:
            self._unsub()
            self._unsub = None

    # ---------------------------------------------------------
    # HEARTBEAT LOOP
    # ---------------------------------------------------------
    async def _heartbeat(self, now):
        """Runs every X seconds."""
        profiles = self.hass.data[DOMAIN]["profiles"]
        entities = self.hass.data[DOMAIN]["entities"]

        # Load all profiles
        profile_list = profiles.load_profiles()

        # Load all entities
        entity_list = entities.load_entities()

        # -----------------------------------------------------
        # FUTURE: Detect new entities
        # -----------------------------------------------------
        # (We will implement this later)
        # -----------------------------------------------------

        # -----------------------------------------------------
        # FUTURE: Detect metadata changes
        # -----------------------------------------------------
        # (We will implement this later)
        # -----------------------------------------------------

        # -----------------------------------------------------
        # FUTURE: Sample entity states
        # -----------------------------------------------------
        # (We will implement this later)
        # -----------------------------------------------------

        # -----------------------------------------------------
        # FUTURE: Trigger rollover events
        # -----------------------------------------------------
        # (We will implement this later)
        # -----------------------------------------------------

        # -----------------------------------------------------
        # FUTURE: Trigger uploads
        # -----------------------------------------------------
        # (We will implement this later)
        # -----------------------------------------------------

        # For now, just log a heartbeat to the console
        print(f"[History Archiver] Heartbeat at {datetime.now().isoformat()}")
