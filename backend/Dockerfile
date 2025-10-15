FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python to unbuffered mode for immediate log output
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Verify run.py exists and is executable
RUN ls -la run.py

# Run the application (run.py handles migrations, seeding, and starts uvicorn)
CMD ["python", "-u", "run.py"]
