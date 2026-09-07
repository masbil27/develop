FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/_work uploads/_results

ENV PORT=5000
EXPOSE 5000

# Timeout worker dinaikkan tinggi karena transkripsi rekaman panjang bisa
# butuh beberapa menit (diproses sinkron per request).
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 1800 server:app
