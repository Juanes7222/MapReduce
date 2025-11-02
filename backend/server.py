from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import grpc
from concurrent import futures
import threading
import time
import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict
import re

# Import generated gRPC code
import jobs_pb2
import jobs_pb2_grpc

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
mongo_password = os.environ['DB_PASSWORD']
app_name = os.environ['APPNAME']
host = os.environ['HOST']
username = os.environ['DB_USERNAME']
options = os.environ['OPTIONS']

mongo_url = mongo_url.format(USERNAME=username, HOST=host, OPTIONS=options, DB_PASSWORD=mongo_password)
print(f"Conectando a MongoDB en {mongo_url}")
client = AsyncIOMotorClient(mongo_url)
db = client[app_name]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for MapReduce coordination
class CoordinatorState:
    def __init__(self):
        self.engines = {}  # engine_id -> {role, capacity, current_load, last_seen}
        self.jobs = {}  # job_id -> {status, shards, map_results, reduce_tasks, results}
        self.map_queue = []  # list of (job_id, shard_id, text)
        self.reduce_queue = []  # list of (job_id, word, counts)
        self.balancing_strategy = 'round_robin'  # or 'least_loaded'
        self.round_robin_index = 0
        self.logs = []  # activity logs
        
    def add_log(self, message):
        timestamp = datetime.now(timezone.utc).isoformat()
        self.logs.append({"timestamp": timestamp, "message": message})
        logger.info(message)
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

coordinator = CoordinatorState()

# Pydantic models
class JobCreate(BaseModel):
    text: str
    balancing_strategy: Optional[str] = 'round_robin'

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

# gRPC Service Implementation
class JobServiceServicer(jobs_pb2_grpc.JobServiceServicer):
    def RegisterEngine(self, request, context):
        engine_id = request.engine_id
        role = request.role
        capacity = request.capacity
        
        coordinator.engines[engine_id] = {
            'role': role,
            'capacity': capacity,
            'current_load': 0,
            'last_seen': time.time()
        }
        
        coordinator.add_log(f"Engine {engine_id} registrado como {role} con una capacidad de {capacity}")
        
        return jobs_pb2.RegisterEngineReply(
            success=True,
            message=f"Engine {engine_id} registrado correctamente"
        )
    
    def FetchJob(self, request, context):
        engine_id = request.engine_id
        
        if engine_id not in coordinator.engines:
            return jobs_pb2.FetchJobReply(task_type="none")
        
        engine = coordinator.engines[engine_id]
        engine['last_seen'] = time.time()
        
        # Check if engine has capacity
        if engine['current_load'] >= engine['capacity']:
            return jobs_pb2.FetchJobReply(task_type="none")
        
        # Assign map task
        if engine['role'] == 'mapper' and coordinator.map_queue:
            job_id, shard_id, text = coordinator.map_queue.pop(0)
            engine['current_load'] += 1
            
            coordinator.add_log(f"Tarea de mapeo asignada (Trabajo={job_id}, shard={shard_id}) a {engine_id}")
            
            return jobs_pb2.FetchJobReply(
                task_type="map",
                map_task=jobs_pb2.MapTask(
                    job_id=job_id,
                    shard_id=shard_id,
                    text_content=text
                )
            )
        
        # Assign reduce task
        if engine['role'] == 'reducer' and coordinator.reduce_queue:
            job_id, word, counts = coordinator.reduce_queue.pop(0)
            engine['current_load'] += 1
            
            coordinator.add_log(f"Tarea de reducción asignada (Trabajo={job_id}, palabra={word}) a {engine_id}")
            
            return jobs_pb2.FetchJobReply(
                task_type="reduce",
                reduce_task=jobs_pb2.ReduceTask(
                    job_id=job_id,
                    word=word,
                    counts=counts
                )
            )
        
        return jobs_pb2.FetchJobReply(task_type="none")
    
    def ReportResult(self, request, context):
        engine_id = request.engine_id
        job_id = request.job_id
        task_type = request.task_type
        
        if engine_id in coordinator.engines:
            coordinator.engines[engine_id]['current_load'] -= 1
        
        if job_id not in coordinator.jobs:
            return jobs_pb2.ReportResultReply(success=False, message="Trabajo no encontrado")
        
        job = coordinator.jobs[job_id]
        
        if task_type == "map":
            shard_id = request.shard_id
            job['completed_shards'] += 1
            
            # Store map outputs
            for output in request.map_outputs:
                job['map_results'][output.word].append(output.count)
            
            coordinator.add_log(f"Resultado de mapeo recibido de {engine_id} (Trabajo={job_id}, shard={shard_id})")
            
            # Check if all map tasks complete
            if job['completed_shards'] == job['num_shards']:
                job['status'] = 'shuffle'
                coordinator.add_log(f"Job {job_id} entering SHUFFLE phase")
                
                # Create reduce tasks
                for word, counts in job['map_results'].items():
                    coordinator.reduce_queue.append((job_id, word, counts))
                
                job['status'] = 'reduciendo'
                job['num_reduce_tasks'] = len(job['map_results'])
                coordinator.add_log(f"El Trabajo {job_id} entra en la fase de REDUCCIÓN con {job['num_reduce_tasks']} tareas")
        
        elif task_type == "reduce":
            word = request.word
            total_count = request.total_count
            
            job['reduce_results'][word] = total_count
            job['completed_reduce_tasks'] += 1
            
            coordinator.add_log(f"Resultado de reducción recibido de {engine_id} (Trabajo={job_id}, palabra={word}, conteo={total_count})")
            
            # Check if all reduce tasks complete
            if job['completed_reduce_tasks'] == job['num_reduce_tasks']:
                job['status'] = 'completada'
                job['completed_at'] = datetime.now(timezone.utc).isoformat()
                
                # Calculate top-K words
                sorted_words = sorted(job['reduce_results'].items(), key=lambda x: x[1], reverse=True)
                job['top_words'] = [{"word": w, "count": c} for w, c in sorted_words[:10]]
                
                coordinator.add_log(f"Trabajo {job_id} COMPLETADO con {len(sorted_words)} palabras únicas")
        
        return jobs_pb2.ReportResultReply(success=True, message="Resultado recibido")

