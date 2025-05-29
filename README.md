# Multi-Agent AI System

## Overview
This project implements a multi-agent AI system designed to intelligently classify and route data inputs in various formats (PDF, JSON, Email) to specialized agents for extraction. The system maintains context to support downstream chaining and audits.

## Project Structure
The project is organized into several directories and files, each serving a specific purpose:

- **agents/**: Contains the core agent implementations.
  - `classifier_agent.py`: Classifies input format and intent, routing to the appropriate agent.
  - `json_agent.py`: Processes JSON data, extracting and reformatting it.
  - `email_agent.py`: Parses email content to extract relevant information.
  - `pdf_agent.py`: Extracts text and structured data from PDF documents.
  - `base_agent.py`: Provides a base class for all agents.

- **memory/**: Manages shared memory for storing input metadata and extracted fields.
  - `memory_store.py`: Implements the shared memory functionality.
  - `models.py`: Defines data models for memory storage.

- **utils/**: Contains utility functions for file handling, parsing, and validation.
  - `file_handlers.py`: Handles file uploads and processing.
  - `parsers.py`: Provides parsing functions for email and JSON.
  - `validators.py`: Validates input data integrity.

- **data/**: Holds sample files for testing the agents.
  - `sample_emails/`: Sample email files.
  - `sample_jsons/`: Sample JSON files.
  - `sample_pdfs/`: Sample PDF files.

- **mcp/**: Implements the Model Context Protocol for agent communication.
  - `protocol.py`: Defines the communication protocol.

- **api/**: Contains the API for interacting with the system.
  - `endpoints.py`: Defines API endpoints.
  - `schemas.py`: Contains data schemas for API validation.

- **tests/**: Includes unit tests for the agents.
  - `test_classifier.py`: Tests for the Classifier Agent.
  - `test_json_agent.py`: Tests for the JSON Agent.
  - `test_email_agent.py`: Tests for the Email Parser Agent.

- **requirements.txt**: Lists project dependencies.

- **main.py**: Entry point for the application, initializing agents and starting the API server.

- **config.py**: Contains configuration settings for the application.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd multi-agent-system
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (optional):
   ```
   cp .env.example .env
   # Edit .env file with your configuration
   ```

4. Run the application:
   ```
   python main.py
   ```

## Usage
### API Endpoints
- **POST /api/v1/process**: Upload data for processing
  ```bash
  # Example: Process a JSON file
  curl -X POST -H "Content-Type: multipart/form-data" \
    -F "file=@./data/sample_jsons/customer_data.json" \
    -F "description=Customer information for processing" \
    http://localhost:8000/api/v1/process
  ```

- **GET /api/v1/results/{task_id}**: Retrieve processing results
  ```bash
  curl http://localhost:8000/api/v1/results/task_123456
  ```

### Input Formats
The system accepts the following input formats:
- **JSON**: Structured data in JSON format
- **Email**: Raw email content or .eml files
- **PDF**: Document files containing text and structured data

### Output Format
Results are returned in a standardized JSON format:
```json
{
  "task_id": "task_123456",
  "status": "completed",
  "agent_used": "json_agent",
  "extracted_data": {
    "field1": "value1",
    "field2": "value2"
  },
  "confidence_score": 0.95,
  "processing_time": "0.234s"
}
```

## Architecture
### Agent Communication Flow
```
Input Data → Classifier Agent → Specialized Agent → Shared Memory
                      ↓                  ↓
                 Metadata           Extracted Data
```

### Components Interaction
- **Classifier Agent**: Entry point that analyzes input and directs to specialized agents
- **Specialized Agents**: Process specific data formats and extract structured information
- **Shared Memory**: Maintains context across agent interactions
- **MCP (Model Context Protocol)**: Facilitates structured communication between agents

## Development Guide
### Creating a New Agent
1. Inherit from the BaseAgent class in `agents/base_agent.py`
2. Implement the required methods:
   ```python
   class NewFormatAgent(BaseAgent):
       def process(self, data, context=None):
           # Processing logic here
           return extracted_data
   ```
3. Register the agent in `main.py`

### Testing
Run the unit tests to ensure your changes don't break existing functionality:
```
pytest tests/
```

### Code Style
Follow PEP 8 guidelines and use the provided linting configuration:
```
flake8 .
```

## Troubleshooting
### Common Issues
- **Agent timeout errors**: Increase the timeout setting in `config.py`
- **Memory overflow**: Adjust the memory limits in the configuration
- **Format not recognized**: Ensure the input format matches one of the supported types

### Logging
Check the logs for detailed error information:
```
tail -f logs/app.log
```

## API Reference
For detailed API documentation, visit:
```
http://localhost:8000/docs
```
or
```
http://localhost:8000/redoc
```

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
- Thanks to all contributors who have helped shape this project
- Special thanks to the open-source libraries that made this possible