FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sentinel/ ./sentinel/
COPY templates/ ./templates/
COPY data/ ./data/
COPY scripts/ ./scripts/

EXPOSE 8000

# Default: run the web service. `make demo` overrides this to run the CLI.
CMD ["uvicorn", "sentinel.main:app", "--host", "0.0.0.0", "--port", "8000"]
