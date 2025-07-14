from core.utils import logger
from services.openaiclient import client
from config import VECTOR_STORE_ID

response = client.vector_stores.files.list(VECTOR_STORE_ID)
for f in response:
    logger.debug(f)
