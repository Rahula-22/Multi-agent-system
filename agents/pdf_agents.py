import io
import re
from typing import Dict, Any, List, Tuple, Optional
import PyPDF2
from agents.base_agent import BaseAgent

class PDFAgent(BaseAgent):
    """Agent for processing PDF documents and extracting structured information."""
    
    def __init__(self):
        super().__init__(name="PDF Agent")
        self.document_types = {
            "invoice": ["invoice", "bill", "receipt", "payment", "due date", "amount due"],
            "contract": ["agreement", "contract", "terms", "conditions", "parties", "signed"],
            "report": ["report", "analysis", "findings", "summary", "conclusion"],
            "letter": ["dear", "sincerely", "regards", "to whom it may concern"],
            "resume": ["experience", "skills", "education", "resume", "cv", "curriculum vitae"]
        }
    
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
                "has_tables": self._detect_tables(extracted_text)
            }
            
            if doc_type == "invoice":
                result["invoice_data"] = self._extract_invoice_data(extracted_text)
            
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
                invoice_data["total_amount"] = match.group(1)
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