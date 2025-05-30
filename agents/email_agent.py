import re
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
import requests
from agents.base_agent import BaseAgent

class EmailParserAgent(BaseAgent):
    """
    Email Parser Agent that extracts structured fields from emails,
    identifies tone, and triggers appropriate actions based on urgency and tone.
    """
    
    def __init__(self):
        super().__init__(name="Email Parser Agent")
        
        # Tone identification keywords
        self.tone_indicators = {
            "escalation": [
                "escalate", "urgent", "immediately", "asap", "emergency", "critical",
                "deadline", "urgent attention", "priority", "expedite", "promptly"
            ],
            "threatening": [
                "lawyer", "legal action", "sue", "complaint", "demand", "dissatisfied",
                "disappointed", "unacceptable", "compensation", "refund", "consequences"
            ],
            "polite": [
                "please", "thank you", "appreciate", "grateful", "kindly", "regards",
                "sincerely", "respectfully", "consideration"
            ],
            "neutral": [
                "inform", "update", "inquiry", "question", "wondering", "information",
                "request", "seeking", "details"
            ]
        }
        
        # Urgency indicators
        self.urgency_indicators = {
            "High": [
                "urgent", "asap", "immediately", "emergency", "critical", "deadline",
                "today", "now", "expedite", "promptly", "high priority"
            ],
            "Medium": [
                "soon", "important", "attention", "priority", "followup", "timely",
                "quick", "next day", "48 hours"
            ],
            "Low": [
                "when possible", "at your convenience", "no rush", "future reference",
                "for your information", "fyi", "sometime", "update", "routine"
            ]
        }
        
        # Issue/request type keywords
        self.issue_types = {
            "Technical Support": [
                "error", "bug", "issue", "problem", "not working", "broken", "crash",
                "technical", "support", "troubleshoot", "help me"
            ],
            "Billing Inquiry": [
                "invoice", "payment", "bill", "charge", "subscription", "price",
                "billing", "transaction", "refund", "credit", "debit"
            ],
            "Feature Request": [
                "feature", "enhancement", "improvement", "suggest", "add capability",
                "would like to see", "missing functionality", "update with"
            ],
            "Account Management": [
                "account", "login", "password", "access", "user", "profile", "settings",
                "permissions", "security", "verification", "authentication"
            ],
            "General Inquiry": [
                "question", "inquiry", "information", "details", "how to", "where is",
                "when will", "what is", "wondering"
            ],
            "Complaint": [
                "complaint", "dissatisfied", "unhappy", "disappointed", "poor service",
                "not acceptable", "bad experience", "terrible", "awful"
            ]
        }
    
    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """
        Parse email content and extract structured information.
        
        Args:
            email_content: Raw email content as string
            
        Returns:
            Dictionary with structured email data
        """
        # Extract basic email components
        sender_name, sender_email = self._extract_sender(email_content)
        subject = self._extract_subject(email_content)
        body = self._extract_body(email_content)
        
        # Extract or infer data from content
        urgency = self._determine_urgency(subject, body)
        tone = self._determine_tone(body)
        issue_type = self._determine_issue_type(subject, body)
        
        # Create structured email data
        email_data = {
            "sender_name": sender_name,
            "sender_email": sender_email,
            "subject": subject,
            "urgency": urgency,
            "tone": tone,
            "issue_type": issue_type,
            "body_snippet": body[:200] + "..." if len(body) > 200 else body,
            "parsed_at": datetime.datetime.now().isoformat(),
        }
        
        # Determine and execute action
        action_result = self._trigger_action(email_data)
        email_data["action_taken"] = action_result
        
        return email_data
    
    def _extract_sender(self, email_content: str) -> Tuple[str, str]:
        """Extract sender name and email from 'From' field."""
        from_match = re.search(r'From:\s*(.*?)(?:\n|$)', email_content)
        if not from_match:
            return "Unknown", "unknown@example.com"
        
        from_line = from_match.group(1).strip()
        
        # Try to extract email in format "Name <email@example.com>"
        name_email_match = re.search(r'(.*?)\s*<([^>]+)>', from_line)
        if name_email_match:
            name = name_email_match.group(1).strip()
            email = name_email_match.group(2).strip()
            return name, email
        
        # If plain email address
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', from_line)
        if email_match:
            email = email_match.group(0)
            name = from_line.replace(email, '').strip()
            if not name:
                name = email.split('@')[0]  # Use email username as name
            return name, email
            
        # No email pattern found
        return from_line, "unknown@example.com"
    
    def _extract_subject(self, email_content: str) -> str:
        """Extract email subject."""
        subject_match = re.search(r'Subject:\s*(.*?)(?:\n|$)', email_content)
        if subject_match:
            return subject_match.group(1).strip()
        return "No Subject"
    
    def _extract_body(self, email_content: str) -> str:
        """Extract email body."""
        # Simple approach: body starts after headers (blank line)
        parts = email_content.split('\n\n', 1)
        if len(parts) > 1:
            return parts[1].strip()
        
        # Alternative: take everything after Subject line
        subject_pos = email_content.find('Subject:')
        if subject_pos != -1:
            subject_end = email_content.find('\n', subject_pos)
            if subject_end != -1:
                return email_content[subject_end:].strip()
        
        # If we can't determine where body starts, return original content
        return email_content.strip()
    
    def _determine_urgency(self, subject: str, body: str) -> str:
        """
        Determine email urgency based on keywords in subject and body.
        Returns: "High", "Medium", or "Low"
        """
        combined_text = (subject + " " + body).lower()
        
        # Check for high urgency indicators
        for keyword in self.urgency_indicators["High"]:
            if keyword.lower() in combined_text:
                return "High"
        
        # Check for medium urgency indicators
        for keyword in self.urgency_indicators["Medium"]:
            if keyword.lower() in combined_text:
                return "Medium"
        
        # Default to low if no higher urgency detected
        return "Low"
    
    def _determine_tone(self, body: str) -> str:
        """
        Determine email tone based on content analysis.
        Returns: "escalation", "threatening", "polite", or "neutral"
        """
        body_lower = body.lower()
        tone_scores = {}
        
        # Calculate score for each tone
        for tone, indicators in self.tone_indicators.items():
            score = 0
            for keyword in indicators:
                if keyword.lower() in body_lower:
                    score += 1
            tone_scores[tone] = score
        
        # Return the tone with highest score, default to neutral for ties
        max_score = max(tone_scores.values()) if tone_scores else 0
        if max_score == 0:
            return "neutral"
            
        # In case of tie, prioritize certain tones
        max_tones = [t for t, s in tone_scores.items() if s == max_score]
        priority_order = ["threatening", "escalation", "polite", "neutral"]
        
        for priority in priority_order:
            if priority in max_tones:
                return priority
                
        # Fallback
        return max(tone_scores.items(), key=lambda x: x[1])[0]
    
    def _determine_issue_type(self, subject: str, body: str) -> str:
        """
        Determine the type of issue or request in the email.
        """
        combined_text = (subject + " " + body).lower()
        issue_scores = {}
        
        # Calculate score for each issue type
        for issue_type, indicators in self.issue_types.items():
            score = 0
            for keyword in indicators:
                if keyword.lower() in combined_text:
                    score += 1
            issue_scores[issue_type] = score
        
        # Return issue type with highest score
        max_score = max(issue_scores.values()) if issue_scores else 0
        if max_score == 0:
            return "General Inquiry"
            
        return max(issue_scores.items(), key=lambda x: x[1])[0]
    
    def _trigger_action(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger appropriate action based on email urgency and tone.
        
        Returns:
            Dictionary with action taken details
        """
        urgency = email_data.get("urgency", "Low")
        tone = email_data.get("tone", "neutral")
        issue_type = email_data.get("issue_type", "General Inquiry")
        
        # Logic for escalation to CRM
        if urgency == "High" or tone in ["escalation", "threatening"]:
            return self._notify_crm(email_data)
        
        # Handle normal requests based on issue type
        if issue_type == "Technical Support":
            return {
                "action": "support_ticket_created",
                "priority": "Medium" if urgency == "Medium" else "Low",
                "department": "Technical Support",
                "status": "Simulated - No actual API calls made"
            }
            
        elif issue_type == "Billing Inquiry":
            return {
                "action": "billing_department_routed",
                "priority": urgency,
                "followup_required": urgency != "Low",
                "status": "Simulated - No actual API calls made"
            }
            
        # Default action for routine emails
        return {
            "action": "logged_and_closed",
            "priority": "Low",
            "auto_response": True,
            "status": "Simulated - No actual API calls made"
        }
    
    def _notify_crm(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate notifying CRM system about high priority or escalation email.
        In a real implementation, this would make an API call to a CRM system.
        
        Returns:
            Status of the notification
        """
        # In a real implementation, this would use requests to call a CRM API
        # Here we just simulate the API call
        
        crm_payload = {
            "customer": {
                "name": email_data.get("sender_name", "Unknown"),
                "email": email_data.get("sender_email", "unknown@example.com"),
            },
            "issue": {
                "type": email_data.get("issue_type", "General Inquiry"),
                "urgency": email_data.get("urgency", "Low"),
                "subject": email_data.get("subject", "No Subject"),
                "description": email_data.get("body_snippet", "")[:200]
            },
            "metadata": {
                "source": "email",
                "tone": email_data.get("tone", "neutral"),
                "requires_immediate_attention": email_data.get("urgency") == "High" or 
                                              email_data.get("tone") in ["escalation", "threatening"],
                "timestamp": datetime.datetime.now().isoformat()
            }
        }
        
        # Simulate API response
        return {
            "action": "crm_notification",
            "success": True,
            "crm_ticket_id": f"CRM-{hash(str(email_data)) % 10000:04d}",
            "requires_followup": True,
            "assigned_to": "Customer Relations Team",
            "status": "Simulated - No actual API calls made",
            "payload": crm_payload
        }
    
    def process(self, email_content: str) -> Dict[str, Any]:
        """Process email content (alias for parse_email)."""
        return self.parse_email(email_content)