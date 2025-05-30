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
from utils.alert_system import AlertSystem
from utils.summary_generator import SummaryGenerator
from mcp.action_chain import ActionChain, register_default_actions

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

class AlertRule(BaseModel):
    rule_id: str
    message: str
    level: str = "medium"
    condition_json: Dict[str, Any]

class ActionChainInput(BaseModel):
    chain_id: str
    conditions: List[Dict[str, Any]]
    actions: List[str]

# Initialize app and dependencies
app = FastAPI(title="Multi-Agent AI System")
memory_store = MemoryStore()
classifier = ClassifierAgent(memory_store)
alert_system = AlertSystem()
summary_generator = SummaryGenerator()
action_chain = ActionChain()
register_default_actions(action_chain)

# Define some default action chains
action_chain.define_chain(
    "urgent_email_chain",
    [{"field": "format", "operator": "eq", "value": "Email"}, 
     {"field": "processed_data.urgency", "operator": "eq", "value": "High"}],
    ["email_notification", "flag_for_review"]
)

action_chain.define_chain(
    "high_value_order_chain",
    [{"field": "format", "operator": "eq", "value": "JSON"}, 
     {"field": "processed_data.flowbit_data.total_amount", "operator": "gt", "value": 1000}],
    ["add_to_crm", "email_notification"]
)

action_chain.define_chain(
    "regulation_document_chain",
    [{"field": "format", "operator": "eq", "value": "PDF"}, 
     {"field": "intent", "operator": "eq", "value": "Regulation"}],
    ["compliance_report", "flag_for_review"]
)

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
        
        # Generate summary
        summary = summary_generator.generate_summary(result)
        result["summary"] = summary["summary"]
        
        # Check for alerts
        alerts = alert_system.check_alerts(result)
        if alerts:
            result["alerts"] = alerts
        
        # Run action chains
        action_results = action_chain.process(result)
        if action_results:
            result["actions"] = action_results
                
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
        
        # Add conversation summary
        if simplified.get("events"):
            summary = summary_generator.generate_conversation_summary(simplified["events"])
            simplified["summary"] = summary
        
        # Include alerts for this conversation
        alerts = alert_system.get_alerts_for_conversation(conversation_id)
        if alerts:
            simplified["alerts"] = alerts
            
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

@app.get("/summary/{conversation_id}")
async def get_conversation_summary(conversation_id: str):
    """Get a summary for the conversation."""
    try:
        history = memory_store.get_conversation_history(conversation_id)
        history_data = {
            "conversation_id": conversation_id,
            "history": history
        }
        simplified = simplify_conversation_history(history_data)
        
        if not simplified.get("events"):
            raise HTTPException(status_code=404, detail="No events found for conversation")
            
        summary = summary_generator.generate_conversation_summary(simplified["events"])
        
        return {
            "conversation_id": conversation_id,
            "summary": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
async def get_recent_alerts(limit: int = 10):
    """Get recent alerts across all conversations."""
    try:
        alerts = alert_system.get_recent_alerts(limit)
        return {"alerts": alerts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/rule")
async def add_alert_rule(rule: AlertRule):
    """Add a custom alert rule."""
    try:
        # Convert JSON condition to a lambda function
        condition_func = eval(f"lambda data: {rule.condition_json.get('code', 'False')}")
        
        success = alert_system.add_custom_rule(
            rule.rule_id,
            condition_func,
            rule.message,
            rule.level
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Rule ID '{rule.rule_id}' already exists")
            
        return {"success": True, "rule_id": rule.rule_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/actions/chain")
async def define_action_chain(chain_input: ActionChainInput):
    """Define a new action chain."""
    try:
        success = action_chain.define_chain(
            chain_input.chain_id,
            chain_input.conditions,
            chain_input.actions
        )
        
        if not success:
            raise HTTPException(
                status_code=400, 
                detail=f"Chain ID '{chain_input.chain_id}' already exists or invalid actions"
            )
            
        return {"success": True, "chain_id": chain_input.chain_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/process-email", response_model=Dict[str, Any])
    async def process_email(request: Request):
        """Process an uploaded email document and trigger appropriate actions"""
        data = await request.json()
        email_content = data.get("content", "")

        conversation_id = memory_store.generate_conversation_id()

        classifier_agent = ClassifierAgent(memory_store=memory_store)
        classification = classifier_agent.classify_format_intent(email_content)
        
        memory_store.add_classification(classification)

        metadata = {
            "conversation_id": conversation_id,
            "source": "api",
            "format_type": classification["format"],
            "intent": classification["intent"],
            "timestamp": memory_store.get_timestamp()
        }
        memory_store.store_metadata(metadata)
        
        email_agent = EmailParserAgent()
        email_result = email_agent.process(email_content)

        memory_store.store_extraction(conversation_id, "email_agent", email_result)

        combined_result = {
            "format": classification["format"],
            "intent": classification["intent"],
            "processed_data": email_result,
            "conversation_id": conversation_id
        }
        
        alerts = alert_system.check_alerts(combined_result)
        if alerts:
            for alert in alerts:
                memory_store.store_alert(conversation_id, alert)
        
        action_result = action_router.route_action(conversation_id, combined_result)
        
        chain_results = action_chain.evaluate(combined_result)
        
        summary = summary_generator.generate_summary(combined_result)

        final_result = {
            "format_type": classification["format"],
            "intent": classification["intent"],
            "email_data": email_result,
            "alerts": alerts,
            "action_taken": action_result,
            "chain_actions": chain_results,
            "summary": summary
        }
        memory_store.store_result(conversation_id, final_result)
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "classification": classification,
            "result": final_result
        }

if __name__ == "__main__":
    uvicorn.run("api.endpoints:app", host="0.0.0.0", port=8000, reload=True)