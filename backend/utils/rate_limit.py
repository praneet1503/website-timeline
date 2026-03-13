import asyncio
import logging
import random
import time

import httpx

REQUEST_DELAY = 0.5
MAX_RETRIES = 3
BASE_BACKOFF = 1.0
MAX_BACKOFF = 8.0
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

_last_request_time = 0.0
_lock = asyncio.Lock()


def _retry_after(response: httpx.Response) -> float | None:
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return max(0.0, float(header))
    except ValueError:
        return None


def _backoff(attempt: int, response: httpx.Response | None = None) -> float:
    ra = _retry_after(response) if response else None
    base = min(MAX_BACKOFF, ra) if ra is not None else min(MAX_BACKOFF, BASE_BACKOFF * (2 ** attempt))
    return base + random.uniform(0.05, 0.3)


async def rate_limited_request(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
) -> httpx.Response:
    global _last_request_time

    last_error: Exception | None = None
    last_response: httpx.Response | None = None

    for attempt in range(MAX_RETRIES):
        async with _lock:
            now = time.monotonic()
            wait = REQUEST_DELAY - (now - _last_request_time)
            if wait > 0:
                await asyncio.sleep(wait)
            _last_request_time = time.monotonic()

        try:
            resp = await client.get(url, params=params)
            last_response = resp
            last_error = None
        except httpx.RequestError as exc:
            last_error = exc
            last_response = None
            if attempt < MAX_RETRIES - 1:
                delay = _backoff(attempt)
                logging.warning("Request error (attempt %d/%d), retrying in %.2fs: %s", attempt + 1, MAX_RETRIES, delay, exc)
                await asyncio.sleep(delay)
            continue

        if resp.status_code not in TRANSIENT_STATUS_CODES:
            return resp

        if attempt < MAX_RETRIES - 1:
            delay = _backoff(attempt, resp)
            logging.warning("Transient %s (attempt %d/%d), retrying in %.2fs", resp.status_code, attempt + 1, MAX_RETRIES, delay)
            await asyncio.sleep(delay)

    if last_response is not None:
        return last_response
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"rate_limited_request exhausted retries for {url}")
