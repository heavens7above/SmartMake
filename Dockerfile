FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

WORKDIR /app

# Copy requirements first to leverage cache
COPY backend/requirements.txt requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (already in base image, but good to ensure match)
RUN playwright install chromium

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Use unbuffered output for logs
ENV PYTHONUNBUFFERED=1

# Command to run the scheduler (or main pipeline)
CMD ["python", "-m", "backend.scheduler"]
