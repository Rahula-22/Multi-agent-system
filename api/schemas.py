from pydantic import BaseModel
from typing import Optional, List

class InputMetadata(BaseModel):
    source: str
    type: str
    timestamp: str

class ExtractedField(BaseModel):
    field_name: str
    value: str

class EmailRecord(BaseModel):
    sender_name: str
    request_intent: str
    urgency: Optional[str] = None
    conversation_id: Optional[str] = None

class JSONRecord(BaseModel):
    data: dict
    anomalies: Optional[List[str]] = None

class ClassifierOutput(BaseModel):
    format: str
    intent: str
    extracted_fields: List[ExtractedField]