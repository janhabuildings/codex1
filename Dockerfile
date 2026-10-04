FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app
COPY server.py ./server.py
COPY resolution.py ./resolution.py
COPY review_guidance.py ./review_guidance.py
COPY references/resolution.json ./references/resolution.json
COPY references/far_tables.json ./references/far_tables.json
COPY static/ ./static/

RUN python resolution.py && chmod -R a+rX /app && python -m py_compile server.py

USER 10001:10001
EXPOSE 8000
CMD ["python", "server.py"]
