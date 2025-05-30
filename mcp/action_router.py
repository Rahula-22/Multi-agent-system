import json
import uuid
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class ActionRouter:
    """
    Action Router component that triggers follow-up actions based on agent outputs.
    Supports action routing based on content type, intent, and data patterns.
    Simulates REST API calls to external systems.
    """
    
    def __init__(self, memory_store=None, simulate=True):
        self.memory_store = memory_store
        self.simulate = simulate
        self.api_endpoints = {
            "crm": "https://api.example.com/crm",
            "ticketing": "https://api.example.com/tickets",
            "compliance": "https://api.example.com/compliance",
            "risk_alert": "https://api.example.com/risk_alert",
            "notification": "https://api.example.com/notify",
            "archive": "https://api.example.com/archive"
        }
    
    def route_action(self, conversation_id: str, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route an action based on processed data from agents.
        
        Args:
            conversation_id: The ID of the conversation
            processed_data: The processed data from an agent
            
        Returns:
            Dictionary with action result
        """
        format_type = processed_data.get("format", "")
        intent = processed_data.get("intent", "")
        
        # Determine action based on format and intent
        action = self._determine_action(format_type, intent, processed_data)
        
        # Execute the determined action
        result = self._execute_action(action, conversation_id, processed_data)
        
        # Log the action in memory store if available
        if self.memory_store:
            self.memory_store.store_action(
                conversation_id=conversation_id,
                chain_id=f"router_{format_type}_{intent}",
                action_id=action["type"],
                status="completed",
                result={
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        return {
            "action_type": action["type"],
            "action_target": action["target"],
            "result": result,
            "conversation_id": conversation_id
        }
    
    def _determine_action(self, format_type: str, intent: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine what action to take based on format type, intent, and data content.
        
        Returns:
            Dictionary with action details
        """
        # Handle PDF documents
        if format_type == "PDF":
            if intent == "Regulation":
                return {
                    "type": "flag_compliance_risk",
                    "target": "compliance",
                    "priority": "high",
                    "description": "Regulatory document requires compliance review"
                }
            elif "flags" in data and any(flag["type"] == "regulatory_content" for flag in data.get("flags", [])):
                return {
                    "type": "flag_compliance_risk",
                    "target": "compliance",
                    "priority": "high",
                    "description": "Document contains regulatory content"
                }
            elif "invoice_data" in data and self._check_high_value(data.get("invoice_data", {})):
                return {
                    "type": "create_payment_review",
                    "target": "ticketing",
                    "priority": "medium",
                    "description": "High-value invoice requires approval"
                }
        
        # Handle Email format
        elif format_type == "Email":
            if intent == "Complaint":
                return {
                    "type": "escalate_issue",
                    "target": "crm",
                    "priority": "high",
                    "description": "Customer complaint requires attention",
                    "endpoint": "/crm/escalate"
                }
            
            # Check email urgency and tone
            if "urgency" in data and data["urgency"] == "High":
                return {
                    "type": "escalate_issue",
                    "target": "crm",
                    "priority": "high",
                    "description": f"Urgent email: {data.get('subject', 'No subject')}",
                    "endpoint": "/crm/escalate"
                }
            
            if "tone" in data and data["tone"] in ["escalation", "threatening"]:
                return {
                    "type": "escalate_issue",
                    "target": "crm",
                    "priority": "high",
                    "description": f"Customer escalation: {data.get('subject', 'No subject')}",
                    "endpoint": "/crm/escalate"
                }

            # For other emails
            return {
                "type": "create_ticket",
                "target": "ticketing",
                "priority": "medium" if data.get("urgency") == "Medium" else "low",
                "description": f"Email follow-up: {data.get('subject', 'No subject')}"
            }
        
        # Handle JSON data
        elif format_type == "JSON":
            if intent == "Fraud Risk":
                return {
                    "type": "flag_risk_alert",
                    "target": "risk_alert",
                    "priority": "critical",
                    "description": "Potential fraud detected in transaction"
                }
            
            # Check for anomalies in JSON data
            if "anomalies" in data and len(data["anomalies"]) > 0:
                return {
                    "type": "flag_data_issue",
                    "target": "ticketing",
                    "priority": "medium",
                    "description": f"Data anomalies detected: {len(data['anomalies'])} issues found"
                }
            
            # Check for high value orders
            if "processed_data" in data and "flowbit_data" in data["processed_data"]:
                flowbit_data = data["processed_data"]["flowbit_data"]
                if "total_amount" in flowbit_data and self._check_high_value(flowbit_data):
                    return {
                        "type": "create_payment_review",
                        "target": "crm",
                        "priority": "medium",
                        "description": f"High-value order: {flowbit_data.get('order_id', 'Unknown ID')}"
                    }
        
        # Default action for anything not specifically handled
        return {
            "type": "archive_data",
            "target": "archive",
            "priority": "low",
            "description": f"Archiving {format_type} data with {intent} intent"
        }
    
    def _execute_action(self, action: Dict[str, Any], conversation_id: str, 
                       data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the specified action by making an API call or simulation.
        
        Args:
            action: The action to execute
            conversation_id: The conversation ID
            data: The data to send with the action
            
        Returns:
            Dictionary with action result
        """
        action_type = action["type"]
        target = action["target"]
        priority = action["priority"]
        description = action["description"]
        
        # Prepare the payload for the API call
        payload = {
            "action": action_type,
            "priority": priority,
            "description": description,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "format": data.get("format", "Unknown"),
                "intent": data.get("intent", "Unknown"),
                "source": "action_router"
            }
        }
        
        # Add relevant data from the processed data
        if "processed_data" in data:
            payload["data"] = data["processed_data"]
        elif "extracted_data" in data:
            payload["data"] = data["extracted_data"]
        else:
            # Filter out large fields to avoid bloating the payload
            filtered_data = {k: v for k, v in data.items() 
                           if k not in ["text_snippet", "body_snippet"] and not isinstance(v, bytes)}
            payload["data"] = filtered_data
        
        # If simulating, return a mock response
        if self.simulate:
            return self._simulate_api_response(action_type, target, payload)
            
        # Otherwise make the actual API call
        try:
            endpoint = self.api_endpoints.get(target, "https://api.example.com/default")
            headers = {"Content-Type": "application/json", "X-Api-Key": "simulation-key"}
            
            response = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response": response.json() if response.text else {},
                    "message": "Action executed successfully"
                }
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "message": f"API error: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing action: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _simulate_api_response(self, action_type: str, target: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an API response for testing without making actual API calls.
        
        Args:
            action_type: Type of action being executed
            target: Target system
            payload: Action payload
            
        Returns:
            Simulated API response
        """
        # Add a small delay to simulate network latency
        time.sleep(0.2)
        
        # Generate a unique ID for the simulated response
        action_id = str(uuid.uuid4())[:8].upper()
        
        responses = {
            "create_ticket": {
                "success": True,
                "ticket_id": f"TICKET-{action_id}",
                "status": "created",
                "assigned_to": "Support Team",
                "priority": payload.get("priority", "medium"),
                "url": f"https://example.com/tickets/TICKET-{action_id}"
            },
            "escalate_issue": {
                "success": True,
                "case_id": f"CASE-{action_id}",
                "status": "escalated",
                "assigned_to": "Customer Relations Manager",
                "priority": "high",
                "sla_hours": 4,
                "url": f"https://example.com/crm/cases/CASE-{action_id}"
            },
            "flag_compliance_risk": {
                "success": True,
                "risk_id": f"COMP-{action_id}",
                "status": "flagged",
                "assigned_to": "Compliance Team",
                "review_deadline": (datetime.now() + 
                                  datetime.timedelta(days=3)).isoformat(),
                "url": f"https://example.com/compliance/COMP-{action_id}"
            },
            "flag_risk_alert": {
                "success": True,
                "alert_id": f"RISK-{action_id}",
                "status": "under_review",
                "risk_score": 0.85,
                "assigned_to": "Fraud Prevention Team",
                "url": f"https://example.com/risk/alerts/RISK-{action_id}"
            },
            "create_payment_review": {
                "success": True,
                "review_id": f"PAY-{action_id}",
                "status": "pending_approval",
                "amount": self._extract_amount(payload),
                "approver": "Finance Manager",
                "url": f"https://example.com/finance/approvals/PAY-{action_id}"
            },
            "flag_data_issue": {
                "success": True,
                "issue_id": f"DATA-{action_id}",
                "status": "open",
                "assigned_to": "Data Quality Team",
                "url": f"https://example.com/data/issues/DATA-{action_id}"
            },
            "archive_data": {
                "success": True,
                "archive_id": f"ARCH-{action_id}",
                "status": "archived",
                "retention_period": "90 days",
                "url": f"https://example.com/archive/ARCH-{action_id}"
            }
        }
        
        # Get the appropriate response template or use a generic one
        response_template = responses.get(action_type, {
            "success": True,
            "action_id": f"GEN-{action_id}",
            "status": "processed",
            "message": "Action processed successfully"
        })
        
        # Add standard fields to all responses
        response = {
            **response_template,
            "timestamp": datetime.now().isoformat(),
            "target_system": target,
            "conversation_id": payload.get("conversation_id", ""),
            "simulation": True
        }
        
        return response
    
    def _check_high_value(self, data: Dict[str, Any]) -> bool:
        """Check if the data represents a high-value transaction."""
        amount = self._extract_amount(data)
        
        # Consider anything over $10,000 as high value
        if amount > 10000:
            return True
            
        return False
    
    def _extract_amount(self, data: Dict[str, Any]) -> float:
        """Extract numerical amount from different data structures."""
        # Try different common field names for monetary amounts
        for field in ["total_amount", "amount", "total", "invoice_total", "payment_amount"]:
            if field in data:
                try:
                    # Handle string values with currency symbols
                    if isinstance(data[field], str):
                        # Remove currency symbols and commas
                        cleaned = data[field].replace('$', '').replace('€', '').replace('£', '').replace(',', '')
                        return float(cleaned)
                    return float(data[field])
                except (ValueError, TypeError):
                    continue
        
        # Look in nested structures
        if "data" in data:
            return self._extract_amount(data["data"])
        
        if "flowbit_data" in data:
            return self._extract_amount(data["flowbit_data"])
            
        if "invoice_data" in data:
            return self._extract_amount(data["invoice_data"])
        
        # If we can't find a relevant amount, return 0
        return 0.0

    def batch_process(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process a batch of agent results and route appropriate actions.
        
        Args:
            results: List of agent processing results
            
        Returns:
            List of action results
        """
        action_results = []
        
        for result in results:
            conversation_id = result.get("conversation_id", str(uuid.uuid4()))
            action_result = self.route_action(conversation_id, result)
            action_results.append(action_result)
            
        return action_results