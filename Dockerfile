FROM python:3.11-slim

WORKDIR /app

# نصب ابزارهای لازم
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "tabdeal.wsgi:application", "--bind", "0.0.0.0:8000"]
