FROM python:3.11-slim

WORKDIR /app

ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --default-timeout=300 --retries=10 -r /tmp/requirements.txt

COPY apps/api /app
COPY apps/worker/runner.py /app/worker_runner.py

CMD ["python", "worker_runner.py"]
