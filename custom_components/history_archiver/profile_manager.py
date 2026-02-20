from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from homeassistant.core import HomeAssistant

from .database import execute, fetchall


@dataclass
class Profile:
    """Represents a single archiver profile."""
    id: int
    name: str
    enabled: bool
    update_interval: int
    file_duration: str
    retention_local: int
    auto_add: bool
    linked_profiles: Optional[str]
    upload_backend: Optional[str]
    upload_path: Optional[str]
    created_at: Optional[str]


class ProfileManager:
    """Handles loading, creating, updating, and deleting profiles."""

    def __init__(self, hass: HomeAssistant):
        self.hass = hass

    # -----------------------------
    # LOAD PROFILES
    # -----------------------------
    def load_profiles(self) -> List[Profile]:
        rows = fetchall(self.hass, """
            SELECT id, name, enabled, update_interval, file_duration,
                   retention_local, auto_add, linked_profiles,
                   upload_backend, upload_path, created_at
            FROM profiles
        """)

        profiles = []
        for row in rows:
            profiles.append(Profile(
                id=row[0],
                name=row[1],
                enabled=bool(row[2]),
                update_interval=row[3],
                file_duration=row[4],
                retention_local=row[5],
                auto_add=bool(row[6]),
                linked_profiles=row[7],
                upload_backend=row[8],
                upload_path=row[9],
                created_at=row[10],
            ))

        return profiles

    # -----------------------------
    # CREATE PROFILE
    # -----------------------------
    def create_profile(
        self,
        name: str,
        update_interval: int,
        file_duration: str,
        retention_local: int,
        auto_add: bool = False,
        linked_profiles: Optional[str] = None,
        upload_backend: Optional[str] = None,
        upload_path: Optional[str] = None,
    ):
        execute(self.hass, """
            INSERT INTO profiles (
                name, enabled, update_interval, file_duration,
                retention_local, auto_add, linked_profiles,
                upload_backend, upload_path, created_at
            )
            VALUES (?, 1, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            name,
            update_interval,
            file_duration,
            retention_local,
            int(auto_add),
            linked_profiles,
            upload_backend,
            upload_path,
        ))

    # -----------------------------
    # UPDATE PROFILE
    # -----------------------------
    def update_profile(self, profile_id: int, **kwargs):
        """Update only the fields provided in kwargs."""
        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key} = ?")
            values.append(value)

        values.append(profile_id)

        query = f"UPDATE profiles SET {', '.join(fields)} WHERE id = ?"
        execute(self.hass, query, tuple(values))

    # -----------------------------
    # DELETE PROFILE
    # -----------------------------
    def delete_profile(self, profile_id: int):
        execute(self.hass, "DELETE FROM profiles WHERE id = ?", (profile_id,))
        execute(self.hass, "DELETE FROM profile_entities WHERE profile_id = ?", (profile_id,))
