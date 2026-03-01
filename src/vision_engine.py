import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "moondream" # or "llava"
VISION_PROMPT = (
    "You are describing a live computer screen for a gaming assistant. "
    "Return 45 to 60 words focused on concrete, visible facts only. "
    "Prioritize: exact UI state, selected item, visible text, numbers, map names, health/ammo/resources, timers, and menus. "
    "For chess, include side to move, visible move list, clock times, and notable piece-square coordinates if readable (for example: white queen on d4). "
    "Do not guess hidden info; if unclear, say uncertain."
)

def describe_image(image_b64, prompt=VISION_PROMPT):
    """Sends an image to Ollama and returns the description."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "images": [image_b64],
        "options": {
            "temperature": 0.1,
            "num_predict": 120
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "No response from vision model.")
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

if __name__ == "__main__":
    from screen_capture import capture_screen
    print(f"Connecting to Ollama at {OLLAMA_URL} with model {MODEL_NAME}...")
    b64 = capture_screen()
    desc = describe_image(b64)
    print(f"Description: {desc}")
