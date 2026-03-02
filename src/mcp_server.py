from mcp.server.fastmcp import FastMCP
from screen_capture import capture_screen
from vision_engine import describe_image
import threading
import time

mcp = FastMCP("GamerCat")
context_lock = threading.Lock()

# Shared state for screen context
current_context = {
    "description": "Nothing yet...",
    "timestamp": 0
}

def auto_capture_loop():
    """Background thread to capture screen every 10 seconds."""
    last_error = None
    last_desc = None
    while True:
        try:
            b64 = capture_screen()
            desc = (describe_image(b64) or "").strip() or "Screen context unavailable."
            with context_lock:
                current_context["description"] = desc
                current_context["timestamp"] = time.time()
            if desc != last_desc:
                print(f"[AutoCapture] Screen context updated: {desc}")
                last_desc = desc
            last_error = None
        except Exception as e:
            error_text = str(e)
            if error_text != last_error:
                print(f"[AutoCapture] Error: {error_text}")
                last_error = error_text
        time.sleep(10)

@mcp.tool()
def get_screen_context() -> str:
    """Returns the most recent detailed screen description."""
    with context_lock:
        age = int(time.time() - current_context["timestamp"])
        desc = current_context["description"]
    return f"Last screen context ({age}s ago): {desc}"

if __name__ == "__main__":
    # Start background capture
    threading.Thread(target=auto_capture_loop, daemon=True).start()
    
    # Run MCP server
    mcp.run()
