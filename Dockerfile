FROM python:3.11-slim

LABEL maintainer="signag"

WORKDIR /app

# Install dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY version_doc.py .
COPY version.py .
COPY static/ static/
COPY templates/ templates/

# Persistent storage for settings
RUN mkdir -p /data

EXPOSE 5000

ENV SETTINGS_FILE=/data/settings.json \
    LOG_LEVEL=INFO \
    PORT=5000

# Use gunicorn for production; single worker is appropriate for this
# single-user, stateful app (connection manager is module-level).
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "60", "app:app"]
