FROM python:3.12.0

WORKDIR /app

# Install system dependencies and cron
RUN apt-get update && apt-get install -y \
    build-essential \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY knowledgebase/query_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY knowledgebase/query_agent/ .
COPY agents/chat_protocol.py .
COPY agents/query_protocol.py .

# Set up cron job for cleanup
RUN echo "0 0 * * * cd /app && python cleanup.py >> /var/log/cron.log 2>&1" > /etc/cron.d/cleanup-cron
RUN chmod 0644 /etc/cron.d/cleanup-cron
RUN crontab /etc/cron.d/cleanup-cron
RUN touch /var/log/cron.log

EXPOSE 8045

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create directories
RUN mkdir -p course_files faiss_index

# Make start script executable
RUN chmod +x start.sh

# Start both cron and the agent
CMD ["./start.sh"]