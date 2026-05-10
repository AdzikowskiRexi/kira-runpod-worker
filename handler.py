import runpod
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"

def handler(job):
    job_input = job["input"]
    prompt = job_input.get("prompt", "")

    payload = {
        "model": "kira",
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json()

    return {"response": result.get("response", "")}

runpod.serverless.start({"handler": handler})
