FROM python:3.12.0

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY agents/respondent_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY agents/respondent_agent/ .
COPY agents/chat_protocol.py .
COPY agents/query_protocol.py .
COPY agents/visualization_protocol.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "respondent_agent.py"]
