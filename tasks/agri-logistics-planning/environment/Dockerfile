FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install pinned Python dependencies
RUN pip install --no-cache-dir \
    pandas==2.2.2 \
    PyYAML==6.0.1

# Initialize environment structure
RUN mkdir -p environment/input_artifacts

# Important: We DO NOT COPY the entire build context. 
# We only copy the necessary artifacts for the agent.
# Note: orchestration scripts are handled by Harbor.

# Set workdir
WORKDIR /workspace

# (Dockerignore will handle exclusions)
COPY . /workspace

