import asyncio
import logging

from aggregator import get_timeline

POPULAR_DOMAINS = [
    "youtube.com",
    "google.com",
    "wikipedia.org",
    "twitter.com",
]


async def prewarm_popular_domains():
    logging.info("Prewarming cache for %d popular domains", len(POPULAR_DOMAINS))
    for domain in POPULAR_DOMAINS:
        try:
            result = await get_timeline(domain)
            logging.info("Prewarmed %s — %d years", domain, len(result.get("years", [])))
        except Exception as exc:
            logging.warning("Prewarm failed for %s: %s", domain, exc)
    logging.info("Prewarm complete")


if __name__ == "__main__":
    asyncio.run(prewarm_popular_domains())
