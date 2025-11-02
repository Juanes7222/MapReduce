from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class JobCreate(BaseModel):
    text: str
    balancing_strategy: Optional[str] = "round_robin"

class JobResponse(BaseModel):
    job_id: str
    status: str
    text_length: int
    num_shards: int
    top_words: Optional[List[Dict[str, Any]]] = None
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None

class EngineInfo(BaseModel):
    engine_id: str
    role: str
    capacity: int
    current_load: int
    last_seen: str
    status: str

class LogEntry(BaseModel):
    timestamp: str
    message: str