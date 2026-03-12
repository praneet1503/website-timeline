import httpx
import logging
import asyncio
import time
import random

WAYBACK_CDX = "https://web.archive.org/cdx/search/cdx"

WAYBACK_AVAILABLE = "https://archive.org/wayback/available"
client = httpx.AsyncClient(timeout=30)

def clean_domain(domain: str) -> str:
    domain = domain.strip().lower()
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    domain = domain.rstrip("/")
    return domain

async def fetch_timeline(domain: str):
    domain = clean_domain(domain)
    query_domains = [f"*.{domain}", domain]

    years = set()
    had_successful_response = False
    last_error = None

    for query_domain in query_domains:
        params = {
            "url": query_domain,
            "output": "json",
            "fl": "timestamp",
            "filter": "statuscode:200",
            "collapse": "timestamp:4",
            "limit": 2000,
        }
        try:
            response = await rate_limited_request(client, WAYBACK_CDX, params=params)
            response.raise_for_status()
            data = response.json()
            had_successful_response = True
        except httpx.HTTPStatusError as e:
            logging.warning("Wayback timeline HTTP error for %s: %s", domain, e)
            last_error = e
            continue
        except httpx.RequestError as e:
            logging.warning("Wayback timeline network error for %s: %s", domain, e)
            last_error = e
            continue
        except Exception as e:
            logging.warning("Wayback timeline unexpected error for %s: %s", domain, e)
            last_error = e
            continue
        if not data or len(data) <= 1:
            continue
        for row in data[1:]:
            if not isinstance(row, list) or not row:
                continue
            timestamp = row[0]
            if not isinstance(timestamp, str) or not timestamp.isdigit():
                continue
            years.add(timestamp[:4])
        if years:
            break
    if not had_successful_response and last_error is not None:
        raise RuntimeError(f"Timeline fetch failed for {domain}") from last_error

    return sorted(years)

async def fetch_snapshots(domain: str, year: str):
    domain = clean_domain(domain)
    query_domains = [domain, f"www.{domain}"]

    snapshots = []
    had_successful_response = False
    last_error = None

    for query_domain in query_domains:
        params = {
            "url": query_domain,
            "from": year,
            "to": year,
            "output": "json",
            "fl": "timestamp",
            "filter": "statuscode:200",
            "collapse": "timestamp:8",
            "limit": 50,
        }
        try:
            response = await rate_limited_request(client, WAYBACK_CDX, params=params)
            response.raise_for_status()
            data = response.json()
            had_successful_response = True
        except httpx.HTTPStatusError as e:
            logging.warning("Wayback snapshots HTTP error for %s/%s: %s", domain, year, e)
            last_error = e
            continue
        except httpx.RequestError as e:
            logging.warning("Wayback snapshots network error for %s/%s: %s", domain, year, e)
            last_error = e
            continue
        except Exception as e:
            logging.warning("Wayback snapshots unexpected error for %s/%s: %s", domain, year, e)
            last_error = e
            continue
        if not data or len(data) <= 1:
            continue
        for row in data[1:]:
            if not isinstance(row, list) or not row:
                continue
            timestamp = row[0]
            if not isinstance(timestamp, str) or len(timestamp) < 8:
                logging.warning("Skipping malformed timestamp: %s", timestamp)
                continue
            formatted_date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"
            snapshots.append({
                "timestamp": timestamp,
                "date": formatted_date,
                "url": f"https://web.archive.org/web/{timestamp}/{domain}",
            })
        if snapshots:
            break
    if not had_successful_response and last_error is not None:
        raise RuntimeError(f"Snapshot fetch failed for {domain}/{year}") from last_error

    return snapshots

