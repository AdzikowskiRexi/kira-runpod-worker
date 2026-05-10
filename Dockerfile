FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y python3 python3-pip curl && rm -rf /var/lib/apt/lists/*

RUN pip3 install runpod requests --break-system-packages

COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

ENV OLLAMA_MODELS=/runpod-volume/models
ENV OLLAMA_HOST=0.0.0.0

CMD ["/bin/bash", "-c", "ollama serve & sleep 3 && python3 /app/handler.py"]
