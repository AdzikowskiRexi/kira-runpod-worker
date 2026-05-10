FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y python3 python3-pip curl && rm -rf /var/lib/apt/lists/*

RUN pip3 install runpod requests --break-system-packages

COPY Modelfile /app/Modelfile
COPY handler.py /app/handler.py

ENV OLLAMA_MODELS=/models

CMD ["/bin/bash", "-c", "ollama serve & sleep 5 && ollama pull nchapman/l3.3-70b-euryale-v2.3:70b && ollama create kira -f /app/Modelfile && python3 /app/handler.py"]
