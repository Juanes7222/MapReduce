from motor.motor_asyncio import AsyncIOMotorClient
from .utils import env, get_logger
logger = get_logger(__name__)

_client = None

def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client:
        return _client

    mongo_url = env("MONGO_URL")
    db_password = env("DB_PASSWORD")
    username = env("DB_USERNAME")
    host = env("HOST")
    options = env("OPTIONS", "")
    mongo_url = mongo_url.format(USERNAME=username, HOST=host, OPTIONS=options, DB_PASSWORD=db_password)
    logger.info(f"Conectando a MongoDB en {host}")
    _client = AsyncIOMotorClient(mongo_url)
    return _client

def close_client():
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Cliente MongoDB cerrado")