import modal
from pathlib import Path
import csv
import shutil

volume = modal.Volume.from_name("webtime-cache-volume", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi","httpx","cachetools","pydantic",)
    .add_local_python_source("server", "wayback", "cache", "models", "aggregator", "prewarm", "utils")
    .add_local_dir("cache", remote_path="/seed_cache")
)
app=modal.App("webtime-backend")
@app.function(
    image=image,
    volumes={"/cache": volume},
)
@modal.asgi_app()
def fastapi_app():
    import cache as cache_module
    def _timeline_looks_valid(path: Path) -> bool:
        if not path.exists() or path.stat().st_size == 0:
            return False
        try:
            with open(path, "r") as f:
                for row in csv.DictReader(f):
                    if row.get("domain", "").strip().lower() == "youtube.com":
                        years = (row.get("years", "") or "").strip()
                        return bool(years and "|" in years)
        except Exception:
            return False
        return False
    def _snapshot_looks_valid(path: Path) -> bool:
        if not path.exists() or path.stat().st_size == 0:
            return False
        try:
            with open(path, "r") as f:
                for row in csv.DictReader(f):
                    if row.get("domain", "").strip().lower() == "youtube.com":
                        if (row.get("year", "") or "").strip() and (row.get("timestamp", "") or "").strip():
                            return True
        except Exception:
            return False
        return False
    seed_timeline = Path("/seed_cache/timeline_cache.csv")
    seed_snapshot = Path("/seed_cache/snapshot_cache.csv")
    live_timeline = Path("/cache/timeline_cache.csv")
    live_snapshot = Path("/cache/snapshot_cache.csv")
    try:
        if seed_timeline.exists() and not _timeline_looks_valid(live_timeline):
            shutil.copy(seed_timeline, live_timeline)
        if seed_snapshot.exists() and not _snapshot_looks_valid(live_snapshot):
            shutil.copy(seed_snapshot, live_snapshot)
        volume.commit()
    except Exception:
        pass

    cache_module.CACHE_DIR = Path("/cache")
    cache_module.TIMELINE_FILE = cache_module.CACHE_DIR / "timeline_cache.csv"
    cache_module.SNAPSHOT_FILE = cache_module.CACHE_DIR / "snapshot_cache.csv"
    import server
    return server.app

