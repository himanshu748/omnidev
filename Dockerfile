FROM python:3.12-slim

WORKDIR /app

# Install dependencies (from backend folder)
COPY backend/requirements.txt .
# Install playwright dependencies + chromium if needed, or just requirements
RUN pip install --no-cache-dir -r requirements.txt && playwright install chromium --with-deps

# Copy application code
COPY backend/app ./app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
