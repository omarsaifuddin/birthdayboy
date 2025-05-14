FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Set environment variable to indicate we're in a Docker environment
ENV ENVIRONMENT=dev
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD python -c "import sys; from database import connection_pool; sys.exit(0 if connection_pool else 1)"

# Run the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"] 