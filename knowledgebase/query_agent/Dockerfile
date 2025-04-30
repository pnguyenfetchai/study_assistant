FROM python:3.12.0

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY knowledgebase/query_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY knowledgebase/query_agent/ .
COPY agents/chat_protocol.py .
COPY agents/query_protocol.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "rag.py"]