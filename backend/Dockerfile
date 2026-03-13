FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user for production
RUN adduser --disabled-password --no-create-home appuser
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV ANALYSIS_DB_PATH=/app/analysis_app.db
ENV LOG_TO_FILE=false

# Expose port
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v3/health')"

CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
