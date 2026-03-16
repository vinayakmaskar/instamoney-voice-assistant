FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput 2>/dev/null || true
RUN python manage.py migrate --noinput 2>/dev/null || true

EXPOSE 8080

CMD ["daphne", "-b", "0.0.0.0", "-p", "8080", "voice_chatbot.asgi:application"]
