from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality and defines the interface that all agents must implement.
    """
    
    def __init__(self, name: str):
        """
        Initialize the agent with a name.
        
        Args:
            name: The name of the agent
        """
        self.name = name
        self.last_processed_data = None
    
    @abstractmethod
    def process(self, data: Any) -> Dict[str, Any]:
        """
        Process input data and return structured results.
        
        Args:
            data: The input data in any format
            
        Returns:
            Processed data as a dictionary
        """
        pass
    
    def log_processing(self, input_data: Any, output_data: Dict[str, Any]) -> None:
        """
        Log the processing of data for debugging purposes.
        
        Args:
            input_data: The input data that was processed
            output_data: The output data after processing
        """
        # Store the last processed data for potential debugging
        self.last_processed_data = {
            "input": input_data,
            "output": output_data
        }
        
        # In a real implementation, this could write to a log file or logging service
        print(f"[{self.name}] Processed input of type {type(input_data).__name__}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent.
        
        Returns:
            Dictionary containing agent metadata
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
        }
    
    def validate_input(self, data: Any) -> bool:
        """
        Validate that the input data is in a format this agent can process.
        
        Args:
            data: The input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True