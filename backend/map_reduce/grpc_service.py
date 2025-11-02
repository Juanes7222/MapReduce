from datetime import datetime, timezone
import jobs_pb2
import jobs_pb2_grpc
import time
from .coordinator import coordinator
from .utils import get_logger

logger = get_logger(__name__)


class JobServiceServicer(jobs_pb2_grpc.JobServiceServicer):
    def RegisterEngine(self, request, context):
        engine_id = request.engine_id
        role = request.role
        capacity = request.capacity
        coordinator.engines[engine_id] = {
            "role": role,
            "capacity": capacity,
            "current_load": 0,
            "last_seen": time.time(),
        }
        coordinator.add_log(
            f"Engine {engine_id} registrado como {role} con capacidad {capacity}"
        )
        return jobs_pb2.RegisterEngineReply(
            success=True, message=f"Engine {engine_id} registrado correctamente"
        )

    def FetchJob(self, request, context):
        engine_id = request.engine_id
        if engine_id not in coordinator.engines:
            return jobs_pb2.FetchJobReply(task_type="none")
        engine = coordinator.engines[engine_id]
        engine["last_seen"] = time.time()
        if engine["current_load"] >= engine["capacity"]:
            return jobs_pb2.FetchJobReply(task_type="none")

        if engine["role"] == "mapper" and coordinator.map_queue:
            job_id, shard_id, text = coordinator.map_queue.pop(0)
            engine["current_load"] += 1
            coordinator.add_log(
                f"Tarea de mapeo asignada (Trabajo={job_id}, shard={shard_id}) a {engine_id}"
            )
            return jobs_pb2.FetchJobReply(
                task_type="map",
                map_task=jobs_pb2.MapTask(
                    job_id=job_id, shard_id=shard_id, text_content=text
                ),
            )

        if engine["role"] == "reducer" and coordinator.reduce_queue:
            job_id, word, counts = coordinator.reduce_queue.pop(0)
            engine["current_load"] += 1
            coordinator.add_log(
                f"Tarea de reducción asignada (Trabajo={job_id}, palabra={word}) a {engine_id}"
            )
            return jobs_pb2.FetchJobReply(
                task_type="reduce",
                reduce_task=jobs_pb2.ReduceTask(
                    job_id=job_id, word=word, counts=counts
                ),
            )
        return jobs_pb2.FetchJobReply(task_type="none")

    def ReportResult(self, request, context):
        engine_id = request.engine_id
        job_id = request.job_id
        task_type = request.task_type

        if engine_id in coordinator.engines:
            # defensive: never go below 0
            coordinator.engines[engine_id]["current_load"] = max(
                0, coordinator.engines[engine_id]["current_load"] - 1
            )

        if job_id not in coordinator.jobs:
            return jobs_pb2.ReportResultReply(
                success=False, message="Trabajo no encontrado"
            )

        job = coordinator.jobs[job_id]

        if task_type == "map":
            shard_id = request.shard_id
            job["completed_shards"] += 1
            for output in request.map_outputs:
                job["map_results"][output.word].append(output.count)
            coordinator.add_log(
                f"Resultado de mapeo recibido de {engine_id} (Trabajo={job_id}, shard={shard_id})"
            )
            if job["completed_shards"] == job["num_shards"]:
                job["status"] = "reduciendo"
                for word, counts in job["map_results"].items():
                    coordinator.reduce_queue.append((job_id, word, counts))
                job["num_reduce_tasks"] = len(job["map_results"])
                coordinator.add_log(
                    f"Job {job_id} pasa a REDUCCIÓN con {job['num_reduce_tasks']} tareas"
                )

        elif task_type == "reduce":
            word = request.word
            total = request.total_count
            job["reduce_results"][word] = total
            job["completed_reduce_tasks"] += 1
            coordinator.add_log(
                f"Resultado de reducción recibido de {engine_id} (Trabajo={job_id}, palabra={word}, conteo={total})"
            )
            if job["completed_reduce_tasks"] == job.get("num_reduce_tasks", 0):
                job["status"] = "completada"
                job["completed_at"] = datetime.now(timezone.utc).isoformat()
                sorted_words = sorted(
                    job["reduce_results"].items(), key=lambda x: x[1], reverse=True
                )
                job["top_words"] = [
                    {"word": w, "count": c} for w, c in sorted_words[:10]
                ]
                coordinator.add_log(
                    f"Trabajo {job_id} COMPLETADO con {len(sorted_words)} palabras únicas"
                )

        return jobs_pb2.ReportResultReply(success=True, message="Resultado recibido")
