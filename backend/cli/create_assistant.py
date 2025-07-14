from core.utils import logger
from services.openaiclient import client
from config import OPENAI_MODEL

response = client.beta.assistants.create(model=OPENAI_MODEL)
logger.debug(response)
