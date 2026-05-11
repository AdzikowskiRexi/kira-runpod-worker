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
model_ready = False

print(f"[STARTUP] OLLAMA_MODELS={os.environ.get('OLLAMA_MODELS', 'NOT SET')}", flush=True)
print(f"[STARTUP] BASE_MODEL={BASE_MODEL}", flush=True)

def start_ollama():
    print("[OLLAMA] Starting ollama serve...", flush=True)
    env = os.environ.copy()
    proc = subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    print(f"[OLLAMA] ollama serve PID: {proc.pid}", flush=True)
    return proc

def wait_for_ollama(retries=120, delay=3):
    print(f"[OLLAMA] Waiting for ollama to be ready (max {retries*delay}s)...", flush=True)
    for i in range(retries):
        try:
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if r.status_code == 200:
                print(f"[OLLAMA] Ready after {i*delay}s", flush=True)
                return True
        except Exception as e:
            if i % 10 == 0:
                print(f"[OLLAMA] Not ready yet ({i*delay}s): {e}", flush=True)
        time.sleep(delay)
    print("[OLLAMA] ERROR: Not ready after timeout!", flush=True)
    return False

def model_exists():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        tags = r.json().get("models", [])
        exists = any(m["name"].startswith(MODEL_NAME) for m in tags)
        print(f"[MODEL] model_exists={exists}, available={[m['name'] for m in tags]}", flush=True)
        return exists
    except Exception as e:
        print(f"[MODEL] model_exists check failed: {e}", flush=True)
        return False

def ensure_model():
    global model_ready
    if model_ready:
        print("[MODEL] Already ready, skipping init", flush=True)
        return
    
    # Check ollama binary
    try:
        result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10)
        print(f"[OLLAMA] Version: {result.stdout.strip()}", flush=True)
    except Exception as e:
        print(f"[OLLAMA] ERROR: ollama binary not found: {e}", flush=True)
        raise RuntimeError(f"ollama binary missing: {e}")
    
    start_ollama()
    
    if not wait_for_ollama():
        raise RuntimeError("Ollama not ready after 6 minutes")
    
    if not model_exists():
        print(f"[MODEL] Pulling base model {BASE_MODEL}...", flush=True)
        print("[MODEL] This may take 10-20 minutes on first run!", flush=True)
        result = subprocess.run(
            ["ollama", "pull", BASE_MODEL],
            check=True,
            capture_output=False
        )
        print(f"[MODEL] Pull complete: {result.returncode}", flush=True)
        
        print("[MODEL] Creating kira model from Modelfile...", flush=True)
        result = subprocess.run(
            ["ollama", "create", MODEL_NAME, "-f", MODELFILE_PATH],
            check=True
        )
        print(f"[MODEL] Create complete: {result.returncode}", flush=True)
    
    model_ready = True
    print("[MODEL] Model ready!", flush=True)

def handler(job):
    print(f"[HANDLER] Job received: {job.get('id', 'unknown')}", flush=True)
    try:
        ensure_model()
    except Exception as e:
        print(f"[HANDLER] ensure_model failed: {e}", flush=True)
        return {"error": str(e)}
    
    job_input = job["input"]
    prompt = job_input.get("prompt", "")
    print(f"[HANDLER] Prompt length: {len(prompt)}", flush=True)
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
            timeout=300
        )
        result = response.json().get("response", "")
        print(f"[HANDLER] Response length: {len(result)}", flush=True)
        return {"output": result}
    except Exception as e:
        print(f"[HANDLER] Generation failed: {e}", flush=True)
        return {"error": str(e)}

print("[STARTUP] Registering handler with runpod...", flush=True)
runpod.serverless.start({"handler": handler})
