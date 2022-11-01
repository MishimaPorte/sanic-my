# syntax=docker/dockerfile:1
FROM python:3.10.4

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

WORKDIR /app/main
CMD ["python", "main/main.py"]
