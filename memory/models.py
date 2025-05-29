from pydantic import BaseModel
from typing import Optional, Dict, Any

class InputMetadata(BaseModel):
    source: str
    type: str
    timestamp: str

class ExtractedField(BaseModel):
    field_name: str
    value: Any

class MemoryRecord(BaseModel):
    input_metadata: InputMetadata
    extracted_fields: Dict[str, ExtractedField]
    conversation_id: Optional[str] = None

class SharedMemoryModel(BaseModel):
    records: Dict[str, MemoryRecord]
