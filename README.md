# 📦 History Archiver for Home Assistant

Disclaimer: I am new to Github/python and relied heavily on Copilot to generate the code for this.

A powerful, local‑first data archiving engine for Home Assistant.  
History Archiver continuously records entity state samples, stores them in a dedicated SQLite database, and lets you export clean, downsampled datasets in multiple formats — perfect for analysis, dashboards, long‑term storage, or external tools.

This integration is designed to be:

- **Fast** — optimized SQLite schema, WAL mode, async I/O  
- **Local‑first** — no cloud, no external dependencies  
- **Flexible** — profiles, metadata selection, multiple export formats  
- **Reliable** — backup/restore support, schema versioning  
- **User‑friendly** — simple config flow, clear UI labels  

---

## 🚀 Features

### ✔ Continuous State Recording  
Samples selected entities at a configurable interval (default: 10 seconds).  
All samples are stored in:

