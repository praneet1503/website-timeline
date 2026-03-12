import csv
import logging
from pathlib import Path

cache_dir = Path("/cache")
timeline_file = cache_dir / "timeline_cache.csv"
snapshot_file = cache_dir / "snapshot_cache.csv"

def ensure_cache_files():
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.warning("Could not create cache directory %s: %s", cache_dir, e)
        return

    if not timeline_file.exists():
        try:
            with open(timeline_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["domain", "years"])
        except OSError as e:
            logging.warning("Could not create timeline cache file: %s", e)

    if not snapshot_file.exists():
        try:
            with open(snapshot_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["domain", "year", "timestamp"])
        except OSError as e:
            logging.warning("Could not create snapshot cache file: %s", e)

def get_timeline_cache(domain: str):
    if not timeline_file.exists():
        return None
    try:
        with open(timeline_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("domain") == domain:
                    years_str = row.get("years", "")
                    if years_str:
                        return years_str.split("|")
                    return []
    except Exception as e:
        logging.warning("Failed to read timeline cache for %s: %s", domain, e)
    return None


def save_timeline_cache(domain: str, years):
    if not timeline_file.exists():
        return

    years_string = "|".join(years)

    try:
        rows = []
        with open(timeline_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("domain") != domain:
                    rows.append(row)
        rows.append({"domain": domain, "years": years_string})

        with open(timeline_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["domain", "years"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        logging.warning("Failed to save timeline cache for %s: %s", domain, e)

def get_snapshot_cache(domain: str, year: str):
    if not snapshot_file.exists():
        return None
    snapshots = []
    try:
        with open(snapshot_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("domain") == domain and row.get("year") == year:
                    timestamp = row.get("timestamp", "")
                    if len(timestamp) >= 8:
                        snapshots.append({
                            "timestamp": timestamp,
                            "date": f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}",
                            "url": f"https://web.archive.org/web/{timestamp}/{domain}",
                        })
    except Exception as e:
        logging.warning("Failed to read snapshot cache for %s/%s: %s", domain, year, e)
        return None
    if snapshots:
        return snapshots
    return None


def save_snapshot_cache(domain: str, year: str, snapshots):
    if not snapshot_file.exists():
        return

    try:
        rows = []
        with open(snapshot_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not (row.get("domain") == domain and row.get("year") == year):
                    rows.append(row)

        for snap in snapshots:
            rows.append({
                "domain": domain,
                "year": year,
                "timestamp": snap.get("timestamp", ""),
            })

        with open(snapshot_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["domain", "year", "timestamp"])
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
    except Exception as e:
        logging.warning("Failed to save snapshot cache for %s/%s: %s", domain, year, e)