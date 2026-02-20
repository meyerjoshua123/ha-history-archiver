import asyncio
import logging
import os
from datetime import datetime

import aiosqlite
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DB_FILENAME, DB_SCHEMA_VERSION, DATA_DB

_LOGGER = logging.getLogger(__name__)


class Database:
    """SQLite database wrapper for History Archiver."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._db_path = hass.config.path(DOMAIN, DB_FILENAME)
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def path(self) -> str:
        return self._db_path

    async def async_initialize(self) -> None:
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")
        await self._ensure_schema()
        _LOGGER.info("History Archiver DB initialized at %s", self._db_path)

    async def _ensure_schema(self) -> None:
        async with self._conn.execute(
            "PRAGMA user_version;"
        ) as cursor:
            row = await cursor.fetchone()
            version = row[0] if row else 0

        if version == 0:
            await self._create_schema()
        elif version != DB_SCHEMA_VERSION:
            _LOGGER.warning(
                "DB schema version mismatch: %s != %s",
                version,
                DB_SCHEMA_VERSION,
            )
            # Here you could implement migrations later.

    async def _create_schema(self) -> None:
        _LOGGER.info("Creating History Archiver DB schema")

        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL
            );

            INSERT OR REPLACE INTO schema_version (id, version)
            VALUES (1, :version);

            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL UNIQUE,
                device_id TEXT,
                area_id TEXT,
                stats_mode TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entity_metadata_selection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                selected INTEGER NOT NULL DEFAULT 0,
                UNIQUE(entity_id, field_name)
            );

            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                tags TEXT,
                active INTEGER NOT NULL DEFAULT 1,
                archived INTEGER NOT NULL DEFAULT 0,
                auto_add_entities INTEGER NOT NULL DEFAULT 0,
                export_formats TEXT NOT NULL,
                schedule_json TEXT,
                date_active_from TEXT,
                date_active_until TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profile_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER NOT NULL,
                entity_id TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                auto_added INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS state_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                value REAL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_state_samples_entity_ts
                ON state_samples(entity_id, ts);

            CREATE TABLE IF NOT EXISTS export_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_id INTEGER,
                export_type TEXT NOT NULL,
                start_ts TEXT NOT NULL,
                end_ts TEXT NOT NULL,
                resolution_seconds INTEGER NOT NULL,
                formats TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS db_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                created_at TEXT NOT NULL,
                size_bytes INTEGER NOT NULL
            );
            """
        )
        await self._conn.execute(
            "PRAGMA user_version = ?;", (DB_SCHEMA_VERSION,)
        )
        await self._conn.commit()

    async def async_execute(self, query: str, params: tuple | dict | None = None):
        async with self._lock:
            await self._conn.execute(query, params or ())
            await self._conn.commit()

    async def async_fetchall(self, query: str, params: tuple | dict | None = None):
        async with self._lock:
            async with self._conn.execute(query, params or ()) as cursor:
                rows = await cursor.fetchall()
        return rows

    async def async_fetchone(self, query: str, params: tuple | dict | None = None):
        async with self._lock:
            async with self._conn.execute(query, params or ()) as cursor:
                row = await cursor.fetchone()
        return row

    async def async_backup(self, backup_path: str) -> None:
        """Create a backup copy of the DB."""
        _LOGGER.info("Creating DB backup at %s", backup_path)
        async with self._lock:
            # Use backup API by opening a new connection
            async with aiosqlite.connect(backup_path) as backup_conn:
                await self._conn.backup(backup_conn)
        stat = os.stat(backup_path)
        await self.async_execute(
            """
            INSERT INTO db_backups (filename, created_at, size_bytes)
            VALUES (?, ?, ?)
            """,
            (
                os.path.basename(backup_path),
                datetime.utcnow().isoformat(),
                stat.st_size,
            ),
        )

    async def async_close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None
