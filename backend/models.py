from pydantic import BaseModel
from typing import List


class TimelineResponse(BaseModel):
    domain: str
    years: List[str]
    cached: bool


class Snapshot(BaseModel):
    timestamp: str
    date: str
    url: str


class SnapshotResponse(BaseModel):
    domain: str
    year: str
    snapshots: List[Snapshot]
    cached: bool = False


class HealthResponse(BaseModel):
    status: str