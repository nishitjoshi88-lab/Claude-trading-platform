FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY trader trader
VOLUME ["/app/data", "/app/state"]
CMD ["python", "-m", "trader", "run"]
