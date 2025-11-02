import grpc
import jobs_pb2
import jobs_pb2_grpc
import argparse
import time
import re
from collections import Counter
from map_reduce.utils import get_logger

logger = get_logger(__name__)


class EngineWorker:
    def __init__(
        self, engine_id: str, role: str, capacity: int, coordinator_address: str
    ):
        self.engine_id = engine_id
        self.role = role
        self.capacity = capacity
        self.coordinator_address = coordinator_address
        self.channel = None
        self.stub = None

    def connect(self):
        try:
            self.channel = grpc.insecure_channel(self.coordinator_address)
            self.stub = jobs_pb2_grpc.JobServiceStub(self.channel)
            logger.info(f"Conectado al coordinador en {self.coordinator_address}")
            return True
        except Exception as e:
            logger.error("Error al conectar: %s", e)
            return False

    def register(self):
        try:
            req = jobs_pb2.RegisterEngineRequest(
                engine_id=self.engine_id, role=self.role, capacity=self.capacity
            )
            res = self.stub.RegisterEngine(req)
            if res.success:
                logger.info("Registrado: %s", res.message)
                return True
            else:
                logger.error("Registro falló: %s", res.message)
                return False
        except Exception as e:
            logger.exception("Error registro: %s", e)
            return False

    def process_map_task(self, task):
        logger.info("Procesando map: %s shard=%s", task.job_id, task.shard_id)
        words = re.findall(r"\b\w+\b", task.text_content.lower())
        wc = Counter(words)
        outputs = []
        for w, c in wc.items():
            outputs.append(jobs_pb2.MapOutput(word=w, count=c))
        logger.info("Map completo: %d palabras únicas", len(wc))
        return outputs

    def process_reduce_task(self, task):
        logger.info("Procesando reduce: %s word=%s", task.job_id, task.word)
        total = sum(task.counts)
        logger.info("Reduce result: %s => %d", task.word, total)
        return total

    def fetch_and_process(self):
        try:
            req = jobs_pb2.FetchJobRequest(engine_id=self.engine_id)
            res = self.stub.FetchJob(req)
            if res.task_type == "none":
                return False
            if res.task_type == "map":
                task = res.map_task
                outputs = self.process_map_task(task)
                report = jobs_pb2.ReportResultRequest(
                    engine_id=self.engine_id,
                    job_id=task.job_id,
                    task_type="map",
                    shard_id=task.shard_id,
                    map_outputs=outputs,
                )
                self.stub.ReportResult(report)
                return True
            elif res.task_type == "reduce":
                task = res.reduce_task
                total = self.process_reduce_task(task)
                report = jobs_pb2.ReportResultRequest(
                    engine_id=self.engine_id,
                    job_id=task.job_id,
                    task_type="reduce",
                    word=task.word,
                    total_count=total,
                )
                self.stub.ReportResult(report)
                return True
        except grpc.RpcError as e:
            logger.error("gRPC error: %s", e)
            return False
        except Exception as e:
            logger.exception("Error processing: %s", e)
            return False

    def run(self):
        logger.info("Iniciando engine %s as %s", self.engine_id, self.role)
        while True:
            if not self.channel:
                if not self.connect():
                    time.sleep(5)
                    continue
                if not self.register():
                    time.sleep(5)
                    self.channel = None
                    continue
            had_work = self.fetch_and_process()
            if not had_work:
                time.sleep(2)
            else:
                time.sleep(0.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-id", required=True)
    parser.add_argument("--role", required=True, choices=["mapper", "reducer"])
    parser.add_argument("--capacity", type=int, default=5)
    parser.add_argument("--coordinator", default="localhost:50051")
    args = parser.parse_args()
    worker = EngineWorker(args.engine_id, args.role, args.capacity, args.coordinator)
    try:
        worker.run()
    except KeyboardInterrupt:
        logger.info("Engine detenido")


if __name__ == "__main__":
    main()
