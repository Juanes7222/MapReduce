from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from .utils import get_logger

logger = get_logger(__name__)


class CoordinatorState:
    def __init__(self):
        self.engines: Dict[str, Dict[str, Any]] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.map_queue: List[Tuple[str, int, str]] = []
        self.reduce_queue: List[Tuple[str, str, List[int]]] = []
        self.balancing_strategy = "round_robin"
        self.round_robin_index = 0
        self.logs: List[Dict[str, str]] = []

    def add_log(self, message: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        self.logs.append({"timestamp": timestamp, "message": message})
        logger.info(message)
        if len(self.logs) > 200:
            self.logs = self.logs[-200:]


# Singleton coordinator instance (usado por grpc_service, api, etc.)
coordinator = CoordinatorState()

__all__ = ["CoordinatorState", "coordinator"]
