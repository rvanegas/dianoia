import io
import json
import time
from dataclasses import dataclass, asdict

from config import OPENAI_MODEL
from core.utils import logger
from services.openaiclient import client

@dataclass
class FileData:
    content: bytes
    filename: str

@dataclass
class FileRef:
    assistant_id: str
    filename: str

def create_file(file_data: FileData):
    file_obj = io.BytesIO(file_data.content)
    file_obj.name = file_data.filename
    f_response = client.files.create(
        file=file_obj,
        purpose="assistants")
    vs_response = client.vector_stores.create()
    client.vector_stores.files.create_and_poll(
        vector_store_id=vs_response.id,
        file_id=f_response.id)
    a_response = client.beta.assistants.create(
        model=OPENAI_MODEL,
        tools=[{"type": "file_search"}],
        tool_resources={"file_search": {"vector_store_ids": [vs_response.id]}})
    expire_old_files()
    file_ref = FileRef(
        assistant_id=a_response.id,
        filename=f_response.filename)
    return json.dumps(asdict(file_ref))

one_day_in_seconds = 24 * 60 * 60

def expire_old_files():
    now = time.time()
    expired_file_ids = []
    expired_vector_store_ids = []
    expired_assistant_ids = []
    for file_obj in client.files.list():
        logger.debug(f"file {file_obj.id} {file_obj.filename} {file_obj.created_at}")
        if now - file_obj.created_at >= one_day_in_seconds:
            logger.debug(f"expired {file_obj.id}")
            expired_file_ids.append(file_obj.id)
    for file_id in expired_file_ids:
        client.files.delete(file_id)
    for vector_store in client.vector_stores.list():
        logger.debug(f"file {vector_store.id} {vector_store.created_at}")
        if now - vector_store.created_at >= one_day_in_seconds:
            logger.debug(f"expired {vector_store.id}")
            expired_vector_store_ids.append(vector_store.id)
    for vector_store_id in expired_vector_store_ids:
        client.vector_stores.delete(vector_store_id)
    for assistant in client.beta.assistants.list():
        logger.debug(f"file {assistant.id} {assistant.created_at}")
        if now - assistant.created_at >= one_day_in_seconds:
            logger.debug(f"expired {assistant.id}")
            expired_assistant_ids.append(assistant.id)
    for assitant_id in expired_assistant_ids:
        client.assitants.delete(assitant_id)
