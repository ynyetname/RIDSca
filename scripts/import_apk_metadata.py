"""Stream an authorized metadata CSV (including AndroZoo format) into local SQLite."""

import argparse
import csv
from pathlib import Path
import re
import sqlite3


def build_index(source, destination):
    Path(destination).parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with sqlite3.connect(destination) as db, open(source, newline="", encoding="utf-8-sig") as f:
        db.execute(
            "CREATE TABLE IF NOT EXISTS apk_metadata (sha256 TEXT PRIMARY KEY, package_name TEXT, vt_detection INTEGER, observed_at TEXT)"
        )
        for row in csv.DictReader(f):
            sha = row.get("sha256", "").lower()
            if not re.fullmatch(r"[a-f0-9]{64}", sha):
                continue
            detections = row.get("vt_detection", "")
            try:
                detections = int(detections) if detections else None
            except ValueError:
                continue
            db.execute(
                "INSERT OR REPLACE INTO apk_metadata VALUES (?, ?, ?, ?)",
                (
                    sha,
                    row.get("package_name", "unknown"),
                    detections,
                    row.get("observed_at", row.get("vt_scan_date", "unknown")),
                ),
            )
            count += 1
            if count % 10000 == 0:
                db.commit()
        db.commit()
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--output", default="local_data/apk_metadata.sqlite")
    args = parser.parse_args()
    print(f"Imported {build_index(args.csv_path, args.output)} rows into {args.output}")


if __name__ == "__main__":
    main()
