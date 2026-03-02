import os

import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL_NAME = "moondream"  # or "llava"
SCREEN_CONTEXT_UNAVAILABLE = "Screen context unavailable."
VISION_PROMPT = (
    "What is visible on this computer screen right now? "
    "Describe only concrete, visible UI/text details in 1 to 3 short sentences. "
    "If the image is unreadable, respond exactly: 'screen unreadable'."
)
VISION_RETRY_PROMPT = (
    "Describe only what is clearly visible on the screenshot in up to two short sentences. "
    "If the image is blank or unreadable, say exactly: 'screen unreadable'."
)


def _request_vision(model_name, image_b64, prompt):
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "images": [image_b64],
        "options": {
            "temperature": 0.1,
            "num_predict": 120,
        },
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    response.raise_for_status()
    return str(response.json().get("response", "") or "").strip()


def _request_vision_chat(model_name, image_b64, prompt):
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            }
        ],
        "stream": False,
    }
    response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=30)
    response.raise_for_status()
    return str(response.json().get("message", {}).get("content", "") or "").strip()


def describe_image(image_b64, prompt=VISION_PROMPT):
    """Sends an image to Ollama and returns the description."""
    model_name = os.getenv("GAMERCAT_VISION_MODEL", DEFAULT_MODEL_NAME)
    
    try:
        content = _request_vision(model_name, image_b64, prompt)
        if content and content.lower() != "screen unreadable":
            return content
        chat_content = _request_vision_chat(model_name, image_b64, prompt)
        if chat_content and chat_content.lower() != "screen unreadable":
            return chat_content
        retry_content = _request_vision(model_name, image_b64, VISION_RETRY_PROMPT)
        if not retry_content:
            retry_content = _request_vision_chat(model_name, image_b64, VISION_RETRY_PROMPT)
        if retry_content and retry_content.lower() != "screen unreadable":
            return retry_content
        if not retry_content:
            return f"{SCREEN_CONTEXT_UNAVAILABLE}: vision model returned empty output."
        return f"{SCREEN_CONTEXT_UNAVAILABLE}: {retry_content}"
    except Exception as e:
        return f"{SCREEN_CONTEXT_UNAVAILABLE}: {str(e)}"

if __name__ == "__main__":
    from screen_capture import capture_screen
    model_name = os.getenv("GAMERCAT_VISION_MODEL", DEFAULT_MODEL_NAME)
    print(f"Connecting to Ollama at {OLLAMA_URL} with model {model_name}...")
    b64 = capture_screen()
    desc = describe_image(b64)
    print(f"Description: {desc}")
