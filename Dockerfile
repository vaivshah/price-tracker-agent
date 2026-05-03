FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies required for psycopg2 building (if using psycopg2 over psycopg2-binary, but we use binary)
# RUN apt-get update && apt-get install -y libpq-dev gcc

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
