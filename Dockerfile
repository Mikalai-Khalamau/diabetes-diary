FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=100 --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

COPY backend/ .
COPY frontend/ ./frontend/

EXPOSE 8000

CMD ["python", "run.py"]