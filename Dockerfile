FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y tesseract-ocr libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV TESSERACT_CMD=/usr/bin/tesseract

RUN mkdir -p /app/storage

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "10000"]
