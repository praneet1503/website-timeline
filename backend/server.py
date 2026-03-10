from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from cachetools import TTLCache

app = FastAPI()
#allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#cache results for 1 hours
cache = TTLCache(maxsize=200, ttl=3600)
WAYBACK_API = "https://web.archive.org/cdx/search/cdx"

def fetch_wayback(domain: str):

    # try domain and www.domain
    possible_domains = [domain, f"www.{domain}"]

    for d in possible_domains:

        params = {
            "url": d,
            "output": "json",
            "fl": "timestamp,statuscode",
            "filter": "statuscode:200",
            "collapse": "timestamp:8",
            "matchType": "domain"
        }

        try:
            r = requests.get(WAYBACK_API, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            continue

        if len(data) > 1:
            years = set()
            for row in data[1:]:
                timestamp = row[0]
                years.add(timestamp[:4])
            return sorted(list(years))

    # fallback empty
    return []

@app.get("/timeline")
def get_timeline(domain:str):
    if domain in cache:
        return {
            "domain":domain,
            "years":cache[domain],
            "cached":True
        }
    years = fetch_wayback(domain)
    cache[domain]=years
    return {
        "domain":domain,
        "years":years,
        "cached":False
    }