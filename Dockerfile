FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies (zstd required by ollama install.sh)
RUN apt-get update && apt-get install -y \
    curl bash ca-certificates \
    python3 python3-pip \
    libstdc++6 libgomp1 \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
RUN pip3 install runpod requests

# Copy app files
COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

# Environment variables
ENV OLLAMA_MODELS=/runpod-volume/models
ENV OLLAMA_HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

CMD ["python3", "/app/handler.py"]
