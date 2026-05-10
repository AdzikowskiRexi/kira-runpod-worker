FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl bash ca-certificates && rm -rf /var/lib/apt/lists/*

RUN curl -L https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64 -o /usr/local/bin/ollama && \
    chmod +x /usr/local/bin/ollama

RUN pip install runpod requests

COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

ENV OLLAMA_MODELS=/runpod-volume/models
ENV OLLAMA_HOST=0.0.0.0
ENV PATH=/usr/local/bin:$PATH

CMD ["/bin/bash", "-c", "ollama serve & sleep 5 && python3 /app/handler.py"]