def start_grpc_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    jobs_pb2_grpc.add_JobServiceServicer_to_server(JobServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Servidor gRPC iniciado en el puerto 50051")
    server.wait_for_termination()

# Start gRPC server in a separate thread
grpc_thread = threading.Thread(target=start_grpc_server, daemon=True)
grpc_thread.start()

# Heartbeat checker
def heartbeat_checker():
    while True:
        time.sleep(5)
        current_time = time.time()
        dead_engines = []
        
        for engine_id, engine in coordinator.engines.items():
            if current_time - engine['last_seen'] > 15:  # 15 seconds timeout
                dead_engines.append(engine_id)
        
        for engine_id in dead_engines:
            coordinator.add_log(f"Engine {engine_id} marcado como inactivo (sin señal de vida)")
            del coordinator.engines[engine_id]

heartbeat_thread = threading.Thread(target=heartbeat_checker, daemon=True)
heartbeat_thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: runs during startup/shutdown.

    Ensures the MongoDB client is closed cleanly on shutdown (replaces
    deprecated @app.on_event("shutdown")).
    """
    try:
        yield
    finally:
        try:
            client.close()
            logger.info("Cliente de MongoDB cerrado durante el apagado")
        except Exception as e:
            logger.exception(f"Error al cerrar el cliente de MongoDB: {e}")

# FastAPI app (use lifespan handler instead of on_event)
app = FastAPI(lifespan=lifespan)
api_router = APIRouter(prefix="/api")

@api_router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate):
    try:
        job_id = str(uuid.uuid4())
        text = job_data.text

        # Partition text into shards (simple: split by lines or chunks)
        words = re.findall(r'\b\w+\b', text.lower())
        shard_size = max(100, len(words) // 4)  # At least 100 words per shard
        shards = []

        for i in range(0, len(words), shard_size):
            shard_text = ' '.join(words[i:i+shard_size])
            shards.append(shard_text)

        num_shards = len(shards)

        # Create job
        job = {
            'job_id': job_id,
            'text': text,
            'status': 'map',
            'num_shards': num_shards,
            'completed_shards': 0,
            'map_results': defaultdict(list),
            'reduce_results': {},
            'num_reduce_tasks': 0,
            'completed_reduce_tasks': 0,
            'top_words': None,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': None
        }

        coordinator.jobs[job_id] = job
        coordinator.balancing_strategy = job_data.balancing_strategy or 'round_robin'

        # Add shards to map queue
        for idx, shard in enumerate(shards):
            coordinator.map_queue.append((job_id, idx, shard))

        # Save to MongoDB
        await db.jobs.insert_one({
            'job_id': job_id,
            'text_length': len(text),
            'num_shards': num_shards,
            'status': 'map',
            'created_at': job['created_at']
        })

        coordinator.add_log(f"Trabajo {job_id} creado con {num_shards} shards")

        return JobResponse(
            job_id=job_id,
            status='map',
            text_length=len(text),
            num_shards=num_shards,
            created_at=job['created_at']
        )
    except Exception as exc:
        # Log full exception server-side for debugging and return controlled 500
        logger.exception(f"Error al crear el Trabajo: {exc}")
        # Raise HTTPException so FastAPI can format the response and CORS middleware
        # still applies. Include minimal message to avoid leaking sensitive info.
        raise HTTPException(status_code=500, detail="Internal server error while creating job")

@api_router.post("/jobs/upload")
async def upload_job(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode('utf-8')
    
    job_data = JobCreate(text=text)
    return await create_job(job_data)

@api_router.get("/jobs", response_model=List[JobResponse])
async def list_jobs():
    jobs_list = []
    
    for job_id, job in coordinator.jobs.items():
        duration = None
        if job['completed_at']:
            start = datetime.fromisoformat(job['created_at'])
            end = datetime.fromisoformat(job['completed_at'])
            duration = (end - start).total_seconds()
        
        jobs_list.append(JobResponse(
            job_id=job_id,
            status=job['status'],
            text_length=len(job['text']),
            num_shards=job['num_shards'],
            top_words=job['top_words'],
            created_at=job['created_at'],
            completed_at=job['completed_at'],
            duration_seconds=duration
        ))
    
    return jobs_list

@api_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    if job_id not in coordinator.jobs:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    
    job = coordinator.jobs[job_id]
    duration = None
    
    if job['completed_at']:
        start = datetime.fromisoformat(job['created_at'])
        end = datetime.fromisoformat(job['completed_at'])
        duration = (end - start).total_seconds()
    
    return JobResponse(
        job_id=job_id,
        status=job['status'],
        text_length=len(job['text']),
        num_shards=job['num_shards'],
        top_words=job['top_words'],
        created_at=job['created_at'],
        completed_at=job['completed_at'],
        duration_seconds=duration
    )

@api_router.get("/engines", response_model=List[EngineInfo])
async def list_engines():
    engines_list = []
    current_time = time.time()
    
    for engine_id, engine in coordinator.engines.items():
        time_since_seen = current_time - engine['last_seen']
        status = 'active' if time_since_seen < 10 else 'idle'
        
        engines_list.append(EngineInfo(
            engine_id=engine_id,
            role=engine['role'],
            capacity=engine['capacity'],
            current_load=engine['current_load'],
            last_seen=datetime.fromtimestamp(engine['last_seen'], tz=timezone.utc).isoformat(),
            status=status
        ))
    
    return engines_list

@api_router.get("/logs", response_model=List[LogEntry])
async def get_logs():
    return coordinator.logs[-50:]  # Return last 50 logs

@api_router.get("/stats")
async def get_stats():
    return {
        'total_engines': len(coordinator.engines),
        'mappers': len([e for e in coordinator.engines.values() if e['role'] == 'mapper']),
        'reducers': len([e for e in coordinator.engines.values() if e['role'] == 'reducer']),
        'map_queue_size': len(coordinator.map_queue),
        'reduce_queue_size': len(coordinator.reduce_queue),
        'total_jobs': len(coordinator.jobs),
        'active_jobs': len([j for j in coordinator.jobs.values() if j['status'] != 'completada'])
    }

app.include_router(api_router)

# Configure CORS origins and credentials based on environment variable.
# If CORS_ORIGINS is set to '*' we must NOT set allow_credentials=True
# because browsers disallow wildcard origin with credentials.
# Accept comma-separated origins in the env var.
_cors_raw = os.environ.get('CORS_ORIGINS', '*').strip()
if _cors_raw == '*':
    _allow_origins = ['*']
    _allow_credentials = False
else:
    _allow_origins = [o.strip() for o in _cors_raw.split(',') if o.strip()]
    _allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_credentials=_allow_credentials,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
