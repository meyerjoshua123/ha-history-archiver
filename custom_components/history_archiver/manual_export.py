from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from .database import Database
from .export_engine import ExportEngine
from .profile_manager import ProfileManager


class ManualExportEngine:
    """Handles custom ad-hoc exports."""

    def __init__(
        self,
        hass: HomeAssistant,
        db: Database,
        profile_manager: ProfileManager,
        export_engine: ExportEngine,
    ) -> None:
        self._hass = hass
        self._db = db
        self._profiles = profile_manager
        self._export_engine = export_engine

    async def async_export_custom(
        self,
        entity_ids: list[str],
        start_ts: datetime,
        end_ts: datetime,
        resolution_seconds: int,
        formats: list[str],
        label: str = "manual",
    ) -> dict[str, Any]:
        return await self._export_engine.async_export(
            entity_ids,
            start_ts,
            end_ts,
            resolution_seconds,
            formats,
            label,
        )
