from typing import Dict, Any, List, Optional
import re
import json

class SummaryGenerator:
    """Generate concise summaries of processed content."""
    
    def __init__(self):
        pass
    
    def generate_email_summary(self, email_data: Dict[str, Any]) -> str:
        """Generate summary for email content."""
        if not email_data or not isinstance(email_data, dict):
            return "No valid email data available."
        
        sender = email_data.get("sender_name", "Unknown sender")
        sender_email = email_data.get("sender_email", "")
        intent = email_data.get("intent", "Unknown")
        urgency = email_data.get("urgency", "Low")
        
        summary = f"Email from {sender} ({sender_email})\n"
        summary += f"Intent: {intent}\n"
        summary += f"Urgency: {urgency}\n"
        
        return summary
    
    def generate_json_summary(self, json_data: Dict[str, Any]) -> str:
        """Generate summary for JSON content."""
        if not json_data or not isinstance(json_data, dict):
            return "No valid JSON data available."
        
        flowbit_data = json_data.get("flowbit_data", {})
        anomalies = json_data.get("anomalies", [])
        
        customer = flowbit_data.get("customer", "Unknown customer")
        order_id = flowbit_data.get("order_id", "Unknown order")
        item_count = len(flowbit_data.get("items", []))
        total_amount = flowbit_data.get("total_amount", 0)
        currency = flowbit_data.get("currency", "USD")
        anomaly_count = len(anomalies)
        
        summary = f"Order {order_id} from {customer}\n"
        summary += f"Contains {item_count} items for {total_amount} {currency}\n"
        
        if anomaly_count > 0:
            summary += f"Detected {anomaly_count} anomalies\n"
        
        return summary
    
    def generate_pdf_summary(self, pdf_data: Dict[str, Any]) -> str:
        """Generate summary for PDF content."""
        if not pdf_data or not isinstance(pdf_data, dict):
            return "No valid PDF data available."
        
        doc_type = pdf_data.get("document_type", "Unknown document")
        has_tables = pdf_data.get("has_tables", False)
        text_length = pdf_data.get("text_length", 0)
        snippet = pdf_data.get("text_snippet", "")[:100] + "..."
        
        summary = f"{doc_type.capitalize()} document ({text_length} chars)\n"
        if has_tables:
            summary += "Contains tabular data\n"
        summary += f"Preview: {snippet}\n"
        
        return summary
    
    def generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary based on the content format and processed data.
        
        Args:
            data: Processed data including format and content-specific details
            
        Returns:
            Dictionary containing summary information
        """
        format_type = data.get("format", "Unknown")
        intent = data.get("intent", "Unknown")
        processed_data = data.get("processed_data", {})
        
        summary_text = ""
        
        if format_type == "Email":
            summary_text = self.generate_email_summary(processed_data)
        elif format_type == "JSON":
            summary_text = self.generate_json_summary(processed_data)
        elif format_type == "PDF":
            summary_text = self.generate_pdf_summary(processed_data)
        else:
            summary_text = f"Unrecognized format: {format_type}"
        
        return {
            "format": format_type,
            "intent": intent,
            "summary": summary_text,
            "conversation_id": data.get("conversation_id")
        }
    
    def generate_conversation_summary(self, history: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of an entire conversation with multiple documents.
        
        Args:
            history: List of events in the conversation
            
        Returns:
            Summary text
        """
        if not history:
            return "No conversation history available."
        
        formats = set()
        intents = set()
        
        for item in history:
            if "format" in item and item["format"]:
                formats.add(item["format"])
            if "intent" in item and item["intent"]:
                intents.add(item["intent"])
        
        events_count = len(history)
        formats_str = ", ".join(formats) if formats else "Unknown"
        intents_str = ", ".join(intents) if intents else "Unknown"
        
        summary = f"Conversation with {events_count} events\n"
        summary += f"Formats: {formats_str}\n"
        summary += f"Intents: {intents_str}\n"
        
        if events_count > 0:
            summary += "\nKey events:\n"
            
            # Add up to 3 key events
            for i, item in enumerate(history[-3:]):
                format_type = item.get("format", "Unknown")
                intent = item.get("intent", "Unknown")
                timestamp = item.get("timestamp", "").split("T")[0]
                summary += f"- {timestamp}: {format_type} with {intent} intent\n"
        
        return summary