import os

class Config:
    # General configuration
    APP_NAME = "Multi-Agent AI System"
    APP_VERSION = "1.0.0"
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # Memory configuration
    MEMORY_TYPE = os.getenv("MEMORY_TYPE", "Redis") 
    MEMORY_HOST = os.getenv("MEMORY_HOST", "localhost")
    MEMORY_PORT = os.getenv("MEMORY_PORT", 6379) 
    MEMORY_DB = os.getenv("MEMORY_DB", 0)  

    # API configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = os.getenv("API_PORT", 8000)

    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit

    # Supported input formats
    SUPPORTED_FORMATS = ["PDF", "JSON", "Email"]

    # Intent types
    INTENT_TYPES = ["Invoice", "RFQ", "Complaint", "Regulation"]