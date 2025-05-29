import json
import re
from typing import Dict, Any, Optional, Union
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.json_agent import JSONAgent
from agents.email_agent import EmailParserAgent
from agents.pdf_agents import PDFAgent

class ClassifierAgent(BaseAgent):
    """
    Classifier Agent that determines the type and intent of input data
    and routes it to the appropriate specialized agent.
    """
    
    def __init__(self, memory_store=None):
        super().__init__(name="Classifier Agent")
        self.memory_store = memory_store
        
        # Initialize specialized agents
        self.json_agent = JSONAgent()
        self.email_agent = EmailParserAgent()
        self.pdf_agent = PDFAgent()
    
    def process(self, data: Any) -> Dict[str, Any]:
        return self.classify(data)
    
    def classify(self, data: Any) -> Dict[str, Any]:
        format_type = self._determine_format(data)
        intent = self._determine_intent(data, format_type)
        
        return {
            "format": format_type,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }
    
    def route_to_agent(self, data: Any, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        # Generate conversation ID if not provided and memory store exists
        if not conversation_id and self.memory_store:
            conversation_id = self.memory_store.generate_conversation_id()
        
        # Classify the input
        classification = self.classify(data)
        format_type = classification["format"]
        
        # Store metadata in memory if memory store exists
        if self.memory_store:
            metadata = {
                "conversation_id": conversation_id,
                "source": "api",
                "format_type": format_type,
                "intent": classification["intent"],
                "timestamp": datetime.now().isoformat()
            }
            self.memory_store.store_metadata(metadata)
        
        # Process data based on format type
        result = {}
        
        if format_type == "JSON":
            processed_data = self.json_agent.process(data)
            result = {
                "format": "JSON",
                "processed_data": processed_data,
                "conversation_id": conversation_id
            }
            
            if self.memory_store:
                self.memory_store.store_extraction(conversation_id, "json_agent", processed_data)
                
        elif format_type == "Email":
            processed_data = self.email_agent.parse_email(data)
            result = {
                "format": "Email",
                "processed_data": processed_data,
                "conversation_id": conversation_id
            }
            
            if self.memory_store:
                self.memory_store.store_extraction(conversation_id, "email_agent", processed_data)
                
        elif format_type == "PDF":
            processed_data = self.pdf_agent.process(data)
            result = {
                "format": "PDF",
                "processed_data": processed_data,
                "conversation_id": conversation_id
            }
            
            if self.memory_store:
                self.memory_store.store_extraction(conversation_id, "pdf_agent", processed_data)
                
        else:
            result = {"error": "Unsupported format", "format": format_type}
        
        # Store final result in memory
        if self.memory_store and "error" not in result:
            self.memory_store.store_result(conversation_id, result)
        
        return result
    
    def _determine_format(self, data: Any) -> str:
        # Check if data is bytes (potentially PDF)
        if isinstance(data, bytes):
            if data[:4] == b'%PDF':
                return "PDF"
            return "Unknown"
        
        # Check if data is a dictionary (JSON)
        if isinstance(data, dict):
            return "JSON"
        
        # Check if data is a string
        if isinstance(data, str):
            try:
                json.loads(data)
                return "JSON"
            except:
                pass
            
            if "From:" in data or "Subject:" in data or "@" in data:
                return "Email"
        
        return "Unknown"
    
    def _determine_intent(self, data: Any, format_type: str) -> str:
        if format_type == "JSON":
            if isinstance(data, dict):
                json_data = data
            else:
                try:
                    json_data = json.loads(data)
                except:
                    return "Unknown"
                    
            if any(key in str(json_data).lower() for key in ["invoice", "bill", "payment"]):
                return "Invoice"
            elif any(key in str(json_data).lower() for key in ["quote", "rfq", "request"]):
                return "RFQ"
            elif any(key in str(json_data).lower() for key in ["complaint", "issue"]):
                return "Complaint"
        
        elif format_type == "Email":
            email_text = data.lower() if isinstance(data, str) else ""
            
            if "invoice" in email_text or "payment" in email_text:
                return "Invoice"
            elif "quote" in email_text or "rfq" in email_text:
                return "RFQ"
            elif "complaint" in email_text or "issue" in email_text:
                return "Complaint"
        
        elif format_type == "PDF":
            return "Document"
        
        return "General"
    
    def classify_format_intent(self, data: Any) -> Dict[str, str]:
        # Get raw format type
        raw_format = self._determine_format(data)
        
        # Map to expected format values
        format_mapping = {
            "JSON": "JSON",
            "Email": "Email", 
            "PDF": "PDF",
            "Unknown": "Other"
        }

        # Get raw intent
        raw_intent = self._determine_intent(data, raw_format)

        # Map to expected intent values
        intent_mapping = {
            "Invoice": "Invoice",
            "RFQ": "RFQ", 
            "Complaint": "Complaint",
            "Document": "Regulation",
            "General": "Other",
            "Unknown": "Other"
        }
        
        format_type = format_mapping.get(raw_format, "Other")
        intent = intent_mapping.get(raw_intent, "Other")
        
        return {
            "format": format_type,
            "intent": intent
        }