import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache
from fastapi.responses import JSONResponse
from wayback import fetch_timeline, fetch_snapshots, fetch_activity, fetch_closest, clean_domain
from cache import (
    ensure_cache_files,
    get_timeline_cache,
    get_snapshot_cache,
    save_snapshot_cache,
    save_timeline_cache,
)
from models import (
    TimelineResponse,
    SnapshotResponse,
    HealthResponse,
    ActivityResponse,
    ClosestResponse,
)

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Website Timeline API",
    description="Explore historical versions of any website via the Wayback Machine.",
    version="2.0.0",
)

try:
    ensure_cache_files()
except Exception as e:
    logging.warning("Cache initialization failed (non-fatal): %s", e)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
cache = TTLCache(maxsize=300, ttl=3600)
snapshot_cache = TTLCache(maxsize=1000, ttl=3600)
activity_cache = TTLCache(maxsize=300, ttl=3600)
@app.get("/timeline", response_model=TimelineResponse)
async def get_timeline(domain: str):
    logging.info("GET /timeline?domain=%s", domain)

    cleaned = clean_domain(domain)

    if cleaned in cache:
        logging.info("Memory cache hit for %s", cleaned)
        return {"domain": cleaned, "years": cache[cleaned], "cached": True}

    csv_cache = get_timeline_cache(cleaned)
    if csv_cache:
        logging.info("Disk cache hit for %s", cleaned)
        cache[cleaned] = csv_cache
        return {"domain": cleaned, "years": csv_cache, "cached": True}

    fetch_failed = False
    try:
        years = await fetch_timeline(cleaned)
    except Exception as e:
        logging.error("fetch_timeline failed for %s: %s", cleaned, e)
        years = []
        fetch_failed = True

    if years is None:
        years = []

    if not fetch_failed:
        save_timeline_cache(cleaned, years)
        cache[cleaned] = years
    else:
        logging.warning("Skipping timeline cache write for %s due to upstream failure", cleaned)

    logging.info("Returning %d years for %s", len(years), cleaned)
    return {"domain": cleaned, "years": years, "cached": False}

@app.get("/snapshots", response_model=SnapshotResponse)
async def get_snapshots(domain: str, year: str):
    logging.info("GET /snapshots?domain=%s&year=%s", domain, year)

    cleaned = clean_domain(domain)
    cache_key = f"{cleaned}_{year}"

    if cache_key in snapshot_cache:
        logging.info("Memory cache hit for %s", cache_key)
        return {"snapshots": snapshot_cache[cache_key], "cached": True}

    csv_snapshots = get_snapshot_cache(cleaned, year)
    if csv_snapshots:
        logging.info("Disk cache hit for %s", cache_key)
        snapshot_cache[cache_key] = csv_snapshots
        return {"snapshots": csv_snapshots, "cached": True}

    fetch_failed = False
    try:
        snapshots = await fetch_snapshots(cleaned, year)
    except Exception as e:
        logging.error("fetch_snapshots failed for %s/%s: %s", cleaned, year, e)
        snapshots = []
        fetch_failed = True

    if snapshots is None:
        snapshots = []

    if not fetch_failed:
        save_snapshot_cache(cleaned, year, snapshots)
        snapshot_cache[cache_key] = snapshots
    else:
        logging.warning("Skipping snapshot cache write for %s due to upstream failure", cache_key)

    return {"snapshots": snapshots, "cached": False}

@app.get("/activity", response_model=ActivityResponse)
async def get_activity(domain: str):
    logging.info("GET /activity?domain=%s", domain)

    cleaned = clean_domain(domain)

    if cleaned in activity_cache:
        logging.info("Memory cache hit for activity/%s", cleaned)
        return {"domain": cleaned, "activity": activity_cache[cleaned], "cached": True}

    fetch_failed = False
    try:
        activity = await fetch_activity(cleaned)
    except Exception as e:
        logging.error("fetch_activity failed for %s: %s", cleaned, e)
        activity = {}
        fetch_failed = True

    if activity is None:
        activity = {}

    if not fetch_failed:
        activity_cache[cleaned] = activity
    else:
        logging.warning("Skipping activity cache write for %s due to upstream failure", cleaned)

    return {"domain": cleaned, "activity": activity, "cached": False}

@app.get("/closest", response_model=ClosestResponse)
async def get_closest(domain: str, date: str):
    logging.info("GET /closest?domain=%s&date=%s", domain, date)

    cleaned = clean_domain(domain)

    if not date.isdigit() or len(date) != 8:
        logging.warning("Invalid date format: %s", date)
        return {
            "domain": cleaned,
            "found": False,
            "timestamp": None,
            "date": None,
            "url": None,
        }

    try:
        result = await fetch_closest(cleaned, date)
    except Exception as e:
        logging.error("fetch_closest failed for %s@%s: %s", cleaned, date, e)
        result = None

    if result is None:
        return {
            "domain": cleaned,
            "found": False,
            "timestamp": None,
            "date": None,
            "url": None,
        }

    return {
        "domain": cleaned,
        "found": True,
        "timestamp": result["timestamp"],
        "date": result["date"],
        "url": result["url"],
    }

@app.get("/health", response_model=HealthResponse)
def health_check():
    return JSONResponse(content={"status": "online"}, status_code=200)
    return {"snapshots": snapshots}

