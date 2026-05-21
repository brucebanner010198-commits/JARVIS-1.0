import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io
from livekit.plugins import silero
from livekit.plugins import openai
from livekit.plugins import elevenlabs
from livekit.plugins import langchain
from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
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

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=(
                "You are J.A.R.V.I.S., an advanced AI assistant. "
                "Keep your responses concise, clear, and helpful. "
                "Be proactive, perceptive, and highly functional."
            )
        )

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")

# Define LangGraph state machine node
def call_model(state: MessagesState):
    messages = state['messages']

    # Context Injection and Memory Storage via Mem0
    if memory and messages:
        last_user_msg = next((m.content for m in reversed(messages) if m.type == "human"), None)
        if last_user_msg:
            # Add user message to memory
            memory.add(messages=last_user_msg, user_id="jarvis_user")
            # Perform vector search
            relevant_memories = memory.search(query=last_user_msg, user_id="jarvis_user")
            if relevant_memories:
                context = "\n".join([mem["memory"] for mem in relevant_memories])
                # Inject context as a system message
                system_msg = SystemMessage(content=f"Relevant historical facts:\n{context}")
                messages = [system_msg] + messages

    response = llm.invoke(messages)
    return {"messages": [response]}

# Build graph
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_edge(START, "agent")
workflow.add_edge("agent", END)
compiled_graph = workflow.compile()

server = AgentServer()

@server.rtc_session(agent_name="jarvis")
async def jarvis(ctx: agents.JobContext):

    # Phase 2: LangGraph Integration wrapped for LiveKit streaming
    llm_adapter = langchain.LLMAdapter(graph=compiled_graph)

    session = AgentSession(
        stt=openai.STT(),
        llm=llm_adapter,
        tts=elevenlabs.TTS(),
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
