import time
import requests
from voice_engine import VoiceEngine
from mcp_server import current_context
from collections import deque
import random

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3"

# Memory for screen descriptions (last 3)
screen_history = deque(maxlen=3)

def get_ai_response(user_input, history, proactive=False):
    """Gets a chat response from Ollama considering the screen history."""
    context_str = "\n".join([f"- {desc}" for desc in history])
    
    system_prompt = (
        "You are 'GamerCat', a supportive, witty, and observant AI gaming buddy. "
        "You speak in short, punchy sentences. Maximum 2 sentences per response. "
        "Use the provided screen history to make relevant comments. "
        "You are offline, local, and slightly snarky but always a good friend."
    )
    
    if proactive:
        prompt = f"Recent screen events:\n{context_str}\n\nComment on what you see happening right now without being asked."
    else:
        prompt = f"Recent screen events:\n{context_str}\n\nUser says: '{user_input}'"
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    
    try:
        print(f"[AI Thinking] Requesting response for: {user_input if not proactive else 'Proactive'}")
        response = requests.post(OLLAMA_CHAT_URL, json=payload, timeout=20)
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "Meow? I lost my train of thought.")
        print(f"[AI Responded] {content}")
        return content
    except Exception as e:
        print(f"[AI Error] {str(e)}")
        return f"Brain freeze! {str(e)}"

def main():
    print("--- GamerCat: The Buddy is Online ---")
    voice = VoiceEngine()
    voice.speak("Gamer Cat is in the house! What's the plan for today?")
    
    last_processed_desc = ""
    last_proactive_time = time.time()
    
    while True:
        try:
            # Update history if screen context changed
            current_desc = current_context["description"]
            context_changed = False
            if current_desc != last_processed_desc and current_desc != "Nothing yet...":
                screen_history.append(current_desc)
                last_processed_desc = current_desc
                print(f"[History Updated] {current_desc}")
                context_changed = True

            # Listen for user input
            user_text = voice.listen(duration=4)
            
            if user_text and len(user_text.strip()) > 1:
                print(f"User (Recognized): {user_text}")
                response = get_ai_response(user_text, list(screen_history))
                voice.speak(response)
                last_proactive_time = time.time() 
            
            # Proactive comment logic
            elif context_changed and (time.time() - last_proactive_time > 30):
                if random.random() > 0.5:
                    print("[Proactive Comment Triggered]")
                    response = get_ai_response(None, list(screen_history), proactive=True)
                    voice.speak(response)
                    last_proactive_time = time.time()
            
            time.sleep(0.1) # Small sleep to be CPU friendly
            
        except KeyboardInterrupt:
            print("\nGamerCat is taking a nap. Catch ya later!")
            break
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    from threading import Thread
    from mcp_server import auto_capture_loop
    
    # Start background capture
    Thread(target=auto_capture_loop, daemon=True).start()
    
    main()
