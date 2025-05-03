![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: The Respondent Agent acts as an intelligent response coordinator, determining when to use specialized tools or visualizations. It analyzes requests and routes them to appropriate agents or tools while maintaining conversation context and ensuring coherent responses.

**Input Data Models**

```python
class RequestResponse(Model):
    request: str   # Original query
    response: str  # Response to process

class ToolRequest(Model):
    params: Dict[str, Any]    # Query for tool selection
```

**Output Data Models**

```python
class ImageResponse(Model):
    request: str  # Original request that generated this image
    image_data: str  # Base64 encoded image
    image_type: str  # e.g., 'png', 'jpeg'
    content_type: str  # e.g., 'image/png', 'image/jpeg'

class ToolResponse(Model):
    result: Any
```

**Features**:

- Intelligent tool selection
- Visualization request handling
- Response formatting and enhancement
- Multi-agent coordination
- Context-aware processing

**Setup**:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Configure agent addresses
3. Set up visualization integration

**Example Usage**:

```python
# Request with potential visualization
"Show me the distribution of grades in the class"

# Complex query requiring tools
"Analyze this dataset and show key trends"

# General response processing
"Summarize these results and highlight important points"
```

**Protocol Integration**:

- Query Protocol: For processing requests
- Visualization Protocol: For creating visual aids
- Response Protocol: For coordinating responses
