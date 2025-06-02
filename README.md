# Multi-Agent AI System

## Overview
This project implements a multi-agent AI system designed to intelligently classify and route data inputs in various formats (PDF, JSON, Email) to specialized agents for extraction. The system maintains context to support downstream chaining and audits.

## Architecture
The system follows a hierarchical architecture with a classifier agent at the top:

1. **Input Processing**: All inputs are first processed by the Classifier Agent
2. **Classification**: The input is analyzed for format and intent
3. **Routing**: Data is routed to specialized agents based on classification
4. **Extraction**: Specialized agents extract structured data from their assigned formats
5. **Memory Storage**: Extracted data and context are stored in shared memory
6. **Result Delivery**: Processed results are returned through the API

### Agent Logic
- **Classifier Agent**: Uses content analysis and metadata to determine input type. Implements a multi-stage classification pipeline:
  1. Format detection (MIME type, headers, structural analysis)
  2. Intent analysis (searching for key patterns that indicate purpose)
  3. Route selection (mapping to appropriate specialized agent)

- **JSON Agent**: Processes structured JSON data through:
  1. Schema validation
  2. Normalization
  3. Field extraction based on configurable templates
  4. Transformation to internal format

- **Email Agent**: Parses email content through:
  1. Header extraction (From, To, Subject, Date)
  2. Body parsing (text/html)
  3. Attachment handling
  4. Named entity recognition for key information

- **PDF Agent**: Handles document processing through:
  1. Text extraction
  2. Table recognition
  3. Form field identification
  4. Structure preservation

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
   git clone https://github.com/Rahula-22/Multi-agent-system.git
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

### Input Formats
The system accepts the following input formats:
- **JSON**: Structured data in JSON format
- **Email**: Raw email content or .eml files
- **PDF**: Document files containing text and structured data

### Components Interaction
- **Classifier Agent**: Entry point that analyzes input and directs to specialized agents
- **Specialized Agents**: Process specific data formats and extract structured information
- **Shared Memory**: Maintains context across agent interactions
- **MCP (Model Context Protocol)**: Facilitates structured communication between agents

## Sample Inputs are included in data folder and output processed is given below
After processing, the system returns structured data like:

```json
{
  "task_id": "task_789abc",
  "status": "completed",
  "input_type": "json",
  "processing_time": "0.87s",
  "extracted_data": {
    "customer_id": "C12345",
    "customer_name": "Jane Smith",
    "order_id": "ORD-7890",
    "order_total": 74.48,
    "items_count": 2,
    "shipping_zip": "12345"
  },
  "confidence_score": 0.95,
  "memory_reference": "mem_456def"
}
```

## Output Logs
The system generates detailed logs during processing to help with debugging and auditing. Example output log:

```
2025-06-01 14:32:18 [INFO] Classifier: Detected format: JSON (confidence: 0.97)
2025-06-01 14:32:19 [INFO] JSON Agent: Starting processing of document doc_567
2025-06-01 14:32:20 [INFO] System: Processing complete in 0.87s
```

## Processing Results
### Screenshots and Post-Action Outputs

Below are visual representations of the system in action:

![Agent Classification Process](docs/images/agent_classification.png)
*Figure 1: The Classifier Agent analyzing input and determining its type*

![PDF Processing Example](docs/images/pdf_processing.png)
*Figure 2: PDF Agent extracting structured information from a document*

![Email Processing Results](docs/images/email_results.png)
*Figure 3: Results of processing an email through the Email Agent*

All processed outputs are stored in the `/results` directory with both raw and formatted versions:

- `/results/raw/`: Contains the complete output data
- `/results/formatted/`: Contains human-readable formatted reports

## Agent Flow and Communication Diagram

The system follows a hierarchical processing flow with bidirectional communication between agents:

```
┌─────────────────┐     ┌───────────────────┐
│                 │     │                   │
│  Input Source   ├────►│  Classifier Agent │
│                 │     │                   │
└─────────────────┘     └──────┬─────┬──────┘
                               │     │     │
                 ┌─────────────┘     │     └──────────────┐
                 │                   │                    │
        ┌────────▼───────┐  ┌────────▼───────┐   ┌────────▼───────┐
        │                │  │                │   │                │
        │   JSON Agent   │  │   PDF Agent    │   │   Email Agent  │
        │                │  │                │   │                │
        └────────┬───────┘  └────────┬───────┘   └────────┬───────┘
                 │                   │                    │
                 │                   │                    │
        ┌────────▼───────────────────▼────────────────────▼───────┐
        │                                                         │
        │                     Shared Memory                       │
        │                                                         │
        └─────────────────────────────────────────────────────────┘
```
*Figure 4: Multi-Agent System Architecture and Communication Flow*

The diagram illustrates how data flows through the system:
1. Input is received and passed to the Classifier Agent
2. The Classifier determines the appropriate specialized agent
3. The specialized agent processes the input and extracts data
4. All agents read/write to the shared memory system
5. Results are made available via the API

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


## Troubleshooting
### Common Issues
- **Agent timeout errors**: Increase the timeout setting in `config.py`
- **Memory overflow**: Adjust the memory limits in the configuration
- **Format not recognized**: Ensure the input format matches one of the supported types


## API Reference
For detailed API documentation, visit:
```
http://localhost:8000/docs
```