![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: This AI Agent integrates with Canvas LMS to provide intelligent access to your course information, assignments, and materials. Using a RAG (Retrieval Augmented Generation) system, it can answer questions about your courses, track deadlines, and help you stay organized with your academic work. Simply ask questions about your courses or assignments to get relevant information.

**Input Data Model**

```python
class RequestResponse(Model):
    request: str  # The question or query about your courses
    response: str   # the response
```

**Output Data Model**

```python
class requestResponse(Model):
    request: str   # The original request
    response: str  # the response
```

**Features**:

- Real-time access to your current course enrollments
- Assignment tracking and deadline management
- Course material search and retrieval
- Intelligent question answering about your courses
- Secure Canvas API integration

**Setup**:

1. Set your Canvas API token in `.env`:
   ```
   CANVAS_TOKEN=your_canvas_token
   ```
2. Configure your school's Canvas domain
3. Set up OpenAI API key for the RAG system

**Example Usage**:

```python
# Ask about current courses
"What courses am I currently enrolled in?"

# Check assignment deadlines
"What are my upcoming assignment deadlines?"

# Search course materials
"Find materials about neural networks in my AI course"
```

**Note**: This agent requires valid Canvas API credentials and an active Canvas LMS account to function.
