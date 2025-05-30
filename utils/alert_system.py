from typing import Dict, Any, List, Optional
import datetime
import json

class AlertSystem:
    """Alert system that triggers notifications based on content patterns and thresholds."""
    
    def __init__(self):
        self.alert_rules = {
            "urgent_email": {
                "condition": lambda data: data.get("format") == "Email" and 
                             data.get("processed_data", {}).get("urgency") == "High",
                "message": "Urgent email received that requires immediate attention",
                "level": "high"
            },
            "invoice_alert": {
                "condition": lambda data: data.get("format") == "JSON" and 
                             data.get("intent") == "Invoice" and
                             data.get("processed_data", {}).get("flowbit_data", {}).get("total_amount", 0) > 1000,
                "message": "High-value invoice detected",
                "level": "medium"
            },
            "pdf_regulation": {
                "condition": lambda data: data.get("format") == "PDF" and 
                             data.get("intent") == "Regulation",
                "message": "Regulatory document received that requires compliance review",
                "level": "medium"
            },
            "multiple_anomalies": {
                "condition": lambda data: data.get("format") == "JSON" and 
                             len(data.get("processed_data", {}).get("anomalies", [])) >= 3,
                "message": "Multiple anomalies detected in JSON data",
                "level": "high"
            }
        }
        self.alerts_history = []
        

    def check_alerts(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check if the processed data triggers any alerts.
        
        Args:
            data: The processed data to check against alert rules
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for rule_id, rule in self.alert_rules.items():
            try:
                if rule["condition"](data):
                    alert = {
                        "id": rule_id,
                        "message": rule["message"],
                        "level": rule["level"],
                        "timestamp": datetime.datetime.now().isoformat(),
                        "data": {
                            "format": data.get("format", "Unknown"),
                            "intent": data.get("intent", "Unknown")
                        }
                    }
                    triggered_alerts.append(alert)
                    self.alerts_history.append(alert)
            except Exception as e:
                print(f"Error checking rule {rule_id}: {str(e)}")
        
        return triggered_alerts
    
    def add_custom_rule(self, rule_id: str, condition, message: str, level: str = "medium") -> bool:
        """
        Add a custom alert rule.
        
        Args:
            rule_id: Unique identifier for the rule
            condition: Function that takes data and returns True if alert should be triggered
            message: Alert message
            level: Alert level (low, medium, high)
            
        Returns:
            Success indicator
        """
        if rule_id in self.alert_rules:
            return False
        
        self.alert_rules[rule_id] = {
            "condition": condition,
            "message": message,
            "level": level
        }
        return True
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent alerts.
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        return self.alerts_history[-limit:]
    
    def get_alerts_for_conversation(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get all alerts for a specific conversation.
        
        Args:
            conversation_id: Conversation ID to filter by
            
        Returns:
            List of alerts for the conversation
        """
        return [
            alert for alert in self.alerts_history 
            if alert.get("data_reference", {}).get("conversation_id") == conversation_id
        ]