import json
import os
import base64

DATA_FILE = "sessions.json"

def load_sessions():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_sessions(sessions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

def image_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")