# FastAPI model service for FA23-BDS-054.
# Jenkins runs train.py first; this image packages the freshly trained model.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Same pinned versions that Jenkins used to train the model
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py config.json ./
COPY artifacts/ artifacts/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=4)"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
