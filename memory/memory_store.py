import json
import sqlite3
import uuid
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class MemoryStore:
    """Memory store implementation using SQLite for persistent agent communication and data."""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metadata table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            source TEXT,
            format_type TEXT,
            intent TEXT,
            timestamp TEXT,
            data TEXT
        )
        """)
        
        # Create classifications table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS classifications (
            id TEXT PRIMARY KEY,
            format TEXT,
            intent TEXT,
            timestamp TEXT,
            data TEXT
        )
        """)
        
        # Create extractions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS extractions (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            agent TEXT,
            timestamp TEXT,
            data TEXT
        )
        """)
        
        # Create results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id TEXT PRIMARY KEY,
            conversation_id TEXT,
            format_type TEXT,
            intent TEXT,
            timestamp TEXT,
            data TEXT
        )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_conversation_id(self) -> str:
        """Generate a unique conversation ID."""
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def add_classification(self, classification: Dict[str, Any]) -> str:
        """Add a classification result to memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        classification_id = str(uuid.uuid4())
        
        cursor.execute(
            """
            INSERT INTO classifications (id, format, intent, timestamp, data) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                classification_id,
                classification.get("format", ""),
                classification.get("intent", ""),
                classification.get("timestamp", self.get_timestamp()),
                json.dumps(classification)
            )
        )
        
        conn.commit()
        conn.close()
        
        return classification_id
    
    def store_metadata(self, metadata: Dict[str, Any]) -> str:
        """Store input metadata in memory."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_id = str(uuid.uuid4())
        
        cursor.execute(
            """
            INSERT INTO metadata (id, conversation_id, source, format_type, intent, timestamp, data) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                metadata_id,
                metadata.get("conversation_id", ""),
                metadata.get("source", ""),
                metadata.get("format_type", ""),
                metadata.get("intent", ""),
                metadata.get("timestamp", self.get_timestamp()),
                json.dumps(metadata)
            )
        )
        
        conn.commit()
        conn.close()
        
        return metadata_id
    
    def store_extraction(self, conversation_id: str, agent: str, data: Dict[str, Any]) -> str:
        """Store extraction results from an agent."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        extraction_id = str(uuid.uuid4())
        
        cursor.execute(
            """
            INSERT INTO extractions (id, conversation_id, agent, timestamp, data) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                extraction_id,
                conversation_id,
                agent,
                self.get_timestamp(),
                json.dumps(data)
            )
        )
        
        conn.commit()
        conn.close()
        
        return extraction_id
    
    def store_result(self, conversation_id: str, result: Dict[str, Any]) -> str:
        """Store final processing result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        result_id = str(uuid.uuid4())
        
        cursor.execute(
            """
            INSERT INTO results (id, conversation_id, format_type, intent, timestamp, data) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                result_id,
                conversation_id,
                result.get("format_type", ""),
                result.get("intent", ""),
                self.get_timestamp(),
                json.dumps(result)
            )
        )
        
        conn.commit()
        conn.close()
        
        return result_id
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all activities for a specific conversation in chronological order."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query metadata
        cursor.execute(
            "SELECT * FROM metadata WHERE conversation_id = ?",
            (conversation_id,)
        )
        metadata_rows = cursor.fetchall()
        
        # Query extractions
        cursor.execute(
            "SELECT * FROM extractions WHERE conversation_id = ?",
            (conversation_id,)
        )
        extraction_rows = cursor.fetchall()
        
        # Query results
        cursor.execute(
            "SELECT * FROM results WHERE conversation_id = ?",
            (conversation_id,)
        )
        result_rows = cursor.fetchall()
        
        conn.close()
        
        # Convert rows to dictionaries and combine
        history = []
        
        for row in metadata_rows:
            item = dict(row)
            item["activity_type"] = "metadata"
            item["data"] = json.loads(item["data"])
            history.append(item)
            
        for row in extraction_rows:
            item = dict(row)
            item["activity_type"] = "extraction"
            item["data"] = json.loads(item["data"])
            history.append(item)
            
        for row in result_rows:
            item = dict(row)
            item["activity_type"] = "result"
            item["data"] = json.loads(item["data"])
            history.append(item)
            
        # Sort by timestamp
        history.sort(key=lambda x: x["timestamp"])
        
        return history
    
    def get_latest_extraction(self, conversation_id: str, agent: str) -> Optional[Dict[str, Any]]:
        """Get the most recent extraction from a specific agent for a conversation."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM extractions 
            WHERE conversation_id = ? AND agent = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (conversation_id, agent)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            item = dict(row)
            item["data"] = json.loads(item["data"])
            return item
        
        return None
    
    def get_result(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the final result for a conversation."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT * FROM results 
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (conversation_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            item = dict(row)
            item["data"] = json.loads(item["data"])
            return item
        
        return None
    
    def find_related_inputs(self, conversation_id: str) -> List[str]:
        """Find all inputs related to the current conversation"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT DISTINCT format_type FROM metadata WHERE conversation_id = ?",
            (conversation_id,)
        )
        formats = [row['format_type'] for row in cursor.fetchall()]
        conn.close()
        
        return formats

    def merge_results(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Merge results from multiple agents for related inputs"""
        formats = self.find_related_inputs(conversation_id)
        
        # If we have multiple formats in the same conversation, merge results
        if len(formats) > 1:
            merged_data = {"formats": formats, "merged": True}
            
            # Get latest extraction from each agent
            for agent_name in ["json_agent", "email_agent", "pdf_agent"]:
                extraction = self.get_latest_extraction(conversation_id, agent_name)
                if extraction:
                    merged_data[f"{agent_name}_data"] = extraction["data"]
            result = {
                "format_type": "merged",
                "intent": "composite",
                "data": merged_data
            }
            self.store_result(conversation_id, result)
            
            return merged_data
        
        return None