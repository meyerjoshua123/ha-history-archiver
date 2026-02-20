import json
import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant

from .database import Database

_LOGGER = logging.getLogger(__name__)


class ProfileManager:
    """Manages profiles, their entities, schedules, and lifecycle."""

    def __init__(self, hass: HomeAssistant, db: Database) -> None:
        self._hass = hass
        self._db = db

    async def async_create_profile(
        self,
        name: str,
        description: str | None,
        tags: list[str] | None,
        auto_add_entities: bool,
        export_formats: list[str],
        schedule_json: dict[str, Any] | None,
        date_active_from: str | None,
        date_active_until: str | None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        tags_str = ",".join(tags or [])
        schedule_str = json.dumps(schedule_json) if schedule_json else None
        formats_str = ",".join(export_formats)

        await self._db.async_execute(
            """
            INSERT INTO profiles (
                name, description, tags, active, archived,
                auto_add_entities, export_formats, schedule_json,
                date_active_from, date_active_until,
                created_at, updated_at
            )
            VALUES (?, ?, ?, 1, 0, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                tags_str,
                int(auto_add_entities),
                formats_str,
                schedule_str,
                date_active_from,
                date_active_until,
                now,
                now,
            ),
        )
        row = await self._db.async_fetchone(
            "SELECT last_insert_rowid();"
        )
        profile_id = int(row[0])
        _LOGGER.info("Created profile %s (%s)", profile_id, name)
        return profile_id

    async def async_update_profile(
        self,
        profile_id: int,
        **kwargs: Any,
    ) -> None:
        fields = []
        params: list[Any] = []
        for key, value in kwargs.items():
            if key == "tags" and isinstance(value, list):
                value = ",".join(value)
            if key == "export_formats" and isinstance(value, list):
                value = ",".join(value)
            if key == "schedule_json" and isinstance(value, dict):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            params.append(value)

        if not fields:
            return

        params.append(datetime.utcnow().isoformat())
        params.append(profile_id)

        await self._db.async_execute(
            f"""
            UPDATE profiles
            SET {", ".join(fields)}, updated_at = ?
            WHERE id = ?
            """,
            tuple(params),
        )

    async def async_set_profile_active(self, profile_id: int, active: bool) -> None:
        await self.async_update_profile(profile_id, active=int(active))

    async def async_archive_profile(self, profile_id: int, archived: bool = True) -> None:
        await self.async_update_profile(profile_id, archived=int(archived))

    async def async_get_profiles(self, include_archived: bool = False) -> list[dict[str, Any]]:
        query = "SELECT id, name, description, tags, active, archived, auto_add_entities, export_formats, schedule_json, date_active_from, date_active_until, created_at, updated_at FROM profiles"
        if not include_archived:
            query += " WHERE archived = 0"
        rows = await self._db.async_fetchall(query)

        profiles: list[dict[str, Any]] = []
        for row in rows:
            (
                pid,
                name,
                description,
                tags,
                active,
                archived,
                auto_add_entities,
                export_formats,
                schedule_json,
                date_active_from,
                date_active_until,
                created_at,
                updated_at,
            ) = row
            profiles.append(
                {
                    "id": pid,
                    "name": name,
                    "description": description,
                    "tags": tags.split(",") if tags else [],
                    "active": bool(active),
                    "archived": bool(archived),
                    "auto_add_entities": bool(auto_add_entities),
                    "export_formats": export_formats.split(",") if export_formats else [],
                    "schedule": json.loads(schedule_json) if schedule_json else None,
                    "date_active_from": date_active_from,
                    "date_active_until": date_active_until,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
            )
        return profiles

    async def async_set_profile_entities(
        self,
        profile_id: int,
        entity_ids: list[str],
        approved: bool,
        auto_added: bool,
    ) -> None:
        for entity_id in entity_ids:
            await self._db.async_execute(
                """
                INSERT INTO profile_entities (profile_id, entity_id, approved, auto_added)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(profile_id, entity_id)
                DO UPDATE SET approved = excluded.approved, auto_added = excluded.auto_added
                """,
                (profile_id, entity_id, int(approved), int(auto_added)),
            )

    async def async_get_profile_entities(
        self, profile_id: int, include_unapproved: bool
    ) -> list[str]:
        if include_unapproved:
            rows = await self._db.async_fetchall(
                """
                SELECT entity_id FROM profile_entities
                WHERE profile_id = ?
                """,
                (profile_id,),
            )
        else:
            rows = await self._db.async_fetchall(
                """
                SELECT entity_id FROM profile_entities
                WHERE profile_id = ? AND approved = 1
                """,
                (profile_id,),
            )
        return [r[0] for r in rows]
