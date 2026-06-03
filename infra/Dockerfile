FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

COPY ./backend/requirements.txt /app/backend/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --retries 5 torch==2.7.1 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --retries 5 -r /app/backend/requirements.txt

COPY backend /app/backend

CMD ["sh", "-c", "alembic -c /app/backend/alembic.ini upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000"]
