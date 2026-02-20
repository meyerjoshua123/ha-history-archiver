from __future__ import annotations

import os
import sqlite3
from homeassistant.core import HomeAssistant

DB_FILENAME = "history_archiver.db"


def get_db_path(hass: HomeAssistant) -> str:
    """Return the full path to the SQLite database file."""
    storage_path = hass.config.path(".storage")
    return os.path.join(storage_path, DB_FILENAME)


def initialize_database(hass: HomeAssistant):
    """Create the database and tables if they do not exist."""
    db_path = get_db_path(hass)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Profiles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            update_interval INTEGER NOT NULL,
            file_duration TEXT NOT NULL,
            retention_local INTEGER NOT NULL,
            auto_add INTEGER NOT NULL DEFAULT 0,
            linked_profiles TEXT,
            upload_backend TEXT,
            upload_path TEXT,
            created_at TEXT
        )
    """)

    # Entities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            id INTEGER PRIMARY KEY,
            entity_id TEXT UNIQUE NOT NULL,
            domain TEXT,
            area TEXT,
            device TEXT,
            friendly_name TEXT,
            auto_added INTEGER NOT NULL DEFAULT 0,
            last_metadata_update TEXT
        )
    """)

    # Profile-entity link table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_entities (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            include INTEGER NOT NULL DEFAULT 1,
            stats_first INTEGER DEFAULT 1,
            stats_last INTEGER DEFAULT 1,
            stats_mean INTEGER DEFAULT 1,
            stats_mode INTEGER DEFAULT 1,
            stats_min INTEGER DEFAULT 1,
            stats_max INTEGER DEFAULT 1,
            FOREIGN KEY(profile_id) REFERENCES profiles(id),
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        )
    """)

    # State samples
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS state_samples (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            value TEXT,
            FOREIGN KEY(profile_id) REFERENCES profiles(id),
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        )
    """)

    # Metadata changes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata_changes (
            id INTEGER PRIMARY KEY,
            entity_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            old_area TEXT,
            new_area TEXT,
            old_device TEXT,
            new_device TEXT,
            old_name TEXT,
            new_name TEXT,
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        )
    """)

    # Events log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events_log (
            id INTEGER PRIMARY KEY,
            timestamp TEXT NOT NULL,
            entity_id TEXT,
            event_type TEXT NOT NULL,
            source TEXT,
            context_id TEXT,
            details TEXT
        )
    """)

    # Upload history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(profile_id) REFERENCES profiles(id)
        )
    """)

    # Stats table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY,
            profile_id INTEGER NOT NULL,
            entity_id INTEGER NOT NULL,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            first_value TEXT,
            last_value TEXT,
            mean_value REAL,
            mode_value TEXT,
            min_value REAL,
            max_value REAL,
            FOREIGN KEY(profile_id) REFERENCES profiles(id),
            FOREIGN KEY(entity_id) REFERENCES entities(id)
        )
    """)

    conn.commit()
    conn.close()


def execute(hass: HomeAssistant, query: str, params: tuple = ()):
    """Execute a write query."""
    db_path = get_db_path(hass)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()


def fetchall(hass: HomeAssistant, query: str, params: tuple = ()):
    """Execute a read query and return all rows."""
    db_path = get_db_path(hass)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows
