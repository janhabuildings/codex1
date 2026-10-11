FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8000

WORKDIR /app
COPY server.py ./server.py
COPY resolution.py ./resolution.py
COPY dob_references.py ./dob_references.py
COPY reference_library.py ./reference_library.py
COPY review_guidance.py ./review_guidance.py
COPY mapping_worker.py ./mapping_worker.py
COPY onedrive.py ./onedrive.py
COPY mapping/ ./mapping/
COPY requirements-worker.txt ./requirements-worker.txt
COPY references/resolution.json ./references/resolution.json
COPY references/far_tables.json ./references/far_tables.json
COPY references/dob-text/ ./references/dob-text/
COPY static/ ./static/

RUN pip install --no-cache-dir -r requirements-worker.txt && python resolution.py && python dob_references.py && chmod -R a+rX /app && python -m py_compile server.py mapping_worker.py

USER 10001:10001
EXPOSE 8000
CMD ["python", "server.py"]
