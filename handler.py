import runpod
import requests
import subprocess
import time

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "kira"
BASE_MODEL = "nchapman/l3.3-70b-euryale-v2.3:70b"
MODELFILE_PATH = "/app/Modelfile"
model_ready = False

def wait_for_ollama(retries=30, delay=2):
    for _ in range(retries):
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(delay)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = r.json().get("models", [])
        return any(m["name"].startswith(MODEL_NAME) for m in models)
    except Exception:
        return False

def ensure_model():
    global model_ready
    if model_ready:
        return
    if not wait_for_ollama():
        raise RuntimeError("Ollama not ready")
    if not model_exists():
        print("Pulling base model...", flush=True)
        subprocess.run(["ollama", "pull", BASE_MODEL], check=True)
        print("Creating kira model...", flush=True)
        subprocess.run(["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH], check=True)
    print("Model ready!", flush=True)
    model_ready = True

def handler(job):
    ensure_model()
    prompt = job.get("input", {}).get("prompt", "")
    payload = {"model": MODEL_NAME, "prompt": prompt, "stream": False}
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=300)
    return {"response": r.json().get("response", "")}

runpod.serverless.start({"handler": handler})
