import asyncio
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, llm
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import silero, anthropic, openai, elevenlabs
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mem0 import Memory
import os

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

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Setup persistent MCP client session for this job
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            await mcp_session.initialize()

            # Note: We must create a dynamically generated wrapper that calls MCP
            class FileSystemTools(llm.ToolContext):
                @llm.function_tool(description="Read a file from the workspace.")
                async def read_file(self, filename: str) -> str:
                    result = await mcp_session.call_tool("read_file", arguments={"filename": filename})
                    return result.content[0].text

                @llm.function_tool(description="Write content to a file in the workspace.")
                async def write_file(self, filename: str, content: str) -> str:
                    result = await mcp_session.call_tool("write_file", arguments={"filename": filename, "content": content})
                    return result.content[0].text

                @llm.function_tool(description="List all files in the workspace.")
                async def list_files(self) -> str:
                    result = await mcp_session.call_tool("list_files", arguments={})
                    return result.content[0].text

            fnc_ctx = FileSystemTools()

            # Using AgentSession correctly based on v1.5 API structure
            agent_session = AgentSession(
                vad=ctx.proc.userdata["vad"],
                stt=openai.STT(),
                llm=anthropic.LLM(model="claude-3-5-sonnet-20240620"),
                tts=elevenlabs.TTS(),
                tools=fnc_ctx.flatten()
            )

            class Assistant(Agent):
                def __init__(self):
                    super().__init__(
                        instructions=(
                            "You are J.A.R.V.I.S., an advanced AI assistant. "
                            "Keep your responses concise, clear, and helpful. "
                            "Be proactive, perceptive, and highly functional. "
                            "Use the provided tools to interact with the file system when requested."
                        )
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
