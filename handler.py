import runpod
import requests
import subprocess
import time
import os
import sys

print("[STARTUP] handler.py starting...", flush=True)

OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "kira"
BASE_MODEL = "nchapman/l3.3-70b-euryale-v2.3:70b"
MODELFILE_PATH = "/app/Modelfile"
VOLUME_MODELS = "/runpod-volume/models"
model_ready = False

print(f"[STARTUP] OLLAMA_MODELS={os.environ.get('OLLAMA_MODELS', 'NOT SET')}", flush=True)

def setup_volume():
    """Create model directory on volume at runtime (volume is mounted now)"""
    try:
        os.makedirs(VOLUME_MODELS, exist_ok=True)
        print(f"[VOLUME] Created/confirmed: {VOLUME_MODELS}", flush=True)
    except Exception as e:
        print(f"[VOLUME] Warning - could not create {VOLUME_MODELS}: {e}", flush=True)
        print("[VOLUME] Will use default Ollama path", flush=True)

def start_ollama():
    print("[OLLAMA] Starting ollama serve...", flush=True)
    env = os.environ.copy()
    proc = subprocess.Popen(["ollama", "serve"], env=env)
    print(f"[OLLAMA] PID: {proc.pid}", flush=True)
    return proc

def wait_for_ollama(retries=120, delay=3):
    print(f"[OLLAMA] Waiting up to {retries*delay}s...", flush=True)
    for i in range(retries):
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if r.status_code == 200:
                print(f"[OLLAMA] Ready after {i*delay}s", flush=True)
                return True
        except Exception as e:
            if i % 10 == 0:
                print(f"[OLLAMA] Not ready yet ({i*delay}s)", flush=True)
        time.sleep(delay)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        tags = r.json().get("models", [])
        names = [m["name"] for m in tags]
        exists = any(n.startswith(MODEL_NAME) for n in tags)
        print(f"[MODEL] Available models: {names}", flush=True)
        return exists
    except Exception as e:
        print(f"[MODEL] Check failed: {e}", flush=True)
        return False

def ensure_model():
    global model_ready
    if model_ready:
        return

    setup_volume()

    # Check ollama binary
    try:
        r = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        print(f"[OLLAMA] Version: {r.stdout.strip()}", flush=True)
    except Exception as e:
        raise RuntimeError(f"ollama not found: {e}")

    start_ollama()

    if not wait_for_ollama():
        raise RuntimeError("Ollama not ready after timeout")

    if not model_exists():
        print(f"[MODEL] Pulling {BASE_MODEL}... (may take 10-20 min)", flush=True)
        subprocess.run(["ollama", "pull", BASE_MODEL], check=True)
        print(f"[MODEL] Creating kira from Modelfile...", flush=True)
        subprocess.run(["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH], check=True)

    model_ready = True
    print("[MODEL] Ready!", flush=True)

def handler(job):
    print(f"[HANDLER] Job: {job.get('id', '?')}", flush=True)
    try:
        ensure_model()
    except Exception as e:
        print(f"[HANDLER] Setup failed: {e}", flush=True)
        return {"error": str(e)}

    prompt = job["input"].get("prompt", "")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=300
        )
        return {"output": r.json().get("response", "")}
    except Exception as e:
        return {"error": str(e)}

print("[STARTUP] Registering handler...", flush=True)
runpod.serverless.start({"handler": handler})
