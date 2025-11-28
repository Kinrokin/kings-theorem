FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Worker loop runs Ouroboros supervisor
CMD ["python", "scripts/run_ouroboros.py"]
