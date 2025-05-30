import requests
import time
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

class APIClient:
    """
    Simulated API client for external service integration.
    Can be used in simulation mode (no actual API calls) or real API mode.
    """
    
    def __init__(self, base_url: str = None, api_key: str = None, simulate: bool = True):
        self.base_url = base_url or "https://api.example.com"
        self.api_key = api_key or "simulation-key"
        self.simulate = simulate
        self.endpoints = {
            "crm": "/crm",
            "ticketing": "/tickets",
            "compliance": "/compliance",
            "risk_alert": "/risk_alert",
            "notification": "/notify",
            "archive": "/archive"
        }
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a POST request to the specified endpoint.
        
        Args:
            endpoint: Endpoint name (e.g., "crm", "ticketing")
            data: Data to send with the request
            
        Returns:
            Response data
        """
        if self.simulate:
            return self._simulate_response(endpoint, data)
        
        try:
            url = f"{self.base_url}{self.endpoints.get(endpoint, '/api')}"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "User-Agent": "MultiAgentSystem/1.0"
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            return {
                "success": response.status_code in [200, 201, 202],
                "status_code": response.status_code,
                "data": response.json() if response.text else {},
                "headers": dict(response.headers),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }
    
    def _simulate_response(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate an API response without making a real API call.
        
        Args:
            endpoint: The endpoint being called
            data: The data being sent
            
        Returns:
            Simulated response
        """
        # Add realistic delay
        time.sleep(0.3)
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Build custom response based on endpoint
        if endpoint == "crm":
            return {
                "success": True,
                "status_code": 201,
                "data": {
                    "case_id": f"CRM-{request_id[:8]}",
                    "status": "created",
                    "priority": data.get("priority", "medium"),
                    "assigned_to": "Customer Relations",
                    "estimated_response_time": "4 hours"
                },
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }
            
        elif endpoint == "ticketing":
            return {
                "success": True,
                "status_code": 201,
                "data": {
                    "ticket_id": f"TKT-{request_id[:8]}",
                    "status": "open",
                    "priority": data.get("priority", "medium"),
                    "queue": "General Support",
                    "estimated_response_time": "24 hours"
                },
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }
            
        elif endpoint == "compliance":
            return {
                "success": True,
                "status_code": 201,
                "data": {
                    "alert_id": f"COMP-{request_id[:8]}",
                    "status": "under_review",
                    "priority": data.get("priority", "high"),
                    "compliance_officer": "Regulatory Team",
                    "review_deadline": "72 hours"
                },
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }
            
        elif endpoint == "risk_alert":
            return {
                "success": True,
                "status_code": 201,
                "data": {
                    "alert_id": f"RISK-{request_id[:8]}",
                    "status": "triggered",
                    "risk_level": data.get("priority", "high"),
                    "notification_sent": True,
                    "responders": ["Fraud Department", "Security Team"]
                },
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }
            
        else:
            # Generic response for other endpoints
            return {
                "success": True,
                "status_code": 200,
                "data": {
                    "id": f"GEN-{request_id[:8]}",
                    "status": "processed",
                    "message": f"Request to {endpoint} processed successfully"
                },
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "simulated": True
            }