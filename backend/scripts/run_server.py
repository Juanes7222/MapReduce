import uvicorn
from map_reduce.api import create_app
from map_reduce.grpc_server import start_grpc_server
from map_reduce.utils import get_logger

logger = get_logger(__name__)


def main():
    # Start gRPC server in background thread
    grpc_server = start_grpc_server(port=50051, max_workers=10)

    # Start uvicorn (blocking)
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
