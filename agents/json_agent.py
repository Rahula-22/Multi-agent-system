from agents.base_agent import BaseAgent
from utils.validators import validate_json_structure
from typing import Dict, Any, List, Tuple, Optional
import datetime
import re
import json
import uuid

class JSONAgent(BaseAgent):
    """
    JSON Agent that processes webhook data, validates against required schema fields,
    and flags anomalies in the data structure.
    """
    
    def __init__(self, memory_store=None):
        super().__init__(name="JSON Agent")
        self.memory_store = memory_store
        self.required_fields = ["order_id", "customer", "items", "total_amount", "currency", "delivery_date"]
        self.valid_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
    
    def process(self, json_data: Dict[str, Any], conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process JSON webhook data, validate schema, and identify anomalies.
        
        Args:
            json_data: The JSON data to process
            conversation_id: Optional conversation ID for tracking
            
        Returns:
            Dictionary with processed data and anomalies
        """
        # Convert string to dict if needed
        if isinstance(json_data, str):
            try:
                json_data = json.loads(json_data)
            except json.JSONDecodeError:
                return {
                    "flowbit_data": {},
                    "anomalies": ["Invalid JSON format"],
                    "is_valid": False
                }
        
        # If not a dict, return error
        if not isinstance(json_data, dict):
            return {
                "flowbit_data": {},
                "anomalies": ["Input is not a valid JSON object"],
                "is_valid": False
            }
        
        # Process the JSON data
        flowbit_data, anomalies = self.map_to_flowbit_schema(json_data)
        
        # Log alert if anomalies are detected
        if anomalies and len(anomalies) > 0:
            self._log_anomaly_alert(flowbit_data, anomalies, conversation_id)
        
        result = {
            "flowbit_data": flowbit_data,
            "anomalies": anomalies,
            "is_valid": len(anomalies) == 0,
            "processed_at": datetime.datetime.now().isoformat()
        }
        
        return result
    
    def map_to_flowbit_schema(self, json_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Maps the input JSON to FlowBit schema and identifies anomalies"""
        flowbit_data = {
            "order_id": None,
            "customer": None,
            "items": [],
            "total_amount": None,
            "currency": None,
            "delivery_date": None
        }
        
        anomalies = []
        
        # Map order_id
        if "order_id" in json_data:
            flowbit_data["order_id"] = str(json_data["order_id"])
        elif "id" in json_data:
            flowbit_data["order_id"] = str(json_data["id"])
            anomalies.append("Field mapping: 'id' used instead of 'order_id'")
        elif "order_number" in json_data:
            flowbit_data["order_id"] = str(json_data["order_number"])
            anomalies.append("Field mapping: 'order_number' used instead of 'order_id'")
        else:
            anomalies.append("Missing required field: order_id")
        
        # Map customer
        if "customer" in json_data:
            flowbit_data["customer"] = str(json_data["customer"])
        elif "customer_name" in json_data:
            flowbit_data["customer"] = str(json_data["customer_name"])
            anomalies.append("Field mapping: 'customer_name' used instead of 'customer'")
        elif "name" in json_data:
            flowbit_data["customer"] = str(json_data["name"])
            anomalies.append("Field mapping: 'name' used instead of 'customer'")
        else:
            anomalies.append("Missing required field: customer")
        
        # Map items
        items_found = False
        for items_field in ["items", "products", "line_items", "order_items"]:
            if items_field in json_data and isinstance(json_data[items_field], list):
                items_found = True
                if items_field != "items":
                    anomalies.append(f"Field mapping: '{items_field}' used instead of 'items'")
                
                for item in json_data[items_field]:
                    flowbit_item = {"sku": "", "qty": 0}
                    
                    # Extract SKU
                    if "sku" in item:
                        flowbit_item["sku"] = str(item["sku"])
                    elif "id" in item:
                        flowbit_item["sku"] = str(item["id"])
                        anomalies.append(f"Item field mapping: 'id' used instead of 'sku'")
                    elif "product_id" in item:
                        flowbit_item["sku"] = str(item["product_id"])
                        anomalies.append(f"Item field mapping: 'product_id' used instead of 'sku'")
                    else:
                        anomalies.append(f"Missing SKU in item: {str(item)}")
                    
                    # Extract quantity
                    if "qty" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["qty"])
                    elif "quantity" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["quantity"])
                        anomalies.append(f"Item field mapping: 'quantity' used instead of 'qty'")
                    elif "amount" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["amount"])
                        anomalies.append(f"Item field mapping: 'amount' used instead of 'qty'")
                    else:
                        anomalies.append(f"Missing quantity in item: {str(item)}")
                    
                    flowbit_data["items"].append(flowbit_item)
                break
        
        if not items_found:
            anomalies.append("Missing required field: items")
        
        # Map total_amount
        if "total_amount" in json_data:
            flowbit_data["total_amount"] = self._convert_to_number(json_data["total_amount"])
        elif "amount" in json_data:
            flowbit_data["total_amount"] = self._convert_to_number(json_data["amount"])
            anomalies.append("Field mapping: 'amount' used instead of 'total_amount'")
        elif "total" in json_data:
            flowbit_data["total_amount"] = self._convert_to_number(json_data["total"])
            anomalies.append("Field mapping: 'total' used instead of 'total_amount'")
        else:
            anomalies.append("Missing required field: total_amount")
        
        # Map currency
        if "currency" in json_data:
            currency = str(json_data["currency"]).upper()
            flowbit_data["currency"] = currency
            if currency not in self.valid_currencies:
                anomalies.append(f"Unknown currency: {currency}")
        elif "currency_code" in json_data:
            currency = str(json_data["currency_code"]).upper()
            flowbit_data["currency"] = currency
            anomalies.append("Field mapping: 'currency_code' used instead of 'currency'")
            if currency not in self.valid_currencies:
                anomalies.append(f"Unknown currency: {currency}")
        else:
            anomalies.append("Missing required field: currency")
            flowbit_data["currency"] = "USD"  # Default currency
        
        # Map delivery_date
        if "delivery_date" in json_data:
            flowbit_data["delivery_date"] = self._format_date(json_data["delivery_date"])
        elif "date" in json_data:
            flowbit_data["delivery_date"] = self._format_date(json_data["date"])
            anomalies.append("Field mapping: 'date' used instead of 'delivery_date'")
        elif "delivery" in json_data and isinstance(json_data["delivery"], dict) and "date" in json_data["delivery"]:
            flowbit_data["delivery_date"] = self._format_date(json_data["delivery"]["date"])
            anomalies.append("Field mapping: 'delivery.date' used instead of 'delivery_date'")
        else:
            anomalies.append("Missing required field: delivery_date")
        
        # Check for type errors
        if flowbit_data["total_amount"] is not None:
            try:
                float(flowbit_data["total_amount"])
            except (ValueError, TypeError):
                anomalies.append("Type error: total_amount is not a valid number")
                flowbit_data["total_amount"] = 0.0
        
        # Check for suspicious values
        if flowbit_data["total_amount"] is not None and flowbit_data["total_amount"] < 0:
            anomalies.append("Suspicious value: negative total_amount")
        
        # Check for empty items array
        if len(flowbit_data["items"]) == 0 and items_found:
            anomalies.append("Suspicious value: empty items array")
        
        return flowbit_data, anomalies
    
    def _log_anomaly_alert(self, data: Dict[str, Any], anomalies: List[str], conversation_id: Optional[str] = None) -> None:
        """
        Log an alert about anomalies in the JSON data to memory store or API.
        
        Args:
            data: The processed data containing anomalies
            anomalies: List of detected anomalies
            conversation_id: Optional conversation ID for correlation
        """
        alert_id = str(uuid.uuid4())[:8]
        
        alert = {
            "alert_id": f"JSON-ANOMALY-{alert_id}",
            "timestamp": datetime.datetime.now().isoformat(),
            "severity": "medium" if len(anomalies) > 3 else "low",
            "source": "json_agent",
            "type": "schema_validation",
            "anomalies": anomalies,
            "data_preview": {
                "order_id": data.get("order_id"),
                "customer": data.get("customer"),
                "total_amount": data.get("total_amount"),
                "currency": data.get("currency"),
                "items_count": len(data.get("items", []))
            }
        }
        
        # Store in memory if available
        if self.memory_store and conversation_id:
            try:
                self.memory_store.store_alert(conversation_id, alert)
                print(f"Alert logged to memory: {alert['alert_id']}")
            except Exception as e:
                print(f"Failed to log alert to memory: {str(e)}")
        else:
            # If no memory store is available, just print to console
            print(f"JSON Anomaly Alert: {len(anomalies)} issues detected")
            for anomaly in anomalies:
                print(f"  - {anomaly}")
    
    def _convert_to_number(self, value: Any) -> float:
        """Convert a value to a number, handling various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            # Remove any currency symbols and commas
            cleaned_value = re.sub(r'[^\d.]', '', value)
            try:
                return float(cleaned_value)
            except ValueError:
                return 0.0
        return 0.0
    
    def _convert_to_int(self, value: Any) -> int:
        """Convert a value to an integer, handling various formats"""
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            return int(value)
        elif isinstance(value, str):
            try:
                return int(float(value))
            except ValueError:
                return 0
        return 0
    
    def _format_date(self, date_value: Any) -> str:
        """Format a date value to ISO YYYY-MM-DD format"""
        if isinstance(date_value, str):
            # Try various date formats
            date_formats = [
                "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y", 
                "%m-%d-%Y", "%d-%m-%Y", "%B %d, %Y", "%b %d, %Y"
            ]
            
            for date_format in date_formats:
                try:
                    parsed_date = datetime.datetime.strptime(date_value, date_format)
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    continue
            
            # If no format matched, check if it's already in ISO format
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_value):
                return date_value
            
            return date_value
        elif isinstance(date_value, (int, float)):
            # Assume it's a timestamp
            try:
                date = datetime.datetime.fromtimestamp(date_value)
                return date.strftime("%Y-%m-%d")
            except:
                return str(date_value)
        
        return str(date_value)