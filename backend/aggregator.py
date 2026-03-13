import logging
from typing import List
from datetime import datetime

from cache import (
    get_timeline_from_memory,
    get_timeline_from_disk,
    save_timeline,
    get_snapshots_from_memory,
    get_snapshots_from_disk,
    save_snapshots,
)
from wayback import fetch_timeline, fetch_snapshots, clean_domain


def _is_stale_timeline(years: List[str]) -> bool:
    if not years:
        return True
    if len(years) > 1:
        return False

    year = years[0]
    if not year.isdigit() or len(year) != 4:
        return False
    current_year = datetime.utcnow().year
    return int(year) < current_year


async def get_timeline(domain: str) -> dict:
    domain = clean_domain(domain)

    # Layer 1 — memory
    years = get_timeline_from_memory(domain)
    if years and not _is_stale_timeline(years):
        logging.info("Memory cache hit (timeline) for %s", domain)
        return {"domain": domain, "years": years, "cached": True}

    # Layer 2 — disk
    years = get_timeline_from_disk(domain)
    if years and not _is_stale_timeline(years):
        logging.info("Disk cache hit (timeline) for %s", domain)
        save_timeline(domain, years)  # promote to memory
        return {"domain": domain, "years": years, "cached": True}

    # Layer 3 — Wayback API
    try:
        years = await fetch_timeline(domain)
    except Exception as exc:
        logging.error("Wayback timeline fetch failed for %s: %s", domain, exc)
        return {"domain": domain, "years": [], "cached": False}

    if years is None:
        years = []

    if years:
        save_timeline(domain, years)
    return {"domain": domain, "years": years, "cached": False}


async def get_snapshots(domain: str, year: str) -> dict:
    domain = clean_domain(domain)

    # Layer 1 — memory
    snaps = get_snapshots_from_memory(domain, year)
    if snaps:
        logging.info("Memory cache hit (snapshots) for %s/%s", domain, year)
        return {"domain": domain, "year": year, "snapshots": snaps, "cached": True}

    # Layer 2 — disk
    snaps = get_snapshots_from_disk(domain, year)
    if snaps:
        logging.info("Disk cache hit (snapshots) for %s/%s", domain, year)
        save_snapshots(domain, year, snaps)  # promote to memory
        return {"domain": domain, "year": year, "snapshots": snaps, "cached": True}

    # Layer 3 — Wayback API
    try:
        snaps = await fetch_snapshots(domain, year)
    except Exception as exc:
        logging.error("Wayback snapshot fetch failed for %s/%s: %s", domain, year, exc)
        return {"domain": domain, "year": year, "snapshots": [], "cached": False}

    if snaps is None:
        snaps = []

    if snaps:
        save_snapshots(domain, year, snaps)
    return {"domain": domain, "year": year, "snapshots": snaps, "cached": False}
