from typing import Dict, Any, Tuple
import re
import uuid

class EmailParserAgent:
    def __init__(self):
        self.conversation_id = None
        
    def parse_email(self, email_body: str) -> Dict[str, Any]:
        """Extract key information from email content"""
        sender_name, sender_email = self.extract_sender_info(email_body)
        intent = self.extract_intent(email_body)
        urgency = self.extract_urgency(email_body)
        
        # Generate conversation ID if not present
        conversation_id = self.extract_conversation_id(email_body) or f"em_{uuid.uuid4().hex[:6]}"
        
        return {
            "sender_name": sender_name,
            "sender_email": sender_email,
            "intent": intent,
            "urgency": urgency,
            "conversation_id": conversation_id
        }
    
    def extract_sender_info(self, email_body: str) -> Tuple[str, str]:
        """Extract sender name and email address"""
        # Look for "From: Name <email>" pattern
        from_match = re.search(r'From:\s*(.*?)\s*<([^>]+)>', email_body)
        if from_match:
            return from_match.group(1).strip(), from_match.group(2).strip()
        
        # Look for "From: email" pattern
        email_match = re.search(r'From:\s*([^\s]+@[^\s]+)', email_body)
        if email_match:
            email = email_match.group(1).strip()
            # Use part before @ as name if no name found
            name = email.split('@')[0]
            return name, email
        
        return "Unknown", "unknown@example.com"
    
    def extract_intent(self, email_body: str) -> str:
        """Determine the email's intent based on content"""
        email_lower = email_body.lower()
        
        # Check for different intent keywords
        if any(word in email_lower for word in ["invoice", "payment", "bill", "receipt"]):
            return "Invoice"
        elif any(word in email_lower for word in ["rfq", "quote", "quotation", "pricing", "proposal"]):
            return "RFQ"
        elif any(word in email_lower for word in ["complaint", "issue", "problem", "dissatisfied", "unhappy"]):
            return "Complaint"
        elif any(word in email_lower for word in ["regulation", "compliance", "legal", "requirement", "policy"]):
            return "Regulation"
        
        return "Other"
    
    def extract_urgency(self, email_body: str) -> str:
        """Determine urgency level based on content and subject"""
        email_lower = email_body.lower()
        subject_match = re.search(r'Subject:\s*(.*)', email_body, re.IGNORECASE)
        subject = subject_match.group(1) if subject_match else ""
        
        # Check urgency indicators
        high_urgency = ["urgent", "asap", "immediately", "emergency", "critical", "important"]
        if any(word in email_lower for word in high_urgency) or any(word in subject.lower() for word in high_urgency):
            return "High"
        
        medium_urgency = ["soon", "timely", "promptly", "attention", "priority"]
        if any(word in email_lower for word in medium_urgency):
            return "Medium"
        
        return "Low"
    
    def extract_conversation_id(self, email_body: str) -> str:
        """Extract conversation ID from email if present"""
        patterns = [
            r'conversation[_\-\s]?id[\s:]*([a-zA-Z0-9_\-]+)',
            r'thread[_\-\s]?id[\s:]*([a-zA-Z0-9_\-]+)',
            r'ref[_\-\s]?id[\s:]*([a-zA-Z0-9_\-]+)',
            r'#([a-zA-Z0-9]{6,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None