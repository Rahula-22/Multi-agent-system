import json
import re
from typing import Dict, Any, Optional, Union, List
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
        
        # Few-shot examples for format classification
        self.format_examples = {
            "JSON": [
                {"order": {"id": "123", "items": []}},
                '{"customer": {"name": "John", "email": "john@example.com"}}'
            ],
            "Email": [
                "From: john@example.com\nTo: service@company.com\nSubject: Question about order",
                "Subject: Invoice #1234\nHello,\nPlease find attached invoice."
            ],
            "PDF": [
                b'%PDF-1.4\n',  # PDF header signature
                b'%PDF'  # Simplified PDF signature
            ]
        }
        
        # Few-shot examples for intent classification with schema patterns
        self.intent_schemas = {
            "Invoice": {
                "keywords": ["invoice", "payment", "bill", "receipt", "transaction", "paid", "amount due"],
                "json_fields": ["invoice_number", "amount", "total", "payment", "due_date"],
                "examples": [
                    "Please find attached invoice #1234 for your recent purchase.",
                    {"invoice_id": "INV-1234", "amount": 500, "currency": "USD"}
                ]
            },
            "RFQ": {
                "keywords": ["quote", "rfq", "request for quote", "quotation", "estimate", "pricing"],
                "json_fields": ["quote_number", "request_id", "estimate"],
                "examples": [
                    "I would like to request a quote for 100 units of your product.",
                    {"request_type": "quote", "product_id": "ABC123", "quantity": 50}
                ]
            },
            "Complaint": {
                "keywords": ["complaint", "issue", "problem", "defect", "unsatisfied", "disappointed", "refund"],
                "json_fields": ["complaint_id", "issue", "problem"],
                "examples": [
                    "I am writing to express my dissatisfaction with your product.",
                    {"issue_type": "complaint", "product": "XYZ", "description": "Item arrived damaged"}
                ]
            },
            "Regulation": {
                "keywords": ["regulation", "compliance", "law", "legal", "requirement", "guideline", "policy"],
                "json_fields": ["regulation_id", "compliance", "policy_number"],
                "examples": [
                    "This document outlines the regulatory requirements for financial reporting.",
                    {"document_type": "regulation", "authority": "SEC", "regulation_code": "10b-5"}
                ]
            },
            "Fraud Risk": {
                "keywords": ["suspicious", "fraud", "unusual", "unauthorized", "anomaly", "scam", "fake"],
                "json_fields": ["risk_score", "fraud_indicators", "suspicious_activity"],
                "examples": [
                    "We have detected suspicious activity on your account.",
                    {"transaction": {"risk_score": 0.85, "anomaly": true, "ip_mismatch": true}}
                ]
            }
        }
    
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
        """
        Determine the format of the input data using few-shot examples and schema matching.
        """
        # Check if data is bytes (potentially PDF)
        if isinstance(data, bytes):
            for example in self.format_examples["PDF"]:
                if data.startswith(example):
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
            
            # Check for Email indicators
            for example in self.format_examples["Email"]:
                # Extract key patterns from examples
                patterns = ["From:", "To:", "Subject:", "@"]
                if any(pattern in data for pattern in patterns):
                    return "Email"
        
        return "Unknown"
    
    def _determine_intent(self, data: Any, format_type: str) -> str:
        """
        Determine the intent of the input data using few-shot examples and schema matching.
        """
        # Convert data to text for keyword matching
        text_data = ""
        json_data = {}
        
        if format_type == "JSON":
            if isinstance(data, dict):
                json_data = data
                text_data = json.dumps(data).lower()
            else:
                try:
                    json_data = json.loads(data)
                    text_data = data.lower()
                except:
                    text_data = str(data).lower()
        elif isinstance(data, str):
            text_data = data.lower()
        elif isinstance(data, bytes):
            # For PDF, we might only have the header bytes at this stage
            # We'll use the format_type to help determine intent
            text_data = ""
        else:
            text_data = str(data).lower()
        
        # Calculate match scores for each intent
        intent_scores = {}
        
        for intent, schema in self.intent_schemas.items():
            score = 0
            
            # Keyword matching
            for keyword in schema["keywords"]:
                if keyword.lower() in text_data:
                    score += 1
            
            # JSON field matching
            if format_type == "JSON" and json_data:
                flat_json = self._flatten_json(json_data)
                for field in schema["json_fields"]:
                    if any(field.lower() in key.lower() for key in flat_json.keys()):
                        score += 2  # Higher weight for field matches
            
            # Special case for PDF format and Regulation intent
            if format_type == "PDF" and intent == "Regulation":
                score += 2  # Bias towards regulation for PDF documents
            
            # Special case for detecting Fraud Risk
            if intent == "Fraud Risk":
                # Check for fraud indicators in JSON data
                if format_type == "JSON" and json_data:
                    flat_json = self._flatten_json(json_data)
                    for key, value in flat_json.items():
                        # Look for risk scores above 0.7
                        if "risk" in key.lower() and isinstance(value, (int, float)) and value > 0.7:
                            score += 3
                        # Look for boolean flags that might indicate fraud
                        if any(indicator in key.lower() for indicator in ["suspicious", "fraud", "anomaly"]) and value:
                            score += 3
                
                # Check for fraud keywords in text with higher sensitivity
                for keyword in schema["keywords"]:
                    if keyword.lower() in text_data:
                        score += 2  # Higher weight for fraud-related keywords
            
            intent_scores[intent] = score
        
        # Select intent with highest score, or General if all scores are zero
        max_score = max(intent_scores.values()) if intent_scores else 0
        if max_score > 0:
            # If there's a tie, prioritize certain intents
            max_intents = [i for i, s in intent_scores.items() if s == max_score]
            if len(max_intents) > 1:
                for priority_intent in ["Fraud Risk", "Regulation", "Invoice"]:
                    if priority_intent in max_intents:
                        return priority_intent
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        # Default intent based on format if no matches found
        format_default_intents = {
            "PDF": "Regulation",
            "Email": "General",
            "JSON": "General"
        }
        return format_default_intents.get(format_type, "General")
    
    def _flatten_json(self, json_obj, parent_key='', delimiter='.'):
        """
        Flatten a nested JSON object into a single level dictionary.
        Used for better field matching against schemas.
        """
        items = {}
        for k, v in json_obj.items() if isinstance(json_obj, dict) else []:
            new_key = f"{parent_key}{delimiter}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.update(self._flatten_json(v, new_key, delimiter))
            elif isinstance(v, list):
                # For lists, we only check the first item if it's a dict
                if v and isinstance(v[0], dict):
                    items.update(self._flatten_json(v[0], new_key, delimiter))
                else:
                    items[new_key] = str(v)
            else:
                items[new_key] = v
                
        return items
    
    def classify_format_intent(self, data: Any) -> Dict[str, str]:
        """
        Classify both format and intent of the input data.
        
        Returns:
            Dictionary with format and intent keys
        """
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
            "Regulation": "Regulation",
            "Fraud Risk": "Fraud Risk",
            "General": "Other",
            "Unknown": "Other"
        }
        
        format_type = format_mapping.get(raw_format, "Other")
        intent = intent_mapping.get(raw_intent, "Other")
        
        return {
            "format": format_type,
            "intent": intent
        }