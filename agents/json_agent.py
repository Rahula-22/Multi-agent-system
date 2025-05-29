from agents.base_agent import BaseAgent
from utils.validators import validate_json_structure
from typing import Dict, Any, List, Tuple
import datetime
import re

class JSONAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="JSON Agent")
        self.required_fields = ["order_id", "customer", "items", "total_amount", "currency", "delivery_date"]
        self.valid_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
    
    def process(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        flowbit_data, anomalies = self.map_to_flowbit_schema(json_data)
        
        return {
            "flowbit_data": flowbit_data,
            "anomalies": anomalies
        }
    
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
        elif "order_number" in json_data:
            flowbit_data["order_id"] = str(json_data["order_number"])
        else:
            anomalies.append("Missing required field: order_id")
        
        # Map customer
        if "customer" in json_data:
            flowbit_data["customer"] = str(json_data["customer"])
        elif "customer_name" in json_data:
            flowbit_data["customer"] = str(json_data["customer_name"])
        elif "name" in json_data:
            flowbit_data["customer"] = str(json_data["name"])
        else:
            anomalies.append("Missing required field: customer")
        
        # Map items
        items_found = False
        for items_field in ["items", "products", "line_items", "order_items"]:
            if items_field in json_data and isinstance(json_data[items_field], list):
                items_found = True
                for item in json_data[items_field]:
                    flowbit_item = {"sku": "", "qty": 0}
                    
                    # Extract SKU
                    if "sku" in item:
                        flowbit_item["sku"] = str(item["sku"])
                    elif "id" in item:
                        flowbit_item["sku"] = str(item["id"])
                    elif "product_id" in item:
                        flowbit_item["sku"] = str(item["product_id"])
                    else:
                        anomalies.append(f"Missing SKU in item: {str(item)}")
                    
                    # Extract quantity
                    if "qty" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["qty"])
                    elif "quantity" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["quantity"])
                    elif "amount" in item:
                        flowbit_item["qty"] = self._convert_to_int(item["amount"])
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
        elif "total" in json_data:
            flowbit_data["total_amount"] = self._convert_to_number(json_data["total"])
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
            if currency not in self.valid_currencies:
                anomalies.append(f"Unknown currency: {currency}")
        else:
            anomalies.append("Missing required field: currency")
        
        # Map delivery_date
        if "delivery_date" in json_data:
            flowbit_data["delivery_date"] = self._format_date(json_data["delivery_date"])
        elif "date" in json_data:
            flowbit_data["delivery_date"] = self._format_date(json_data["date"])
        elif "delivery" in json_data and isinstance(json_data["delivery"], dict) and "date" in json_data["delivery"]:
            flowbit_data["delivery_date"] = self._format_date(json_data["delivery"]["date"])
        else:
            anomalies.append("Missing required field: delivery_date")
        
        return flowbit_data, anomalies
    
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