import time
import os
from PIL import ImageGrab
import io
import base64

def capture_screen():
    """Captures the primary monitor screen and returns the image as a base64 string."""
    screenshot = ImageGrab.grab()
    # Resize for faster processing if needed (optional)
    # screenshot.thumbnail((800, 600))
    
    buffered = io.BytesIO()
    screenshot.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if __name__ == "__main__":
    print("Testing screen capture...")
    img_b64 = capture_screen()
    print(f"Captured screen, base64 length: {len(img_b64)}")
