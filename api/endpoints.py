from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, Union, List
import uvicorn
import json
import os
import sqlite3

from agents.classifier_agent import ClassifierAgent
from memory.memory_store import MemoryStore

# Models
class ProcessInput(BaseModel):
    content: str
    conversation_id: Optional[str] = None
    file_name: Optional[str] = None
    
class EmailInput(BaseModel):
    content: str
    conversation_id: Optional[str] = None

class JsonInput(BaseModel):
    data: Dict[str, Any]
    conversation_id: Optional[str] = None

# Initialize app and dependencies
app = FastAPI(title="Multi-Agent AI System")
memory_store = MemoryStore()
classifier = ClassifierAgent(memory_store)

# Utility functions
def find_related_inputs(memory_store, conversation_id: str) -> List[str]:
    """Find all inputs related to the current conversation"""
    conn = sqlite3.connect(memory_store.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT DISTINCT format_type FROM metadata WHERE conversation_id = ?",
        (conversation_id,)
    )
    formats = [row['format_type'] for row in cursor.fetchall()]
    conn.close()
    
    return formats

def merge_results(memory_store, conversation_id: str) -> Optional[Dict[str, Any]]:
    """Merge results from multiple agents for related inputs"""
    formats = find_related_inputs(memory_store, conversation_id)
    
    if len(formats) > 1:
        merged_data = {"formats": formats, "merged": True}
        
        for agent_name in ["json_agent", "email_agent", "pdf_agent"]:
            extraction = memory_store.get_latest_extraction(conversation_id, agent_name)
            if extraction:
                merged_data[f"{agent_name}_data"] = extraction["data"]
        
        result = {
            "format_type": "merged",
            "intent": "composite",
            "data": merged_data
        }
        memory_store.store_result(conversation_id, result)
        
        return merged_data
    
    return None

def simplify_conversation_history(history_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simplify a complex conversation history into a standardized format.
    """
    conversation_id = history_data.get("conversation_id", "")
    raw_history = history_data.get("history", [])
    
    raw_history.sort(key=lambda x: x.get("timestamp", ""))
    
    simplified_events = []
    pending_metadata = {}
    
    for item in raw_history:
        if not item.get("data"):
            continue
        
        event = {
            "id": item.get("id", ""),
            "source": item.get("agent", item.get("source", "")),
            "format": item.get("format_type", item.get("format", "")),
            "intent": item.get("intent", ""),
            "timestamp": item.get("timestamp", ""),
            "data": {}
        }
        
        # Extract data - avoid nested data.data structures
        data = item.get("data", {})
        while isinstance(data, dict) and "data" in data and isinstance(data["data"], dict) and len(data) == 1:
            data = data["data"]
        event["data"] = data
        
        # Check if this is just metadata with no meaningful content
        is_metadata_only = (
            item.get("activity_type") == "metadata" and 
            not event["format"] and 
            not event["intent"]
        )
        
        if is_metadata_only:
            # Store as pending metadata to merge with next meaningful event
            for key, value in event.items():
                if value and key not in pending_metadata:
                    pending_metadata[key] = value
        else:
            # Merge any pending metadata into this event
            for key, value in pending_metadata.items():
                if not event.get(key) and key != "data":
                    event[key] = value
                    
            simplified_events.append(event)
            pending_metadata = {}
    
    return {
        "conversation_id": conversation_id,
        "events": simplified_events
    }

# API Endpoints
@app.post("/process")
async def process_any(
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    conversation_id: Optional[str] = Form(None)
):
    """
    Single unified endpoint to process any input type.
    The classifier will determine the format and route to the appropriate agent.
    """
    try:
        input_content = None
        
        if not conversation_id:
            conversation_id = memory_store.generate_conversation_id()
        
        if file:
            input_content = await file.read()
            file_metadata = {
                "conversation_id": conversation_id,
                "source": "file_upload",
                "file_name": file.filename
            }
            memory_store.store_metadata(file_metadata)
            
        elif content:
            input_content = content
            try:
                input_content = json.loads(content)
                json_metadata = {
                    "conversation_id": conversation_id,
                    "source": "json_input",
                    "format_type": "json"
                }
                memory_store.store_metadata(json_metadata)
            except json.JSONDecodeError:
                text_metadata = {
                    "conversation_id": conversation_id,
                    "source": "text_input"
                }
                memory_store.store_metadata(text_metadata)
        else:
            raise HTTPException(status_code=400, detail="No content or file provided")
        
        # Classification and routing
        classification = classifier.classify_format_intent(input_content)
        
        format_intent_metadata = {
            "conversation_id": conversation_id,
            "source": "classifier",
            "format_type": classification["format"],
            "intent": classification["intent"]
        }
        memory_store.store_metadata(format_intent_metadata)
            
        result = classifier.route_to_agent(input_content, conversation_id)
        
        result["format"] = classification["format"]
        result["intent"] = classification["intent"]
        
        # Check for related inputs that might need to be merged
        formats = memory_store.find_related_inputs(conversation_id)
        if len(formats) > 1:
            merged_result = memory_store.merge_results(conversation_id)
            if merged_result:
                result["merged_data"] = merged_result
                
        result["conversation_id"] = conversation_id
                
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{conversation_id}/simplified")
async def get_simplified_conversation_history(conversation_id: str):
    """Get a simplified version of the conversation history."""
    try:
        history = memory_store.get_conversation_history(conversation_id)
        history_data = {
            "conversation_id": conversation_id,
            "history": history
        }
        simplified = simplify_conversation_history(history_data)
        return simplified
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/history/{conversation_id}")
async def get_conversation_history(conversation_id: str):
    """Get the full history for a conversation."""
    try:
        history = memory_store.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result/{conversation_id}")
async def get_conversation_result(conversation_id: str):
    """Get the final result for a conversation."""
    try:
        result = memory_store.get_result(conversation_id)
        if not result:
            raise HTTPException(status_code=404, detail="Result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/pdf")
async def process_pdf(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None)
):
    """Process a PDF file and extract information."""
    try:
        content = await file.read()
        
        _, ext = os.path.splitext(file.filename)
        if ext.lower() != '.pdf':
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only PDF files are supported."
            )
        
        result = classifier.route_to_agent(content, conversation_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("api.endpoints:app", host="0.0.0.0", port=8000, reload=True)