async def fetch_activity(domain: str):
    domain = clean_domain(domain)
    query_domains = [domain, f"www.{domain}"]
    year_counts = {}
    had_successful_response = False
    last_error = None

    for query_domain in query_domains:
        params = {
            "url": query_domain,
            "output": "json",
            "fl": "timestamp",
            "filter": "statuscode:200",
            "collapse": "timestamp:6",
            "limit": 5000,
        }
        try:
            response = await rate_limited_request(client, WAYBACK_CDX, params=params)
            response.raise_for_status()
            data = response.json()
            had_successful_response = True
        except httpx.HTTPStatusError as e:
            logging.warning("Wayback activity HTTP error for %s: %s", domain, e)
            last_error = e
            continue
        except httpx.RequestError as e:
            logging.warning("Wayback activity network error for %s: %s", domain, e)
            last_error = e
            continue
        except Exception as e:
            logging.warning("Wayback activity unexpected error for %s: %s", domain, e)
            last_error = e
            continue
        if not data or len(data) <= 1:
            continue
        for row in data[1:]:
            if not isinstance(row, list) or not row:
                continue
            timestamp = row[0]
            if not isinstance(timestamp, str) or len(timestamp) < 4:
                continue
            year = timestamp[:4]
            year_counts[year] = year_counts.get(year, 0) + 1
        if year_counts:
            break

    if not had_successful_response and last_error is not None:
        raise RuntimeError(f"Activity fetch failed for {domain}") from last_error

    return year_counts

async def fetch_closest(domain: str, date: str):
    domain = clean_domain(domain)

    params = {
        "url": domain,
        "timestamp": date,
    }

    try:
        response = await rate_limited_request(client, WAYBACK_AVAILABLE, params=params)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPStatusError as e:
        logging.warning("Wayback closest HTTP error for %s@%s: %s", domain, date, e)
        return None
    except httpx.RequestError as e:
        logging.warning("Wayback closest network error for %s@%s: %s", domain, date, e)
        return None
    except Exception as e:
        logging.warning("Wayback closest unexpected error for %s@%s: %s", domain, date, e)
        return None
    archived = data.get("archived_snapshots", {})
    closest = archived.get("closest")

    if not closest or not closest.get("available"):
        return None

    timestamp = closest.get("timestamp", "")
    url = closest.get("url", "")
    formatted_date = ""
    if len(timestamp) >= 8:
        formatted_date = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]}"

    return {
        "timestamp": timestamp,
        "date": formatted_date,
        "url": url,
        "domain": domain,
    }

_last_request_time = 0
REQUEST_DELAY = 0.5  
MAX_RETRIES = 4
BASE_BACKOFF = 1.0
MAX_BACKOFF = 12.0
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}
_rate_limit_lock = asyncio.Lock()
def _get_retry_after_seconds(response: httpx.Response):
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None
    try:
        seconds = float(retry_after)
        return max(0.0, seconds)
    except ValueError:
        return None

def _compute_backoff_seconds(attempt: int, response: httpx.Response = None):
    retry_after = _get_retry_after_seconds(response) if response is not None else None
    if retry_after is not None:
        base_wait = min(MAX_BACKOFF, retry_after)
    else:
        base_wait = min(MAX_BACKOFF, BASE_BACKOFF * (2 ** (attempt - 1)))
    return base_wait + random.uniform(0.05, 0.35)

async def rate_limited_request(client, url, params):
    global _last_request_time
    response = None
    last_request_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        async with _rate_limit_lock:
            now = time.time()
            elapsed = now - _last_request_time

            if elapsed < REQUEST_DELAY:
                await asyncio.sleep(REQUEST_DELAY - elapsed)

            _last_request_time = time.time()

            try:
                response = await client.get(url, params=params)
                last_request_error = None
            except httpx.RequestError as e:
                last_request_error = e
                response = None

        if response is None:
            if attempt == MAX_RETRIES:
                if last_request_error is not None:
                    raise last_request_error
                raise RuntimeError(f"Wayback request failed without response for {url}")
            wait_seconds = _compute_backoff_seconds(attempt)
            logging.warning(
                "Wayback request error for %s (attempt %d/%d). Retrying in %.2fs. Error=%s",
                url,
                attempt,
                MAX_RETRIES,
                wait_seconds,
                last_request_error,
            )
            await asyncio.sleep(wait_seconds)
            continue

        if response.status_code not in TRANSIENT_STATUS_CODES:
            return response

        if attempt < MAX_RETRIES:
            wait_seconds = _compute_backoff_seconds(attempt, response)
            logging.warning(
                "Wayback transient status %s for %s (attempt %d/%d). Retrying in %.2fs.",
                response.status_code,
                url,
                attempt,
                MAX_RETRIES,
                wait_seconds,
            )
            await asyncio.sleep(wait_seconds)
            continue

        return response

    if response is not None:
        return response
    raise RuntimeError("Wayback request failed without response")
