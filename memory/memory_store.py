import json
import sqlite3
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

class MemoryStore:
    """Memory store using SQLite for persistent agent communication and data."""
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create required tables
        tables = {
            "metadata": """
                CREATE TABLE IF NOT EXISTS metadata (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    source TEXT,
                    format_type TEXT,
                    intent TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """,
            "classifications": """
                CREATE TABLE IF NOT EXISTS classifications (
                    id TEXT PRIMARY KEY,
                    format TEXT,
                    intent TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """,
            "extractions": """
                CREATE TABLE IF NOT EXISTS extractions (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    agent TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """,
            "results": """
                CREATE TABLE IF NOT EXISTS results (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    format_type TEXT,
                    intent TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """,
            "actions": """
                CREATE TABLE IF NOT EXISTS actions (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    chain_id TEXT,
                    action_id TEXT,
                    status TEXT,
                    triggered_at TEXT,
                    completed_at TEXT,
                    result TEXT
                )
            """,
            "decision_traces": """
                CREATE TABLE IF NOT EXISTS decision_traces (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    agent TEXT,
                    decision_point TEXT,
                    reasoning TEXT,
                    alternatives TEXT,
                    selected_option TEXT,
                    confidence REAL,
                    timestamp TEXT
                )
            """,
            "alerts": """
                CREATE TABLE IF NOT EXISTS alerts (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    source TEXT,
                    timestamp TEXT,
                    data TEXT
                )
            """
        }
        
        for table_sql in tables.values():
            cursor.execute(table_sql)
            
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
    
    def store_action(self, conversation_id: str, chain_id: str, action_id: str, 
                     status: str, result: Dict[str, Any]) -> str:
        """Store a triggered action from an action chain."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        action_record_id = str(uuid.uuid4())
        timestamp = self.get_timestamp()
        
        cursor.execute(
            """
            INSERT INTO actions 
            (id, conversation_id, chain_id, action_id, status, triggered_at, completed_at, result) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action_record_id,
                conversation_id,
                chain_id,
                action_id,
                status,
                timestamp,
                timestamp if status in ["completed", "failed"] else None,
                json.dumps(result)
            )
        )
        
        conn.commit()
        conn.close()
        return action_record_id
    
    def update_action_status(self, action_id: str, status: str, result: Dict[str, Any] = None) -> bool:
        """Update the status of a previously stored action."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if result is not None:
            cursor.execute(
                """
                UPDATE actions 
                SET status = ?, completed_at = ?, result = ?
                WHERE id = ?
                """,
                (
                    status,
                    self.get_timestamp(),
                    json.dumps(result),
                    action_id
                )
            )
        else:
            cursor.execute(
                """
                UPDATE actions 
                SET status = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    status,
                    self.get_timestamp() if status in ["completed", "failed"] else None,
                    action_id
                )
            )
        
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0
    
    def store_decision_trace(self, conversation_id: str, agent: str, decision_data: Dict[str, Any]) -> str:
        """Store an agent's decision-making trace."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        trace_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO decision_traces 
            (id, conversation_id, agent, decision_point, reasoning, alternatives, selected_option, confidence, timestamp) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                conversation_id,
                agent,
                decision_data.get("decision_point", ""),
                decision_data.get("reasoning", ""),
                json.dumps(decision_data.get("alternatives", [])),
                decision_data.get("selected_option", ""),
                decision_data.get("confidence", 0.0),
                self.get_timestamp()
            )
        )
        
        conn.commit()
        conn.close()
        return trace_id
    
    def store_alert(self, conversation_id: str, alert_data: Dict[str, Any]) -> str:
        """Store an alert generated by the system."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        alert_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO alerts 
            (id, conversation_id, alert_type, severity, message, source, timestamp, data) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                conversation_id,
                alert_data.get("type", ""),
                alert_data.get("severity", "medium"),
                alert_data.get("message", ""),
                alert_data.get("source", ""),
                self.get_timestamp(),
                json.dumps(alert_data.get("data", {}))
            )
        )
        
        conn.commit()
        conn.close()
        return alert_id
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all activities for a specific conversation in chronological order."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all relevant data from tables
        tables_and_types = {
            "metadata": "metadata",
            "extractions": "extraction", 
            "results": "result",
            "actions": "action",
            "decision_traces": "decision_trace",
            "alerts": "alert"
        }
        
        history = []
        
        for table, activity_type in tables_and_types.items():
            cursor.execute(f"SELECT * FROM {table} WHERE conversation_id = ?", (conversation_id,))
            rows = cursor.fetchall()
            
            for row in rows:
                item = dict(row)
                item["activity_type"] = activity_type
                
                # Parse JSON fields based on table
                if table == "actions":
                    item["result"] = json.loads(item["result"]) if item["result"] else {}
                elif table == "decision_traces":
                    item["alternatives"] = json.loads(item["alternatives"]) if item["alternatives"] else []
                else:
                    if "data" in item:
                        item["data"] = json.loads(item["data"])
                
                history.append(item)
        
        conn.close()
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get("timestamp") or x.get("triggered_at", ""))
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
    
    def get_action_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all actions for a specific conversation."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM actions WHERE conversation_id = ? ORDER BY triggered_at ASC",
            (conversation_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {**dict(row), "result": json.loads(row["result"]) if row["result"] else {}}
            for row in rows
        ]
    
    def get_decision_traces(self, conversation_id: str, agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get decision traces for a conversation, optionally filtered by agent."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if agent:
            cursor.execute(
                "SELECT * FROM decision_traces WHERE conversation_id = ? AND agent = ? ORDER BY timestamp ASC",
                (conversation_id, agent)
            )
        else:
            cursor.execute(
                "SELECT * FROM decision_traces WHERE conversation_id = ? ORDER BY timestamp ASC",
                (conversation_id,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {**dict(row), "alternatives": json.loads(row["alternatives"]) if row["alternatives"] else []}
            for row in rows
        ]
    
    def get_alerts(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get alerts for a specific conversation."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM alerts WHERE conversation_id = ? ORDER BY timestamp ASC",
            (conversation_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {**dict(row), "data": json.loads(row["data"]) if row["data"] else {}}
            for row in rows
        ]
    
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
        
        if len(formats) > 1:
            merged_data = {"formats": formats, "merged": True}
            
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