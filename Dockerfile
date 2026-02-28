FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 7860

# Install system dependencies (FAISS needs libgomp1)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Create data directory and ensure it has write permissions
RUN mkdir -p /app/backend/data && chmod -R 777 /app/backend/data

# Expose the port (Hugging Face uses 7860 by default)
EXPOSE 7860

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]
