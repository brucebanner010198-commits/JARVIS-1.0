import os
import sys

# Start xvfb before anything else if we are in headless mode
if not os.environ.get('DISPLAY'):
    try:
        from xvfbwrapper import Xvfb
        vdisplay = Xvfb()
        vdisplay.start()
        # Keep reference to avoid garbage collection closing the display
        import builtins
        builtins.vdisplay = vdisplay

        # Create an empty .Xauthority file to satisfy XauthError
        xauth_path = os.path.expanduser("~/.Xauthority")
        if not os.path.exists(xauth_path):
            open(xauth_path, 'a').close()

    except Exception as e:
        print(f"Warning: Could not start xvfb. GUI features may fail. {e}", file=sys.stderr)

from mcp.server.fastmcp import FastMCP
import mss
import pyautogui
import threading
import time
import base64
from collections import deque

mcp = FastMCP("DesktopServer")

# Buffer for the last 10 frames
# Each item is a base64 encoded string of the screenshot
SCREEN_BUFFER = deque(maxlen=10)

def screen_capture_loop():
    try:
        with mss.mss() as sct:
            while True:
                # Capture the primary monitor
                monitor = sct.monitors[0] if sct.monitors else None
                if not monitor:
                    time.sleep(1)
                    continue
                sct_img = sct.grab(monitor)
                # Compress to base64
                img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)
                base64_encoded = base64.b64encode(img_bytes).decode('utf-8')

                SCREEN_BUFFER.append(base64_encoded)
                time.sleep(1) # 1 FPS
    except Exception as e:
        print(f"Screen capture failed: {e}", file=sys.stderr)

# Start the background capture daemon
capture_thread = threading.Thread(target=screen_capture_loop, daemon=True)
capture_thread.start()

@mcp.tool()
def get_latest_screen() -> str:
    """Returns the latest captured screen frame as a base64 encoded PNG string."""
    if not SCREEN_BUFFER:
        return "No screen captured yet."
    return SCREEN_BUFFER[-1]

@mcp.tool()
def move_mouse(x: int, y: int) -> str:
    """Smoothly moves the physical mouse to the specified (X, Y) coordinates on the screen."""
    try:
        pyautogui.moveTo(x, y, duration=0.5)
        return f"Mouse moved to ({x}, {y})"
    except Exception as e:
        return f"Error moving mouse: {e}"

@mcp.tool()
def click_mouse(button: str = "left") -> str:
    """Clicks the physical mouse. Button can be 'left', 'right', or 'middle'."""
    try:
        if button not in ["left", "right", "middle"]:
            return "Invalid button. Must be 'left', 'right', or 'middle'."
        pyautogui.click(button=button)
        return f"Clicked {button} mouse button."
    except Exception as e:
        return f"Error clicking mouse: {e}"

@mcp.tool()
def type_text(text: str) -> str:
    """Types the given text via the physical keyboard."""
    try:
        pyautogui.write(text, interval=0.05)
        return f"Typed text: {text}"
    except Exception as e:
        return f"Error typing text: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
