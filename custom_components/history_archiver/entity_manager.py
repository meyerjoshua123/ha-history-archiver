import logging
from datetime import datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import METADATA_FIELDS
from .database import Database

_LOGGER = logging.getLogger(__name__)


class EntityManager:
    """Tracks entities, their metadata, and metadata selection."""

    def __init__(self, hass: HomeAssistant, db: Database) -> None:
        self._hass = hass
        self._db = db

    async def async_sync_entities(self) -> None:
        """Sync entities from HA registries into our DB."""
        dev_reg = async_get_device_registry(self._hass)
        ent_reg = async_get_entity_registry(self._hass)

        now = datetime.utcnow().isoformat()

        for entity in ent_reg.entities.values():
            entity_id = entity.entity_id
            device_id = entity.device_id
            area_id = entity.area_id

            row = await self._db.async_fetchone(
                "SELECT id FROM entities WHERE entity_id = ?",
                (entity_id,),
            )
            if row is None:
                await self._db.async_execute(
                    """
                    INSERT INTO entities (entity_id, device_id, area_id, stats_mode, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (entity_id, device_id, area_id, "raw", now, now),
                )
            else:
                await self._db.async_execute(
                    """
                    UPDATE entities
                    SET device_id = ?, area_id = ?, updated_at = ?
                    WHERE entity_id = ?
                    """,
                    (device_id, area_id, now, entity_id),
                )

            # Ensure metadata selection rows exist
            for field in METADATA_FIELDS:
                await self._db.async_execute(
                    """
                    INSERT OR IGNORE INTO entity_metadata_selection (entity_id, field_name, selected)
                    VALUES (?, ?, 0)
                    """,
                    (entity_id, field),
                )

    async def async_get_entity_tree(self) -> dict[str, Any]:
        """Return entities grouped by device for UI."""
        dev_reg = async_get_device_registry(self._hass)
        ent_reg = async_get_entity_registry(self._hass)

        rows = await self._db.async_fetchall(
            """
            SELECT e.entity_id, e.device_id, e.area_id,
                   ms.field_name, ms.selected
            FROM entities e
            LEFT JOIN entity_metadata_selection ms
                ON e.entity_id = ms.entity_id
            ORDER BY e.entity_id, ms.field_name
            """
        )

        tree: dict[str, Any] = {}

        # Build metadata selection map
        meta_map: dict[str, dict[str, bool]] = {}
        for entity_id, device_id, area_id, field_name, selected in rows:
            meta_map.setdefault(entity_id, {})[field_name] = bool(selected)

        for entity in ent_reg.entities.values():
            entity_id = entity.entity_id
            device_id = entity.device_id
            dev = dev_reg.devices.get(device_id) if device_id else None

            device_key = device_id or f"no_device::{entity_id}"

            if device_key not in tree:
                tree[device_key] = {
                    "device_id": device_id,
                    "device_name": dev.name if dev else "Unassigned device",
                    "manufacturer": dev.manufacturer if dev else None,
                    "model": dev.model if dev else None,
                    "entities": [],
                }

            tree[device_key]["entities"].append(
                {
                    "entity_id": entity_id,
                    "friendly_name": entity.original_name or entity_id,
                    "domain": entity.domain,
                    "selected_metadata": meta_map.get(entity_id, {}),
                }
            )

        return tree

    async def async_set_metadata_selection(
        self, entity_id: str, field_name: str, selected: bool
    ) -> None:
        await self._db.async_execute(
            """
            INSERT INTO entity_metadata_selection (entity_id, field_name, selected)
            VALUES (?, ?, ?)
            ON CONFLICT(entity_id, field_name)
            DO UPDATE SET selected = excluded.selected
            """,
            (entity_id, field_name, int(selected)),
        )

    async def async_record_sample(self, entity_id: str, value: float) -> None:
        now = datetime.utcnow().isoformat()
        await self._db.async_execute(
            """
            INSERT INTO state_samples (entity_id, ts, value, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (entity_id, now, value, now),
        )
