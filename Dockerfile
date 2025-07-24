FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./app/firebase/serviceAccountKey.json /app/firebase/serviceAccountKey.json


ENV GOOGLE_APPLICATION_CREDENTIALS=app/firebase/serviceAccountKey.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
