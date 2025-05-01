FROM python:3.12.0

WORKDIR /app

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY agents/tools/visualization_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY agents/tools/visualization_agent/ .
COPY agents/chat_protocol.py .
COPY agents/visualization_protocol.py .
EXPOSE 8044

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "visualization_agent.py"]