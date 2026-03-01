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
    while True:
        try:
            b64 = capture_screen()
            desc = describe_image(b64)
            with context_lock:
                current_context["description"] = desc
                current_context["timestamp"] = time.time()
            print(f"[AutoCapture] Screen context updated: {desc}")
        except Exception as e:
            print(f"[AutoCapture] Error: {e}")
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
