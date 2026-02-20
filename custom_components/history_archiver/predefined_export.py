from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant

from .database import Database
from .export_engine import ExportEngine
from .profile_manager import ProfileManager


class PredefinedExportEngine:
    """Handles day/week/month/year and profile re-exports."""

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

    async def async_export_day(
        self,
        entity_ids: list[str],
        day: datetime,
        resolution_seconds: int,
        formats: list[str],
    ) -> dict[str, Any]:
        start = datetime(day.year, day.month, day.day, 0, 0, 0)
        end = start + timedelta(days=1) - timedelta(seconds=1)
        return await self._export_engine.async_export(
            entity_ids, start, end, resolution_seconds, formats, "day"
        )

    async def async_export_week(
        self,
        entity_ids: list[str],
        any_day_in_week: datetime,
        resolution_seconds: int,
        formats: list[str],
    ) -> dict[str, Any]:
        # ISO week: Monday as first day
        weekday = any_day_in_week.weekday()
        monday = any_day_in_week - timedelta(days=weekday)
        start = datetime(monday.year, monday.month, monday.day, 0, 0, 0)
        end = start + timedelta(days=7) - timedelta(seconds=1)
        return await self._export_engine.async_export(
            entity_ids, start, end, resolution_seconds, formats, "week"
        )

    async def async_export_month(
        self,
        entity_ids: list[str],
        year: int,
        month: int,
        resolution_seconds: int,
        formats: list[str],
    ) -> dict[str, Any]:
        start = datetime(year, month, 1, 0, 0, 0)
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        end = next_month - timedelta(seconds=1)
        return await self._export_engine.async_export(
            entity_ids, start, end, resolution_seconds, formats, "month"
        )

    async def async_export_year(
        self,
        entity_ids: list[str],
        year: int,
        resolution_seconds: int,
        formats: list[str],
    ) -> dict[str, Any]:
        start = datetime(year, 1, 1, 0, 0, 0)
        end = datetime(year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        return await self._export_engine.async_export(
            entity_ids, start, end, resolution_seconds, formats, "year"
        )
