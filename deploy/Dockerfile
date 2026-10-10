FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py core.py mcp_server.py index.html styles.css app.js ./
RUN useradd --uid 10001 --create-home refundguard && mkdir /data && chown refundguard /data
USER refundguard
CMD ["python", "app.py"]
