from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from contextlib import asynccontextmanager
from .models import JobCreate, JobResponse, EngineInfo, LogEntry
from .db import get_mongo_client, close_client
from .coordinator import coordinator
from typing import List
from .utils import get_logger, env
from collections import defaultdict
import uuid
import time
import re
from datetime import datetime, timezone

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        yield
    finally:
        try:
            close_client()
            logger.info("Lifespan: Mongo client closed")
        except Exception as e:
            logger.exception("Error closing mongo client: %s", e)


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    api_router = APIRouter(prefix="/api")

    @api_router.post("/jobs", response_model=JobResponse)
    async def create_job(job_data: JobCreate):
        try:
            job_id = str(uuid.uuid4())
            text = job_data.text
            words = re.findall(r"\b\w+\b", text.lower())
            shard_size = max(100, len(words) // 4)
            shards = []
            for i in range(0, len(words), shard_size):
                shards.append(" ".join(words[i : i + shard_size]))
            num_shards = len(shards)

            job = {
                "job_id": job_id,
                "text": text,
                "status": "map",
                "num_shards": num_shards,
                "completed_shards": 0,
                "map_results": defaultdict(list),
                "reduce_results": {},
                "num_reduce_tasks": 0,
                "completed_reduce_tasks": 0,
                "top_words": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
            }
            coordinator.jobs[job_id] = job
            coordinator.balancing_strategy = (
                job_data.balancing_strategy or "round_robin"
            )
            for idx, shard in enumerate(shards):
                coordinator.map_queue.append((job_id, idx, shard))

            # Save summary to MongoDB (non-blocking)
            client = get_mongo_client()
            db = client[env("APPNAME", "MapReduce")]
            await db.jobs.insert_one(
                {
                    "job_id": job_id,
                    "text_length": len(text),
                    "num_shards": num_shards,
                    "status": "map",
                    "created_at": job["created_at"],
                }
            )

            coordinator.add_log(f"Trabajo {job_id} creado con {num_shards} shards")
            return JobResponse(
                job_id=job_id,
                status="map",
                text_length=len(text),
                num_shards=num_shards,
                created_at=job["created_at"],
            )
        except Exception as exc:
            logger.exception("Error creando job: %s", exc)
            raise HTTPException(
                status_code=500, detail="Internal server error while creating job"
            )

    @api_router.post("/jobs/upload")
    async def upload_job(file: UploadFile = File(...)):
        content = await file.read()
        text = content.decode("utf-8")
        return await create_job(JobCreate(text=text))

    @api_router.get("/jobs", response_model=List[JobResponse])
    async def list_jobs():
        jobs_list = []
        for job_id, job in coordinator.jobs.items():
            duration = None
            if job["completed_at"]:
                start = datetime.fromisoformat(job["created_at"])
                end = datetime.fromisoformat(job["completed_at"])
                duration = (end - start).total_seconds()
            jobs_list.append(
                JobResponse(
                    job_id=job_id,
                    status=job["status"],
                    text_length=len(job["text"]),
                    num_shards=job["num_shards"],
                    top_words=job["top_words"],
                    created_at=job["created_at"],
                    completed_at=job["completed_at"],
                    duration_seconds=duration,
                )
            )
        return jobs_list

    @api_router.get("/jobs/{job_id}", response_model=JobResponse)
    async def get_job(job_id: str):
        if job_id not in coordinator.jobs:
            raise HTTPException(status_code=404, detail="Trabajo no encontrado")
        job = coordinator.jobs[job_id]
        duration = None
        if job["completed_at"]:
            start = datetime.fromisoformat(job["created_at"])
            end = datetime.fromisoformat(job["completed_at"])
            duration = (end - start).total_seconds()
        return JobResponse(
            job_id=job_id,
            status=job["status"],
            text_length=len(job["text"]),
            num_shards=job["num_shards"],
            top_words=job["top_words"],
            created_at=job["created_at"],
            completed_at=job["completed_at"],
            duration_seconds=duration,
        )

    @api_router.get("/engines", response_model=List[EngineInfo])
    async def list_engines():
        engines_list = []
        current_time = time.time()
        for engine_id, engine in coordinator.engines.items():
            time_since_seen = current_time - engine["last_seen"]
            status = "active" if time_since_seen < 10 else "idle"
            engines_list.append(
                EngineInfo(
                    engine_id=engine_id,
                    role=engine["role"],
                    capacity=engine["capacity"],
                    current_load=engine["current_load"],
                    last_seen=datetime.fromtimestamp(
                        engine["last_seen"], tz=timezone.utc
                    ).isoformat(),
                    status=status,
                )
            )
        return engines_list

    @api_router.get("/logs", response_model=List[LogEntry])
    async def get_logs():
        return coordinator.logs[-50:]

    @api_router.get("/stats")
    async def get_stats():
        return {
            "total_engines": len(coordinator.engines),
            "mappers": len(
                [e for e in coordinator.engines.values() if e["role"] == "mapper"]
            ),
            "reducers": len(
                [e for e in coordinator.engines.values() if e["role"] == "reducer"]
            ),
            "map_queue_size": len(coordinator.map_queue),
            "reduce_queue_size": len(coordinator.reduce_queue),
            "total_jobs": len(coordinator.jobs),
            "active_jobs": len(
                [j for j in coordinator.jobs.values() if j["status"] != "completada"]
            ),
        }

    app.include_router(api_router)

    # CORS config
    from fastapi.middleware.cors import CORSMiddleware

    _cors_raw = env("CORS_ORIGINS", "*").strip()
    if _cors_raw == "*":
        _allow_origins = ["*"]
        _allow_credentials = False
    else:
        _allow_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
        _allow_credentials = True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=_allow_credentials,
    )

    return app
