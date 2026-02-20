import csv
import json
import logging
import os
from datetime import datetime
from typing import Any

import pandas as pd

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get as async_get_device_registry
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import (
    DATA_ACCURACY_MEAN,
    DATA_ACCURACY_RAW,
    DATA_ACCURACY_WEIGHTED_MEAN,
    METADATA_FIELDS,
    SUPPORTED_EXPORT_FORMATS,
)
from .database import Database

_LOGGER = logging.getLogger(__name__)


class ExportEngine:
    """Handles downsampling and multi-format export."""

    def __init__(self, hass: HomeAssistant, db: Database, export_path: str) -> None:
        self._hass = hass
        self._db = db
        self._export_path = hass.config.path(export_path)
        os.makedirs(self._export_path, exist_ok=True)

    async def async_export(
        self,
        entities: list[str],
        start_ts: datetime,
        end_ts: datetime,
        resolution_seconds: int,
        formats: list[str],
        label: str,
    ) -> dict[str, Any]:
        """Export data for given entities and time range."""
        formats = [f for f in formats if f in SUPPORTED_EXPORT_FORMATS]
        if not formats:
            raise ValueError("No valid export formats selected")

        dev_reg = async_get_device_registry(self._hass)
        ent_reg = async_get_entity_registry(self._hass)

        start_iso = start_ts.isoformat()
        end_iso = end_ts.isoformat()

        results: dict[str, Any] = {}

        for entity_id in entities:
            # Fetch raw samples
            rows = await self._db.async_fetchall(
                """
                SELECT ts, value FROM state_samples
                WHERE entity_id = ? AND ts >= ? AND ts <= ?
                ORDER BY ts
                """,
                (entity_id, start_iso, end_iso),
            )
            if not rows:
                continue

            samples = [(datetime.fromisoformat(ts), float(value)) for ts, value in rows]

            # Build target timestamps
            current = start_ts
            target_points: list[datetime] = []
            while current <= end_ts:
                target_points.append(current)
                current = current + pd.Timedelta(seconds=resolution_seconds)

            # Downsample
            downsampled = self._downsample(samples, target_points)

            # Build DataFrame
            df = pd.DataFrame(
                [
                    {
                        "timestamp": ts.isoformat(),
                        "value": value,
                        "data_accuracy": accuracy,
                    }
                    for ts, value, accuracy in downsampled
                ]
            )

            # Metadata block
            meta = await self._build_metadata_block(entity_id, dev_reg, ent_reg)

            # Write formats
            base_name = f"{label}_{entity_id.replace('.', '_')}_{start_ts.date()}_{end_ts.date()}"
            entity_result: dict[str, str] = {}

            for fmt in formats:
                path = await self._write_format(fmt, base_name, df, meta)
                entity_result[fmt] = path

            results[entity_id] = entity_result

        return results

    def _downsample(
        self,
        samples: list[tuple[datetime, float]],
        targets: list[datetime],
    ) -> list[tuple[datetime, float, str]]:
        """Downsample using raw/mean/weighted_mean."""
        if not samples:
            return []

        result: list[tuple[datetime, float, str]] = []
        idx = 0
        n = len(samples)

        for target in targets:
            # Move idx so that samples[idx] is the last sample <= target
            while idx + 1 < n and samples[idx + 1][0] <= target:
                idx += 1

            if samples[idx][0] == target:
                # Exact match
                result.append((target, samples[idx][1], DATA_ACCURACY_RAW))
                continue

            if idx + 1 >= n:
                # No next sample, hold last value as raw
                result.append((target, samples[idx][1], DATA_ACCURACY_RAW))
                continue

            t1, v1 = samples[idx]
            t2, v2 = samples[idx + 1]

            total = (t2 - t1).total_seconds()
            if total <= 0:
                result.append((target, v1, DATA_ACCURACY_RAW))
                continue

            offset = (target - t1).total_seconds()
            ratio = offset / total

            if abs(ratio - 0.5) < 1e-9:
                # Exact midpoint -> mean
                value = (v1 + v2) / 2.0
                accuracy = DATA_ACCURACY_MEAN
            else:
                # Weighted mean
                value = v1 + (v2 - v1) * ratio
                accuracy = DATA_ACCURACY_WEIGHTED_MEAN

            result.append((target, value, accuracy))

        return result

    async def _build_metadata_block(self, entity_id, dev_reg, ent_reg) -> list[str]:
        """Build metadata lines based on selected fields."""
        # Get selection
        rows = await self._db.async_fetchall(
            """
            SELECT field_name, selected
            FROM entity_metadata_selection
            WHERE entity_id = ?
            """,
            (entity_id,),
        )
        selected = {field: bool(sel) for field, sel in rows if bool(sel)}

        if not selected:
            return []

        entity = ent_reg.entities.get(entity_id)
        device = dev_reg.devices.get(entity.device_id) if entity and entity.device_id else None

        lines: list[str] = []
        lines.append(f"# Entity: {entity_id}")

        for field in METADATA_FIELDS:
            if field not in selected:
                continue
            value = None
            if field == "manufacturer":
                value = device.manufacturer if device else None
            elif field == "model":
                value = device.model if device else None
            elif field == "sw_version":
                value = device.sw_version if device else None
            elif field == "hw_version":
                value = device.hw_version if device else None
            elif field == "device_class":
                value = getattr(entity, "device_class", None) if entity else None
            elif field == "entity_category":
                value = getattr(entity, "entity_category", None) if entity else None
            elif field == "integration_domain":
                value = entity.platform if entity else None
            elif field == "area_name":
                # Could resolve via area registry if desired
                value = None
            elif field == "device_name":
                value = device.name if device else None
            elif field == "entity_name":
                value = entity.original_name if entity else None

            if value is not None:
                lines.append(f"# {field}: {value}")

        return lines

    async def _write_format(
        self,
        fmt: str,
        base_name: str,
        df: pd.DataFrame,
        metadata_lines: list[str],
    ) -> str:
        os.makedirs(self._export_path, exist_ok=True)

        if fmt == "csv":
            path = os.path.join(self._export_path, f"{base_name}.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for line in metadata_lines:
                    writer.writerow([line])
                df.to_csv(f, index=False)
            return path

        if fmt == "json":
            path = os.path.join(self._export_path, f"{base_name}.json")
            with open(path, "w", encoding="utf-8") as f:
                if metadata_lines:
                    f.write("// " + "\n// ".join(metadata_lines) + "\n")
                json.dump(df.to_dict(orient="records"), f, indent=2)
            return path

        if fmt == "html":
            path = os.path.join(self._export_path, f"{base_name}.html")
            with open(path, "w", encoding="utf-8") as f:
                if metadata_lines:
                    f.write("<!--\n" + "\n".join(metadata_lines) + "\n-->\n")
                f.write(df.to_html(index=False))
            return path

        if fmt == "xlsx":
            path = os.path.join(self._export_path, f"{base_name}.xlsx")
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="data")
            return path

        if fmt == "sqlite":
            path = os.path.join(self._export_path, f"{base_name}.sqlite")
            conn = f"sqlite:///{path}"
            df.to_sql("export", conn, if_exists="replace", index=False)
            return path

        if fmt == "parquet":
            path = os.path.join(self._export_path, f"{base_name}.parquet")
            df.to_parquet(path, index=False)
            return path

        if fmt == "feather":
            path = os.path.join(self._export_path, f"{base_name}.feather")
            df.to_feather(path)
            return path

        if fmt == "arrow":
            path = os.path.join(self._export_path, f"{base_name}.arrow")
            table = pa.Table.from_pandas(df)
            with pa.OSFile(path, "wb") as sink:
                with pa.ipc.new_file(sink, table.schema) as writer:
                    writer.write_table(table)
            return path

        raise ValueError(f"Unsupported format: {fmt}")
