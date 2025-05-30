from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
import uvicorn

from api.endpoints import app as api_app
from memory.memory_store import MemoryStore
from utils.alert_system import AlertSystem
from utils.summary_generator import SummaryGenerator
from mcp.action_chain import ActionChain, register_default_actions
from mcp.action_router import ActionRouter
from utils.api_client import APIClient

app = FastAPI(title="Multi-Agent AI System Dashboard")

# Mount the API app as a sub-application
app.mount("/api", api_app)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Initialize components
memory_store = MemoryStore()
alert_system = AlertSystem()
summary_generator = SummaryGenerator()
action_chain = ActionChain()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request}
    )

@app.on_event("startup")
async def startup_event():
    # Register default actions
    register_default_actions(action_chain)
    
    global action_router
    action_router = ActionRouter(memory_store=memory_store, simulate=True)
    
    # Initialize API client
    global api_client
    api_client = APIClient(simulate=True)
    
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
    
    print("Multi-Agent AI System initialized with alert system, summarization, and action chaining")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)