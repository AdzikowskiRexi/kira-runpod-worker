FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl bash ca-certificates python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o /usr/local/bin/ollama && \
    chmod +x /usr/local/bin/ollama

RUN pip3 install runpod requests

COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

RUN mkdir -p /root/.ollama /runpod-volume/models

ENV OLLAMA_MODELS=/runpod-volume/models
ENV OLLAMA_HOST=0.0.0.0
ENV PATH=/usr/local/bin:$PATH

CMD ["python3", "/app/handler.py"]
