import io
import json
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
    vector_store_id: str
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
    file_ref = FileRef(
        vector_store_id=vs_response.id,
        filename=f_response.filename)
    return json.dumps(asdict(file_ref))
