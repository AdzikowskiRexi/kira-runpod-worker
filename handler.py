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

print(f"[STARTUP] OLLAMA_MODELS={os.environ.get('OLLAMA_MODELS', 'NOT SET')}", flush=True)

def setup_volume():
    try:
        os.makedirs(VOLUME_MODELS, exist_ok=True)
        print(f"[VOLUME] Created: {VOLUME_MODELS}", flush=True)
    except Exception as e:
        print(f"[VOLUME] Warning: {e}", flush=True)

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
        except Exception:
            if i % 10 == 0:
                print(f"[OLLAMA] Not ready yet ({i*delay}s)", flush=True)
        time.sleep(delay)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        tags = r.json().get("models", [])
        names = [m["name"] for m in tags]
        exists = any(n.startswith(MODEL_NAME) for n in names)
        print(f"[MODEL] Available: {names}, kira exists: {exists}", flush=True)
        return exists
    except Exception as e:
        print(f"[MODEL] Check failed: {e}", flush=True)
        return False

def init_model():
    """Called at startup - before any requests come in"""
    setup_volume()

    try:
        r = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        print(f"[OLLAMA] Version: {r.stdout.strip()}", flush=True)
    except Exception as e:
        print(f"[OLLAMA] ERROR: binary missing: {e}", flush=True)
        sys.exit(1)

    start_ollama()

    if not wait_for_ollama():
        print("[OLLAMA] ERROR: timeout waiting for ollama", flush=True)
        sys.exit(1)

    if not model_exists():
        print(f"[MODEL] Pulling {BASE_MODEL}...", flush=True)
        result = subprocess.run(["ollama", "pull", BASE_MODEL], check=True)
        print(f"[MODEL] Pull done: {result.returncode}", flush=True)
        print("[MODEL] Creating kira...", flush=True)
        result = subprocess.run(
            ["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH], check=True
        )
        print(f"[MODEL] Create done: {result.returncode}", flush=True)

    print("[MODEL] Model ready!", flush=True)

def handler(job):
    print(f"[HANDLER] Job: {job.get('id', '?')}", flush=True)
    prompt = job["input"].get("prompt", "")
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=300
        )
        result = r.json().get("response", "")
        print(f"[HANDLER] Response length: {len(result)}", flush=True)
        return {"output": result}
    except Exception as e:
        print(f"[HANDLER] Error: {e}", flush=True)
        return {"error": str(e)}

# Initialize model at startup (before accepting requests)
print("[STARTUP] Initializing model...", flush=True)
init_model()
print("[STARTUP] Starting runpod handler...", flush=True)
runpod.serverless.start({"handler": handler})
