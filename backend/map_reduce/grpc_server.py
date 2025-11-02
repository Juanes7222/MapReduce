import grpc
from concurrent import futures
import jobs_pb2_grpc
from .grpc_service import JobServiceServicer
from .utils import get_logger

logger = get_logger(__name__)


def start_grpc_server(port: int = 50051, max_workers: int = 10):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    jobs_pb2_grpc.add_JobServiceServicer_to_server(JobServiceServicer(), server)
    address = f"[::]:{port}"
    server.add_insecure_port(address)
    server.start()
    logger.info(f"Servidor gRPC iniciado en {address}")
    return server
