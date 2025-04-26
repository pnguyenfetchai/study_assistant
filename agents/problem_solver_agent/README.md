![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: The Problem Solver Agent is the primary solution generator in the system. It receives problems or queries, processes them using advanced AI capabilities, and generates detailed solutions. It can work both independently and in conjunction with other agents to provide comprehensive answers.

**Input Data Models**

```python
class QueryRequest(Model):
    query: str  # The problem or query to solve

class ChatMessage(Model):
    content: List[Content]  # Direct problem statements
    timestamp: datetime
    msg_id: UUID
```

**Output Data Models**

```python
class RequestResponse(Model):
    request: str   # Original problem
    response: str  # Generated solution

class ChatMessage(Model):
    content: List[TextContent]  # Solution or response
    timestamp: datetime
    msg_id: UUID
```

**Features**:

- Direct problem solving using GPT-4
- Integration with Query Agent for context-aware solutions
- Step-by-step solution generation
- Support for various problem types
- Real-time response generation

**Setup**:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Configure agent addresses
3. Set up protocol integrations

**Example Usage**:

```python
# Solve a math problem
"What is the solution to x² + 5x + 6 = 0?"

# Answer a conceptual question
"Explain how neural networks learn"

# Provide step-by-step solution
"Show me how to balance this chemical equation: H2 + O2 -> H2O"
```

**Protocol Integration**:

- Problem Protocol: For receiving solution requests
- Query Protocol: For getting additional context
- Chat Protocol: For direct user interaction
