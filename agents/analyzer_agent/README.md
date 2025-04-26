![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: The Analyzer Agent is responsible for verifying and analyzing responses and statements. It serves as a fact-checker and quality control component in the system, evaluating the correctness of solutions and statements using advanced AI capabilities.

**Input Data Models**

```python
class RequestResponse(Model):
    request: str   # The original query or problem
    response: str  # The solution or response to verify

class ChatMessage(Model):
    content: List[Content]  # Text content for direct communication
    timestamp: datetime
    msg_id: UUID
```

**Output Data Models**

```python
class ChatMessage(Model):
    content: List[TextContent]  # Analysis results or verification
    timestamp: datetime
    msg_id: UUID

class ChatAcknowledgement(Model):
    timestamp: datetime
    acknowledged_msg_id: UUID
```

**Features**:

- Verification of problem solutions and responses
- Direct statement fact-checking
- Quality assessment of generated content
- Integration with GPT-4 for advanced analysis
- Real-time response evaluation

**Setup**:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Configure agent addresses in the code
3. Ensure proper protocol integration

**Example Usage**:

```python
# Verify a mathematical statement
"Is it correct that 3 + 3 = 6?"

# Analyze a complex response
"Verify this solution: The derivative of x² is 2x"

# Check factual accuracy
"Is it true that water boils at 100°C?"
```

**Protocol Integration**:

- Query Protocol: For internal agent communication
- Chat Protocol: For direct user interaction and verification requests
