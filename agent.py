import asyncio
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.voice.agent_session import AgentSession
from livekit.agents.voice.agent import Agent
from livekit.plugins import silero, anthropic, openai, elevenlabs
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mem0 import Memory
import os
import base64

load_dotenv(".env.local")

# Initialize Mem0 with pgvector config
config = {
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "dbname": "mem0",
            "user": "postgres",
            "password": "password",
            "host": "localhost",
            "port": 5432,
        }
    }
}
try:
    memory = Memory.from_config(config)
except Exception as e:
    print(f"Warning: Could not initialize Mem0 connected to pgvector. Proceeding without persistent memory. Error: {e}")
    memory = None

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

# Using the correct decorators and base classes for ToolContext as per SDK 1.5.0.
# ToolContext doesn't require inheritance but typically is populated via decorator or manually.
# For simplicity, we create wrapper functions and then add them to ToolContext.
# Wait, the best way in Livekit 1.5.0 is `fnc_ctx = llm.ToolContext(tools=[read_file, write_file, ...])`
# where those are decorated by @llm.function_tool

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Setup persistent MCP client sessions for this job
    fs_server_params = StdioServerParameters(command="python", args=["mcp_server.py"])
    desktop_server_params = StdioServerParameters(command="python", args=["desktop_mcp_server.py"])

    async with stdio_client(fs_server_params) as (fs_read, fs_write):
        async with ClientSession(fs_read, fs_write) as fs_session:
            await fs_session.initialize()

            async with stdio_client(desktop_server_params) as (desk_read, desk_write):
                async with ClientSession(desk_read, desk_write) as desk_session:
                    await desk_session.initialize()

                    @llm.function_tool(description="Read a file from the workspace.")
                    async def read_file(filename: str) -> str:
                        result = await fs_session.call_tool("read_file", arguments={"filename": filename})
                        return result.content[0].text

                    @llm.function_tool(description="Write content to a file in the workspace.")
                    async def write_file(filename: str, content: str) -> str:
                        result = await fs_session.call_tool("write_file", arguments={"filename": filename, "content": content})
                        return result.content[0].text

                    @llm.function_tool(description="List all files in the workspace.")
                    async def list_files() -> str:
                        result = await fs_session.call_tool("list_files", arguments={})
                        return result.content[0].text

                    @llm.function_tool(description="Returns the latest captured screen frame.")
                    async def get_latest_screen() -> list[llm.ChatContent] | str:
                        result = await desk_session.call_tool("get_latest_screen", arguments={})
                        b64_image = result.content[0].text
                        if b64_image == "No screen captured yet.":
                            return "No screen captured yet."
                        try:
                            image_data = base64.b64decode(b64_image)
                            return [
                                llm.ChatContent(type="image", image=llm.ImageContent(image=image_data)),
                                llm.ChatContent(type="text", text="Here is the latest screen capture.")
                            ]
                        except Exception as e:
                            return f"Error parsing image: {e}"

                    @llm.function_tool(description="Smoothly moves the physical mouse to the specified (X, Y) coordinates on the screen.")
                    async def move_mouse(x: int, y: int) -> str:
                        result = await desk_session.call_tool("move_mouse", arguments={"x": x, "y": y})
                        return result.content[0].text

                    @llm.function_tool(description="Clicks the physical mouse. Button can be 'left', 'right', or 'middle'.")
                    async def click_mouse(button: str = "left") -> str:
                        result = await desk_session.call_tool("click_mouse", arguments={"button": button})
                        return result.content[0].text

                    @llm.function_tool(description="Types the given text via the physical keyboard.")
                    async def type_text(text: str) -> str:
                        result = await desk_session.call_tool("type_text", arguments={"text": text})
                        return result.content[0].text

                    # Group functions into ToolContext or List of tools
                    tools = [read_file, write_file, list_files, get_latest_screen, move_mouse, click_mouse, type_text]
                    fnc_ctx = llm.ToolContext(tools=tools)

                    class Assistant(Agent):
                        def __init__(self):
                            super().__init__(
                                instructions=(
                                    "You are J.A.R.V.I.S., an advanced AI assistant. "
                                    "Keep your responses concise, clear, and helpful. "
                                    "Be proactive, perceptive, and highly functional. "
                                    "Use the provided tools to interact with the file system and desktop when requested."
                                )
                            )

                    agent_session = AgentSession(
                        vad=ctx.proc.userdata["vad"],
                        stt=openai.STT(),
                        llm=anthropic.LLM(model="claude-3-5-sonnet-20240620"),
                        tts=elevenlabs.TTS(),
                        tools=fnc_ctx.flatten()
                    )

                    await agent_session.start(agent=Assistant(), room=ctx.room)

                    await asyncio.sleep(1)
                    await agent_session.say("Systems online. I am ready.", allow_interruptions=True)

                    try:
                        await asyncio.Future()
                    except asyncio.CancelledError:
                        pass

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
