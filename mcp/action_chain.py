from typing import Dict, Any, List, Callable, Optional
import datetime
import importlib
import inspect

class ActionChain:
    """Manages chains of actions to be executed based on extracted data."""
    
    def __init__(self):
        self.registered_actions = {}
        self.action_chains = {}
        
    def register_action(self, action_id: str, action_func: Callable) -> bool:
        """
        Register an action function that can be chained.
        
        Args:
            action_id: Unique identifier for the action
            action_func: Function that performs the action
            
        Returns:
            Success indicator
        """
        if action_id in self.registered_actions:
            return False
        
        self.registered_actions[action_id] = action_func
        return True
    
    def define_chain(self, chain_id: str, conditions: List[Dict[str, Any]], 
                    actions: List[str]) -> bool:
        """
        Define a chain of actions to be triggered when conditions are met.
        
        Args:
            chain_id: Unique identifier for the chain
            conditions: List of condition dictionaries with {field, operator, value}
            actions: List of action_ids to execute in sequence
            
        Returns:
            Success indicator
        """
        if chain_id in self.action_chains:
            return False
            
        # Validate that all actions exist
        for action_id in actions:
            if action_id not in self.registered_actions:
                return False
        
        self.action_chains[chain_id] = {
            "conditions": conditions,
            "actions": actions,
            "created_at": datetime.datetime.now().isoformat()
        }
        return True
    
    def _check_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Check if a single condition is met"""
        field = condition.get("field", "")
        operator = condition.get("operator", "eq")
        value = condition.get("value")
        
        # Navigate nested fields using dot notation
        field_parts = field.split(".")
        current = data
        for part in field_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        actual_value = current
        
        # Apply the operator
        if operator == "eq":
            return actual_value == value
        elif operator == "neq":
            return actual_value != value
        elif operator == "gt":
            return actual_value > value
        elif operator == "lt":
            return actual_value < value
        elif operator == "contains":
            return value in actual_value if hasattr(actual_value, "__contains__") else False
        elif operator == "regex":
            import re
            return bool(re.search(value, str(actual_value)))
        
        return False
    
    def _check_all_conditions(self, conditions: List[Dict[str, Any]], 
                             data: Dict[str, Any]) -> bool:
        """Check if all conditions in a list are met"""
        return all(self._check_condition(condition, data) for condition in conditions)
    
    def process(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process data through all defined chains and execute matching actions.
        
        Args:
            data: Data to check against chain conditions
            
        Returns:
            List of action results
        """
        results = []
        
        for chain_id, chain in self.action_chains.items():
            if self._check_all_conditions(chain["conditions"], data):
                chain_results = []
                
                # Execute each action in the chain
                for action_id in chain["actions"]:
                    action_func = self.registered_actions.get(action_id)
                    if action_func:
                        try:
                            action_result = action_func(data)
                            chain_results.append({
                                "action_id": action_id,
                                "success": True,
                                "result": action_result
                            })
                        except Exception as e:
                            chain_results.append({
                                "action_id": action_id,
                                "success": False,
                                "error": str(e)
                            })
                
                results.append({
                    "chain_id": chain_id,
                    "triggered_at": datetime.datetime.now().isoformat(),
                    "actions": chain_results
                })
        
        return results

# Register common actions
def register_default_actions(action_chain):
    """Register a set of default actions with the action chain."""
    
    def send_email_notification(data):
        """Send an email notification based on processed data."""
        # In a real implementation, this would connect to an email service
        return {
            "notification_type": "email",
            "recipient": "admin@example.com",
            "subject": f"Alert: {data.get('format')} with {data.get('intent')} intent received",
            "status": "simulated"
        }
    
    def add_to_crm(data):
        """Add extracted information to a CRM system."""
        # In a real implementation, this would connect to a CRM API
        format_type = data.get("format")
        
        if format_type == "Email":
            email_data = data.get("processed_data", {})
            return {
                "crm_action": "contact_added",
                "contact": {
                    "name": email_data.get("sender_name"),
                    "email": email_data.get("sender_email"),
                    "status": "simulated"
                }
            }
        elif format_type == "JSON":
            json_data = data.get("processed_data", {}).get("flowbit_data", {})
            return {
                "crm_action": "order_added",
                "order": {
                    "id": json_data.get("order_id"),
                    "customer": json_data.get("customer"),
                    "amount": json_data.get("total_amount"),
                    "status": "simulated"
                }
            }
        
        return {"status": "not_applicable"}
    
    def flag_for_review(data):
        """Flag the content for manual review."""
        return {
            "flagged": True,
            "reason": "Triggered by action chain",
            "review_queue": "general",
            "priority": "medium",
            "status": "simulated"
        }
    
    def generate_compliance_report(data):
        """Generate a compliance report for regulatory content."""
        if data.get("intent") == "Regulation":
            return {
                "report_type": "compliance",
                "generated": True,
                "sections": ["Overview", "Regulatory Impact", "Required Actions"],
                "status": "simulated"
            }
        return {"status": "not_applicable"}
    
    # Register the actions
    action_chain.register_action("email_notification", send_email_notification)
    action_chain.register_action("add_to_crm", add_to_crm)
    action_chain.register_action("flag_for_review", flag_for_review)
    action_chain.register_action("compliance_report", generate_compliance_report)