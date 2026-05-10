import runpod
import requests
import subprocess
import time
import os

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "kira"
BASE_MODEL = "nchapman/l3.3-70b-euryale-v2.3:70b"
MODELFILE_PATH = "/app/Modelfile"

def wait_for_ollama():
    for i in range(30):
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(2)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags")
        models = r.json().get("models", [])
        return any(m["name"].startswith(MODEL_NAME) for m in models)
    except:
        return False

def setup_model():
    print("Waiting for Ollama to start...")
    if not wait_for_ollama():
        raise Exception("Ollama did not start in time")
    
    if model_exists():
        print(f"Model {MODEL_NAME} already exists, skipping download.")
        return
    
    print(f"Pulling base model {BASE_MODEL}...")
    subprocess.run(["ollama", "pull", BASE_MODEL], check=True)
    
    print("Creating kira model from Modelfile...")
    subprocess.run(["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH], check=True)
    print("Kira model ready!")

def handler(job):
    job_input = job["input"]
    prompt = job_input.get("prompt", "")

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
    result = response.json()
    return {"response": result.get("response", "")}

if __name__ == "__main__":
    setup_model()
    runpod.serverless.start({"handler": handler})
