FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src /app/src
COPY config /app/config
COPY keys /app/keys
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["python", "src/scripts/run_engine.py"]
