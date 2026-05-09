FROM python:3.11-slim

WORKDIR /workspace

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for incident response planning
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.24.3 \
    python-dateutil==2.8.2

# Create directories and copy artifacts
RUN mkdir -p /input_artifacts/incidents /logs/agent
COPY input_artifacts/ /input_artifacts/

WORKDIR /workspace
