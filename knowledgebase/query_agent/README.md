![tag:education](https://img.shields.io/badge/education-4A90E2)
![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)

**Description**: The Query Agent implements a Retrieval Augmented Generation (RAG) system for intelligent information retrieval. It maintains a knowledge base of course materials and uses advanced embedding techniques to find and provide relevant context for queries, enhancing the quality of responses throughout the system.

**Input Data Models**

```python
class QueryRequest(Model):
    query: str  # The search query or question

class RequestResponse(Model):
    request: str   # Original query
    response: str  # Retrieved context
```

**Output Data Models**

```python
class RequestResponse(Model):
    request: str   # Original query
    response: str  # Retrieved context and information

class ChatMessage(Model):
    content: List[TextContent]  # Processed information
    timestamp: datetime
    msg_id: UUID
```

**Features**:

- FAISS vector database integration
- OpenAI embeddings for semantic search
- Intelligent context retrieval
- Course material indexing
- Real-time information access

**Setup**:

1. Set your OpenAI API key in `.env`:
   ```
   OPENAI_API_KEY=your_openai_key
   ```
2. Initialize the FAISS database:
   ```python
   python initialize_rag.py
   ```
3. Configure Canvas integration for material access

**Example Usage**:

```python
# Query course materials
"Find information about neural networks"

# Get context for a problem
"Provide materials related to calculus derivatives"

# Search specific topics
"Find examples of recursion in programming"
```

**Protocol Integration**:

- Query Protocol: For handling information requests
- Canvas Protocol: For accessing course materials
- Chat Protocol: For direct information queries

**Directory Structure**:

```
knowledgebase/
├── query_agent/
│   ├── rag.py
│   ├── faiss_db/
│   └── course_files/
└── .env
```
