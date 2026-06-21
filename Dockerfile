FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OR-Tools, NetworkX, and PostGIS client
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY ./backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./backend/app ./app

# Copy ML models and data
COPY ./ml ./ml

# Set environment variable for models directory
ENV MODELS_DIR=/app/ml/models

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
