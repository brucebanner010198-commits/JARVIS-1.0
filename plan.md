# Phase 2: Contextual Persistence & Stateful Memory Implementation Plan

## 1. Environment & Dependencies Update
* Add requirements for state and memory management:
  * `livekit-plugins-langchain` to connect LangGraph state machines to LiveKit's `AgentSession`.
  * `langgraph` for deterministic state orchestration and tool loops.
  * `langchain-anthropic` for LLM nodes inside the LangGraph.
  * `mem0ai` as the core RAG memory layer.
  * `psycopg2-binary` to enable PostgreSQL `pgvector` connections.

## 2. Infrastructure Deployment
* Update `docker-compose.yml` to include a `pgvector` container alongside LiveKit and Redis.
  * Define environment variables (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).
  * Expose port `5432` for local python connections.

## 3. LangGraph Orchestration (`agent.py`)
* Replace the direct `anthropic.LLM()` call in `AgentSession` with `livekit.plugins.langchain.LLMAdapter(graph=compiled_graph)`.
* Define a `StateGraph` using LangGraph `MessagesState`.
* Set up a routing node that processes messages using `langchain_anthropic.ChatAnthropic` before returning them to LiveKit.

## 4. Mem0 Context Injection
* Instantiate the `Mem0` client connected to the local `pgvector` store.
* Configure the LangGraph node to add user messages to memory, then perform a vector search against Mem0 on each user input.
* Dynamically prepend the relevant historical facts invisibly into the LangGraph `SystemMessage` before executing the underlying LLM call.

## 5. Local Execution & Testing
* Start the updated infrastructure (`docker compose up -d`).
* Verify the Python logic works by executing `python agent.py start`.
