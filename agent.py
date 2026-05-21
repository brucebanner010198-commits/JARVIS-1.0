import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import silero
from livekit.plugins import anthropic
from livekit.plugins import openai
from livekit.plugins import elevenlabs

load_dotenv(".env.local")

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are J.A.R.V.I.S., an advanced AI assistant. "
                "Keep your responses concise, clear, and helpful. "
                "Be proactive, perceptive, and highly functional."
            )
        )

server = AgentServer()

@server.rtc_session(agent_name="jarvis")
async def jarvis(ctx: agents.JobContext):
    session = AgentSession(
        stt=openai.STT(), # Deepgram/Faster-Whisper abstraction
        llm=anthropic.LLM(model="claude-3-5-sonnet-20240620"),
        tts=elevenlabs.TTS(), # Kokoro/XTTS abstraction
        vad=silero.VAD.load(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
    )

    await session.generate_reply(
        instructions="Greet the user and let them know systems are online and you are ready."
    )

if __name__ == "__main__":
    agents.cli.run_app(server)
