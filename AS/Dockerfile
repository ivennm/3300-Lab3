FROM python:3.11-slim
WORKDIR /app
COPY as_server.py .
EXPOSE 53533/udp
CMD ["python", "-u", "as_server.py"]
