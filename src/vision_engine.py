import requests
import json
import base64

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "moondream" # or "llava"

def describe_image(image_b64, prompt="Describe what is happening on this screen in exactly 30 words."):
    """Sends an image to Ollama and returns the description."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "images": [image_b64]
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
