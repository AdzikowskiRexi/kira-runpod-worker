import runpod
import requests
import subprocess
import time
import os

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "kira"
BASE_MODEL = "nchapman/13.3-70b-euryale-v2.3:70b"
MODELFILE_PATH = "/app/Modelfile"
model_ready = False

def start_ollama():
    env = os.environ.copy()
    subprocess.Popen(["ollama", "serve"], env=env)
    print("Ollama serve started")

def wait_for_ollama(retries=60, delay=3):
    for i in range(retries):
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if r.status_code == 200:
                print(f"Ollama ready after {i*delay}s")
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        tags = r.json().get("models", [])
        return any(m["name"].startswith(MODEL_NAME) for m in tags)
    except Exception:
        return False

def ensure_model():
    global model_ready
    if model_ready:
        return
    start_ollama()
    if not wait_for_ollama():
        raise RuntimeError("Ollama not ready after 3 minutes")
    if not model_exists():
        print("Pulling base model...")
        subprocess.run(["ollama", "pull", BASE_MODEL], check=True)
        print("Creating kira model...")
        subprocess.run(["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH], check=True)
    model_ready = True
    print("Model ready!")

def handler(job):
    ensure_model()
    job_input = job["input"]
    prompt = job_input.get("prompt", "")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=300
        )
        return {"output": response.json().get("response", "")}
    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})
