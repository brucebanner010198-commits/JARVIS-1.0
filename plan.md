# Phase 4: Omnipresent Vision & Desktop "God Mode" Plan

## 1. Environment & Dependencies Setup
* Add `mss` (for fast screen capture), `pyautogui` (for mouse/keyboard actuation), and `xvfbwrapper` to `requirements.txt`.
* Ensure necessary system libraries for headless environments (like `xvfb` for X11 in the sandbox) are handled if testing locally on Linux without a display.

## 2. Vision Daemon & Desktop MCP Server
* Create `desktop_mcp_server.py` using `FastMCP`.
* Wrap the `pyautogui` import and logic using `xvfbwrapper.Xvfb` if no display is detected to prevent `XauthError` and `DisplayConnectionError` crashes.
* Implement a background thread/task that uses `mss` to capture the screen at 1 FPS, keeping the last 10 frames compressed as base64 strings in a rolling buffer (`collections.deque`).
* Expose tools:
  * `get_latest_screen()`: Returns the latest frame(s) to the Vision-Language Model formatted as multimodal blocks.
  * `move_mouse(x: int, y: int)`: Smoothly moves the mouse via `PyAutoGUI`.
  * `click_mouse(button: str)`: Clicks the mouse.
  * `type_text(text: str)`: Types text via keyboard.

## 3. Agent Integration (`agent.py`)
* Connect to both the `mcp_server.py` (Filesystem) and the new `desktop_mcp_server.py` (Desktop Control) using multiple MCP `stdio_client` instances within the `entrypoint` context manager.
* Wrap the MCP client tool invocations locally inside `entrypoint` using the correct LiveKit 1.5.0 `@llm.function_tool(description="...")` decorator over normal async functions that capture the active `mcp_session`.
* Provide the list of tools directly to `llm.ToolContext` and pass the flattened tool list (`fnc_ctx.flatten()`) to `AgentSession`.
* Format visual outputs explicitly using `llm.ChatContent` elements with `llm.ImageContent(image=bytes_data)` so the Claude 3.5 Sonnet VLM can query the screen buffer.

## 4. Local Execution & Testing
* Ensure the `./workspace` directory is created.
* Spin up the LiveKit environment (`docker compose up -d`).
* Start the agent daemon which spawns the MCP servers locally (`python agent.py start`).
* Verify that J.A.R.V.I.S. can securely execute filesystem and desktop actions via the tool grid without latency or hallucinating APIs.
