import time
from core.utils import logger

from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

ONE_DAY_IN_SECONDS = 24 * 60 * 60

def cleanup():
    now = time.time()

    expired_file_ids = []
    for file_obj in client.files.list():
        logger.debug(f"file {file_obj.id} {file_obj.filename} {file_obj.created_at}")
        if now - file_obj.created_at >= ONE_DAY_IN_SECONDS:
            logger.debug(f"expired {file_obj.id}")
            expired_file_ids.append(file_obj.id)
    for file_id in expired_file_ids:
        logger.debug(f"delete {file_id}")
        client.files.delete(file_id)

    expired_vector_store_ids = []
    for vector_store in client.vector_stores.list():
        logger.debug(f"file {vector_store.id} {vector_store.created_at}")
        if now - vector_store.created_at >= ONE_DAY_IN_SECONDS:
            logger.debug(f"expired {vector_store.id}")
            expired_vector_store_ids.append(vector_store.id)
    for vector_store_id in expired_vector_store_ids:
        logger.debug(f"delete {vector_store_id}")
        client.vector_stores.delete(vector_store_id)

    expired_assistant_ids = []
    for assistant in client.beta.assistants.list():
        logger.debug(f"file {assistant.id} {assistant.created_at}")
        if now - assistant.created_at >= ONE_DAY_IN_SECONDS:
            logger.debug(f"expired {assistant.id}")
            expired_assistant_ids.append(assistant.id)
    for assitant_id in expired_assistant_ids:
        logger.debug(f"delete {assistant_id}")
        client.assitants.delete(assitant_id)
