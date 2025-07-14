from core.utils import logger
from services.openaiclient import client

response = client.vector_stores.create()
logger.debug(response.id)
