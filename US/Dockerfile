FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY us_server.py .
EXPOSE 8080
CMD ["python", "-u", "us_server.py"]
