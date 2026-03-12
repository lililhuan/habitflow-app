FROM python:3.11-slim

# Install system dependencies needed by flet/flutter web assets
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Flet web assets are served automatically; expose default port
EXPOSE 8080

ENV FLET_WEB=1
ENV PORT=8080
# Database stored in /tmp on ephemeral containers (or mount a volume for persistence)
ENV DATABASE_PATH=/tmp/habitflow.db

CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8080"]
