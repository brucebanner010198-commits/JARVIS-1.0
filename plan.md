# Phase 1: Zero-Latency Voice Core Implementation Plan

## 1. Environment & Dependencies Setup
* Initialize a Python environment using `uv` or `pip`.
* Create a `requirements.txt` file specifying core packages:
  * `livekit-agents` for orchestration and WebRTC transport.
  * `livekit-plugins-silero` for local Voice Activity Detection (VAD).
  * `livekit-plugins-anthropic` for routing logic to Claude 3.5 Sonnet.
  * Local STT (Faster-Whisper) and TTS (Kokoro/XTTS) will be integrated natively via LiveKit's custom plugin interface.
* Create a `.gitignore` to prevent tracking `__pycache__` and `.env` files.

## 2. Infrastructure Deployment
* Set up a `docker-compose.yml` to run a local LiveKit Server instance.
* This container will manage the WebRTC connections necessary for sub-100ms transport latency between the voice core and client interfaces.

## 3. Core Voice Agent Engine (`agent.py`)
* Use `livekit.agents.AgentSession` (Agents 1.0 standard) to orchestrate the pipeline.
* Configure the session with:
  * `vad=silero.VAD.load()` for exact millisecond speech start/stop detection.
  * `llm=anthropic.LLM()` targeting `claude-3-5-sonnet` for heavy logic routing.
* Implement the "Iron Man Mechanic": Enable barge-in logic inherently supported by the `AgentSession` loop, which flushes the TTS audio buffer upon user interruption.
* Set initial instructions defining the J.A.R.V.I.S. persona.

## 4. Local Execution & Testing
* Start the infrastructure (`docker compose up -d`).
* Start the agent daemon locally to listen for connections (`python agent.py dev`).
* Test using the built-in console mode (`python agent.py console`).
