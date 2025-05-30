import io
import re
from typing import Dict, Any, List, Tuple, Optional
import PyPDF2
from agents.base_agent import BaseAgent
import datetime

class PDFAgent(BaseAgent):
    """Agent for processing PDF documents and extracting structured information."""
    
    def __init__(self):
        super().__init__(name="PDF Agent")
        self.document_types = {
            "invoice": ["invoice", "bill", "receipt", "payment", "due date", "amount due"],
            "contract": ["agreement", "contract", "terms", "conditions", "parties", "signed"],
            "report": ["report", "analysis", "findings", "summary", "conclusion"],
            "policy": ["policy", "regulation", "compliance", "guidelines", "rules", "procedures"],
            "letter": ["dear", "sincerely", "regards", "to whom it may concern"],
            "resume": ["experience", "skills", "education", "resume", "cv", "curriculum vitae"]
        }
        
        # Regulatory keywords to flag in policy documents
        self.regulatory_keywords = [
            "GDPR", "FDA", "HIPAA", "PCI DSS", "SOX", "CCPA", "GLBA", 
            "COPPA", "FERPA", "FISMA", "NERC", "SEC", "FTC", "FINRA",
            "data protection", "privacy regulation", "compliance requirement"
        ]
        
        # Invoice high-value threshold
        self.high_value_threshold = 10000
    
    def process(self, pdf_data: bytes) -> Dict[str, Any]:
        """Process PDF data and extract information."""
        try:
            extracted_text = self._extract_text_from_pdf(pdf_data)
            doc_type = self._detect_document_type(extracted_text)
            key_values = self._extract_key_value_pairs(extracted_text)
            
            result = {
                "document_type": doc_type,
                "text_length": len(extracted_text),
                "extracted_data": key_values,
                "text_snippet": extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text,
                "status": "processed",
                "has_tables": self._detect_tables(extracted_text),
                "flags": []  # Initialize flags list
            }
            
            # Process based on document type
            if doc_type == "invoice":
                invoice_data = self._extract_invoice_data(extracted_text)
                result["invoice_data"] = invoice_data
                
                # Extract line items
                line_items = self._extract_line_items(extracted_text)
                result["line_items"] = line_items
                
                # Flag high-value invoices
                if self._check_high_value_invoice(invoice_data):
                    result["flags"].append({
                        "type": "high_value_invoice",
                        "message": f"Invoice total exceeds {self.high_value_threshold}",
                        "severity": "high"
                    })
                    
            elif doc_type == "policy" or "policy" in doc_type:
                policy_data = self._extract_policy_data(extracted_text)
                result["policy_data"] = policy_data
                
                # Check for regulatory keywords
                regulatory_mentions = self._check_regulatory_keywords(extracted_text)
                if regulatory_mentions:
                    result["regulatory_mentions"] = regulatory_mentions
                    result["flags"].append({
                        "type": "regulatory_content",
                        "message": f"Document mentions regulatory frameworks: {', '.join(regulatory_mentions)}",
                        "severity": "medium"
                    })
            
            self.log_processing(pdf_data, result)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to process PDF document"
            }
    
    def _extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text from PDF data."""
        text = ""
        try:
            pdf_file = io.BytesIO(pdf_data)
            reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
                
        except Exception as e:
            raise ValueError(f"Error extracting text from PDF: {str(e)}")
            
        return text
    
    def _detect_document_type(self, text: str) -> str:
        """Detect the type of document based on content."""
        text_lower = text.lower()
        
        # Count keyword occurrences for each document type
        type_scores = {}
        for doc_type, keywords in self.document_types.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            type_scores[doc_type] = count
            
        # Get the document type with highest keyword match
        if type_scores:
            best_match = max(type_scores.items(), key=lambda x: x[1])
            if best_match[1] > 0:
                return best_match[0]
                
        return "unknown"
    
    def _extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """Extract potential key-value pairs from text."""
        patterns = [
            r"([\w\s]+):\s*([\w\s,.@\-]+)",  # Pattern like "Key: Value"
            r"([\w\s]+)\s*=\s*([\w\s,.@\-]+)"  # Pattern like "Key = Value"
        ]
        
        key_values = {}
        lines = text.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            for pattern in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    key = match[0].strip().lower()
                    value = match[1].strip()
                    if key and value:
                        key_values[key] = value
        
        return key_values
    
    def _detect_tables(self, text: str) -> bool:
        """Detect if the document appears to contain tables."""
        table_indicators = [
            r"(\|[^\|]+){3,}\|",  # Multiple lines with pipe separations
            r"(\t[^\t]+){3,}",    # Multiple tabs
            r"(\d+\.\s+[\w\s]+\n){3,}"  # Row numbers followed by data
        ]
        
        for pattern in table_indicators:
            if re.search(pattern, text):
                return True
                
        return False
    
    def _extract_invoice_data(self, text: str) -> Dict[str, Any]:
        """Extract invoice-specific data from document text."""
        invoice_data = {}
        
        # Extract invoice number
        invoice_patterns = [
            r"invoice\s*(?:#|number|num|no)?\s*[:\.]?\s*([A-Z0-9\-]+)",
            r"invoice\s*id\s*[:\.]?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["invoice_number"] = match.group(1)
                break
        
        # Extract date
        date_patterns = [
            r"date\s*[:\.]?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})",
            r"date\s*[:\.]?\s*(\w+\s+\d{1,2},?\s+\d{4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data["date"] = match.group(1)
                break
        
        # Extract total amount
        amount_patterns = [
            r"total\s*(?:amount|sum)?\s*[:\.]?\s*[$€£]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
            r"amount\s*due\s*[:\.]?\s*[$€£]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Remove commas and convert to float
                amount_str = match.group(1).replace(',', '')
                try:
                    invoice_data["total_amount"] = float(amount_str)
                except ValueError:
                    invoice_data["total_amount"] = amount_str
                break
        
        # Extract currency
        currency_patterns = [
            r"currency\s*[:\.]?\s*(\w{3})",
            r"(USD|EUR|GBP|JPY|CAD|AUD)"
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text)
            if match:
                invoice_data["currency"] = match.group(1)
                break
        
        return invoice_data
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract line items from invoice text.
        This will attempt to find patterns that represent invoice line items.
        """
        line_items = []
        
        # Split text into lines and look for potential item sections
        lines = text.split('\n')
        
        # Find potential line item section boundaries
        item_section_start = -1
        item_section_end = -1
        
        # Look for headings that typically indicate line item sections
        headers = ["item description", "description", "item", "qty", "quantity", "price", "amount"]
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if this line contains multiple header keywords
            header_matches = sum(1 for header in headers if header in line_lower)
            if header_matches >= 2 and item_section_start == -1:
                item_section_start = i
                continue
            
            # Look for totals section which typically comes after line items
            if item_section_start != -1 and any(x in line_lower for x in ["subtotal", "total", "sum", "amount due"]):
                item_section_end = i
                break
        
        # If we found a section with line items
        if item_section_start != -1:
            # Default to end of document if no end marker found
            if item_section_end == -1:
                item_section_end = len(lines)
            
            # Process lines between start and end markers
            for i in range(item_section_start + 1, item_section_end):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Try to extract line item information using various patterns
                
                # Pattern 1: Description followed by quantity and price
                # Example: "Widget X    2    $10.00    $20.00"
                pattern1 = re.search(r"(.+?)\s+(\d+)\s+[\$\€\£]?(\d+(?:\.\d{2})?)\s+[\$\€\£]?(\d+(?:\.\d{2})?)", line)
                if pattern1:
                    line_items.append({
                        "description": pattern1.group(1).strip(),
                        "quantity": int(pattern1.group(2)),
                        "unit_price": float(pattern1.group(3)),
                        "total": float(pattern1.group(4))
                    })
                    continue
                
                # Pattern 2: Item code, description, and amount
                # Example: "1234 - Office Supplies - $50.00"
                pattern2 = re.search(r"([A-Z0-9\-]+)\s*[-:]\s*(.+?)[-:]\s*[\$\€\£]?(\d+(?:\.\d{2})?)", line)
                if pattern2:
                    line_items.append({
                        "code": pattern2.group(1).strip(),
                        "description": pattern2.group(2).strip(),
                        "amount": float(pattern2.group(3))
                    })
                    continue
                
                # Pattern 3: Just item and price
                # Example: "Consulting services - $1,200.00"
                pattern3 = re.search(r"(.+?)[-:]\s*[\$\€\£]?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", line)
                if pattern3:
                    amount_str = pattern3.group(2).replace(',', '')
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        amount = 0.0
                    
                    line_items.append({
                        "description": pattern3.group(1).strip(),
                        "amount": amount
                    })
        
        return line_items
    
    def _extract_policy_data(self, text: str) -> Dict[str, Any]:
        """Extract policy-specific information."""
        policy_data = {}

        policy_patterns = [
            r"policy\s*(?:#|number|num|no)?\s*[:\.]?\s*([A-Z0-9\-]+)",
            r"policy\s*id\s*[:\.]?\s*([A-Z0-9\-]+)"
        ]
        
        for pattern in policy_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                policy_data["policy_number"] = match.group(1)
                break

        date_patterns = [
            r"effective\s*date\s*[:\.]?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})",
            r"effective\s*[:\.]?\s*(\w+\s+\d{1,2},?\s+\d{4})"
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                policy_data["effective_date"] = match.group(1)
                break
 
        issuer_patterns = [
            r"issued\s*by\s*[:\.]?\s*([\w\s,\.]+)",
            r"issuing\s*authority\s*[:\.]?\s*([\w\s,\.]+)",
            r"published\s*by\s*[:\.]?\s*([\w\s,\.]+)"
        ]
        
        for pattern in issuer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                policy_data["issuer"] = match.group(1).strip()
                break
        
        section_headers = re.findall(r"(?:^|\n)([IVX]+\.\s+[\w\s]+)(?:$|\n)", text)
        if section_headers:
            policy_data["sections"] = section_headers
        
        return policy_data
    
    def _check_high_value_invoice(self, invoice_data: Dict[str, Any]) -> bool:
        """Check if invoice is high value (exceeds threshold)."""
        if "total_amount" in invoice_data:
            try:
                if isinstance(invoice_data["total_amount"], (int, float)):
                    return invoice_data["total_amount"] > self.high_value_threshold

                if isinstance(invoice_data["total_amount"], str):
                    # Remove any currency symbols and commas
                    clean_amount = re.sub(r'[^\d.]', '', invoice_data["total_amount"])
                    amount = float(clean_amount)
                    return amount > self.high_value_threshold
            except (ValueError, TypeError):
                pass
                
        return False
    
    def _check_regulatory_keywords(self, text: str) -> List[str]:
        """Check for mentions of regulatory frameworks."""
        found_keywords = []
        
        for keyword in self.regulatory_keywords:
            # Use word boundary to ensure we match whole words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_keywords.append(keyword)
        
        return found_keywords
    
    def log_processing(self, pdf_data: bytes, result: Dict[str, Any]) -> None:
        """Log PDF processing activity."""
        processing_info = {
            "timestamp": datetime.datetime.now().isoformat(),
            "document_type": result.get("document_type", "unknown"),
            "text_length": result.get("text_length", 0),
            "status": result.get("status", "unknown"),
            "flags": result.get("flags", [])
        }
        
        print(f"Processed {processing_info['document_type']} document: " +
              f"{len(processing_info['flags'])} flags raised")