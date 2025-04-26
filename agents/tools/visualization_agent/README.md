![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: The Visualization Agent specializes in creating visual representations of data. It can process natural language requests and generate appropriate visualizations using matplotlib, making complex data more accessible and understandable through charts, graphs, and other visual formats.

**Input Data Models**

```python
class ToolRequest(Model):
    params: Dict[str, Any]  # Visualization parameters

class ChatMessage(Model):
    content: List[Content]  # Visualization request
    timestamp: datetime
    msg_id: UUID
```

**Output Data Models**

```python
class ToolResponse(Model):
    result: Any  # Generated visualization

class ChatMessage(Model):
    content: List[TextContent]  # Base64 encoded image
    timestamp: datetime
    msg_id: UUID
```

**Features**:

- Dynamic pie chart generation
- Natural language data extraction
- Base64 image encoding
- Direct chat interface
- Flexible visualization options

**Setup**:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Install required visualization libraries:
   ```
   pip install matplotlib
   ```
3. Configure messaging protocols

**Example Usage**:

```python
# Create a pie chart
"Create a pie chart showing: Chrome 60%, Firefox 25%, Safari 15%"

# Generate data visualization
"Visualize this data distribution: A=30, B=45, C=25"

# Custom chart request
"Show me a breakdown of student grades: A=15, B=40, C=30, D=10, F=5"
```

**Protocol Integration**:

- Visualization Protocol: For internal requests
- Chat Protocol: For direct user interaction
- Tool Protocol: For specific visualization tasks
