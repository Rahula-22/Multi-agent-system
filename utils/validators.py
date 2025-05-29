def validate_json_structure(data, required_fields):
    if not isinstance(data, dict):
        return False, "Input data is not a valid JSON object."
    
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "JSON structure is valid."

def validate_email_format(email):
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, email):
        return False, "Invalid email format."
    
    return True, "Email format is valid."

def validate_pdf_file(file_path):
    import os
    if not os.path.isfile(file_path) or not file_path.endswith('.pdf'):
        return False, "File is not a valid PDF."
    
    return True, "PDF file is valid."