import time

from core.utils import logger, prettytimestamp
from services.openaiclient import client

OPENAI_OBJECTS_TTL = 3 * 24 * 60 * 60

def cleanup():
    now = time.time()

    expired_file_ids = []
    for file_obj in client.files.list():
        logger.debug(f"file {prettytimestamp(file_obj.created_at)} {file_obj.id} {file_obj.filename}")
        if now - file_obj.created_at >= OPENAI_OBJECTS_TTL:
            logger.debug(f"expired {file_obj.id}")
            expired_file_ids.append(file_obj.id)
    for file_id in expired_file_ids:
        logger.debug(f"delete {file_id}")
        client.files.delete(file_id)

    expired_vector_store_ids = []
    for vector_store in client.vector_stores.list():
        logger.debug(f"file {prettytimestamp(vector_store.created_at)} {vector_store.id}")
        if now - vector_store.created_at >= OPENAI_OBJECTS_TTL:
            logger.debug(f"expired {vector_store.id}")
            expired_vector_store_ids.append(vector_store.id)
    for vector_store_id in expired_vector_store_ids:
        logger.debug(f"delete {vector_store_id}")
        client.vector_stores.delete(vector_store_id)

    expired_assistant_ids = []
    for assistant in client.beta.assistants.list():
        logger.debug(f"file {prettytimestamp(assistant.created_at)} {assistant.id}")
        if now - assistant.created_at >= OPENAI_OBJECTS_TTL:
            logger.debug(f"expired {assistant.id}")
            expired_assistant_ids.append(assistant.id)
    for assistant_id in expired_assistant_ids:
        logger.debug(f"delete {assistant_id}")
        client.beta.assistants.delete(assistant_id)

cleanup()
