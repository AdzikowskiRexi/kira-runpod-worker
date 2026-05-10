FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

RUN pip install runpod requests

COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

ENV OLLAMA_MODELS=/runpod-volume/models
ENV OLLAMA_HOST=0.0.0.0

CMD ["/bin/bash", "-c", "ollama serve & sleep 5 && python3 /app/handler.py"]
