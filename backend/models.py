from pydantic import BaseModel
from typing import List, Dict, Optional

class TimelineResponse(BaseModel):
    """Response for GET /timeline — list of years a domain was archived."""
    domain: str
    years: List[str]
    cached: bool


class Snapshot(BaseModel):
    """A single archived snapshot of a website."""
    timestamp: str     
    date: str          
    url: str           


class SnapshotResponse(BaseModel):
    """Response for GET /snapshots — daily snapshots for a domain+year."""
    snapshots: List[Snapshot]
    cached: bool = False


class HealthResponse(BaseModel):
    """Response for GET /health — simple liveness check."""
    status: str


class ActivityResponse(BaseModel):
    """
    Response for GET /activity — yearly snapshot counts.
    activity is a dict like { "2005": 120, "2006": 340 }
    """
    domain: str
    activity: Dict[str, int]
    cached: bool = False


class ClosestResponse(BaseModel):
    """
    Response for GET /closest — the single nearest snapshot to a date.
    Returns null-safe fields; check 'found' to see if a match exists.
    """
    domain: str
    found: bool
    timestamp: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None