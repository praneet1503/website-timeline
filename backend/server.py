import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from aggregator import get_timeline, get_snapshots
from cache import ensure_cache_files
from models import TimelineResponse, SnapshotResponse, HealthResponse
from prewarm import prewarm_popular_domains

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        ensure_cache_files()
    except Exception as exc:
        logging.warning("Cache init failed (non-fatal): %s", exc)
    asyncio.create_task(prewarm_popular_domains())
    yield

app = FastAPI(
    title="Website Timeline API",
    description="Explore historical versions of any website via the Wayback Machine.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/timeline", response_model=TimelineResponse)
async def timeline_endpoint(domain: str = Query(..., description="Domain to look up")):
    return await get_timeline(domain)

@app.get("/snapshots", response_model=SnapshotResponse)
async def snapshots_endpoint(
    domain: str = Query(..., description="Domain to look up"),
    year: str = Query(..., description="Year to fetch snapshots for"),
):
    return await get_snapshots(domain, year)

@app.get("/health", response_model=HealthResponse)
async def health_endpoint():
    return {"status": "ok"}

