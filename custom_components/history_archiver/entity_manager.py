from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from homeassistant.core import HomeAssistant, State

from .database import execute, fetchall


@dataclass
class EntityRecord:
    """Represents a single Home Assistant entity stored in the DB."""
    id: int
    entity_id: str
    domain: str
    area: Optional[str]
    device: Optional[str]
    friendly_name: Optional[str]
    auto_added: bool
    last_metadata_update: Optional[str]


class EntityManager:
    """Handles entity storage, metadata tracking, and profile linking."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    # -----------------------------
    # LOAD ENTITIES
    # -----------------------------
    def load_entities(self) -> List[EntityRecord]:
        rows = fetchall(self.hass, """
            SELECT id, entity_id, domain, area, device, friendly_name,
                   auto_added, last_metadata_update
            FROM entities
        """)

        entities = []
        for row in rows:
            entities.append(EntityRecord(
                id=row[0],
                entity_id=row[1],
                domain=row[2],
                area=row[3],
                device=row[4],
                friendly_name=row[5],
                auto_added=bool(row[6]),
                last_metadata_update=row[7],
            ))

        return entities

    # -----------------------------
    # ADD ENTITY
    # -----------------------------
    def add_entity(
        self,
        entity_id: str,
        domain: str,
        area: Optional[str],
        device: Optional[str],
        friendly_name: Optional[str],
        auto_added: bool = False,
    ):
        execute(self.hass, """
            INSERT OR IGNORE INTO entities (
                entity_id, domain, area, device, friendly_name,
                auto_added, last_metadata_update
            )
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            entity_id,
            domain,
            area,
            device,
            friendly_name,
            int(auto_added),
        ))

    # -----------------------------
    # UPDATE METADATA + LOG CHANGES
    # -----------------------------
    def update_metadata(
        self,
        entity_id: str,
        new_area: Optional[str],
        new_device: Optional[str],
        new_name: Optional[str],
    ):
        # Get current metadata
        rows = fetchall(self.hass, """
            SELECT id, area, device, friendly_name
            FROM entities
            WHERE entity_id = ?
        """, (entity_id,))

        if not rows:
            return  # entity not in DB yet

        entity_db_id, old_area, old_device, old_name = rows[0]

        # Detect changes
        if old_area != new_area or old_device != new_device or old_name != new_name:
            # Log metadata change
            execute(self.hass, """
                INSERT INTO metadata_changes (
                    entity_id, timestamp,
                    old_area, new_area,
                    old_device, new_device,
                    old_name, new_name
                )
                VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
            """, (
                entity_db_id,
                old_area, new_area,
                old_device, new_device,
                old_name, new_name,
            ))

            # Update entity record
            execute(self.hass, """
                UPDATE entities
                SET area = ?, device = ?, friendly_name = ?, last_metadata_update = datetime('now')
                WHERE id = ?
            """, (
                new_area,
                new_device,
                new_name,
                entity_db_id,
            ))

    # -----------------------------
    # LINK ENTITY TO PROFILE
    # -----------------------------
    def link_entity_to_profile(
        self,
        profile_id: int,
        entity_db_id: int,
        include: bool = True,
    ):
        execute(self.hass, """
            INSERT OR IGNORE INTO profile_entities (
                profile_id, entity_id, include
            )
            VALUES (?, ?, ?)
        """, (
            profile_id,
            entity_db_id,
            int(include),
        ))

    # -----------------------------
    # UPDATE PER-ENTITY STATS CONFIG
    # -----------------------------
    def update_entity_stats(
        self,
        profile_id: int,
        entity_db_id: int,
        **kwargs,
    ):
        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(profile_id)
        values.append(entity_db_id)

        execute(self.hass, f"""
            UPDATE profile_entities
            SET {', '.join(fields)}
            WHERE profile_id = ? AND entity_id = ?
        """, tuple(values))
