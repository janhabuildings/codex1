FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app
COPY server.py ./server.py
COPY static/ ./static/

RUN chmod -R a+rX /app && python -m py_compile server.py

USER 10001:10001
EXPOSE 8000
CMD ["python", "server.py"]
