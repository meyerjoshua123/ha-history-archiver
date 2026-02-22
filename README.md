# 📦 History Archiver for Home Assistant

A powerful, local‑first data archiving engine for Home Assistant.  
History Archiver continuously records entity state samples, stores them in a dedicated SQLite database, and lets you export clean, downsampled datasets in multiple formats — perfect for analysis, dashboards, long‑term storage, or external tools.

This integration is designed to be:

- **Fast** — optimized SQLite schema, WAL mode, async I/O  
- **Local‑first** — no cloud, no external dependencies  
- **Flexible** — profiles, metadata selection, multiple export formats  
- **Reliable** — backup/restore support, schema versioning  
- **User‑friendly** — simple config flow, clear UI labels  

---

## ⚠️ Disclaimer

**I am new to GitHub/Python and relied heavily on Copilot to generate the code for this.**  
This project is a learning exercise and may evolve rapidly. Use at your own discretion.

---

## 🚀 Features

### ✔ Continuous State Recording  
Samples selected entities at a configurable interval (default: 10 seconds).  
All samples are stored in: /config/history_archiver/history.db

### ✔ Entity Metadata Tracking  
Automatically syncs:

- Device name  
- Manufacturer  
- Model  
- Software version  
- Hardware version  
- Device class  
- Entity category  
- Integration domain  
- Entity name  

You choose which metadata fields to include in exports.

### ✔ Profiles  
Create multiple export profiles with:

- Custom entity lists  
- Export formats  
- Scheduling rules  
- Tags and descriptions  
- Auto‑add entity behavior  

### ✔ Downsampling Engine  
Exports can downsample using:

- **Raw**  
- **Mean**  
- **Weighted mean**

### ✔ Multi‑Format Export  
Supported formats:

- CSV  
- JSON  
- HTML  
- XLSX  
- SQLite  
- Parquet  
- Feather  
- Arrow  

Exports are written to: config/www/community/ha-history-archiver

(or your custom path)

### ✔ Backup & Restore  
Built‑in services allow you to:

- Create a backup of the database  
- Restore from a previous backup  

Backups are stored in: /config/history_archiver_backups

### ✔ HACS Compatible  
Includes:

- `hacs.json`  
- `hacs.png`  
- Proper repo structure  

---

## 🛠 Installation

### Option A — HACS (Recommended)

1. Open **HACS → Integrations**
2. Click **⋮ → Custom repositories**
3. Add: https://github.com/meyerjoshua123/ha-history-archiver
4. Category: **Integration**
5. Install **History Archiver**
6. Restart Home Assistant

---

### Option B — Manual Installation

1. Download the latest release from:  
   https://github.com/meyerjoshua123/ha-history-archiver/releases
2. Extract to: config/custom_components/history_archiver
3. Restart Home Assistant

---

## ⚙️ Configuration

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **History Archiver**

You will be prompted for:

### **Record Interval (s)**  
How often to record entity state samples.  
**Recommended: 10s**

### **Export Path**  
Where export files will be written.

Default: config/www/community/ha-history-archiver

You can change this anytime via the integration’s **Options**.

---

## 📤 Exporting Data

Exports can be triggered via:

### ✔ Profiles  
Scheduled or manual exports.

### ✔ Predefined Exports  
- Day  
- Week  
- Month  
- Year  

### ✔ Manual Export Service  
Export any set of entities for any time range.

---

## 🗄 Database Schema

The SQLite database includes:

- `entities`  
- `entity_metadata_selection`  
- `profiles`  
- `profile_entities`  
- `state_samples`  
- `export_runs`  
- `db_backups`  
- `schema_version`  

Schema versioning ensures safe upgrades.

---

## 🔄 Backup & Restore

### Backup  
Creates a timestamped copy of the database.

### Restore  
Replaces the active DB with a backup and reloads schema.

Useful for:

- Migrating to a new HA instance  
- Recovering from corruption  
- Testing changes safely  

---

## 🧩 Services

| Service | Description |
|--------|-------------|
| `history_archiver.backup_db` | Creates a DB backup |
| `history_archiver.restore_db` | Restores DB from a backup |
| `history_archiver.manual_export` | Manual export for any entities/time range |
| `history_archiver.predefined_export_*` | Day/Week/Month/Year exports |

---

## 🧑‍💻 Code Owners

@meyerjoshua123


---

## 📝 License

MIT License — see `LICENSE` file.

---

## ❤️ Contributing

Pull requests are welcome!  
If you have ideas, issues, or feature requests, open an issue here:

https://github.com/meyerjoshua123/ha-history-archiver/issues

