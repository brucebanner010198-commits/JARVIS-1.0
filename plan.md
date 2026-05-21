# Phase 3: The Tooling Grid & MCP Integration Plan

## 1. Environment & Dependencies Setup
* Install `mcp` via pip to support the Model Context Protocol.
* Update `requirements.txt` to include `mcp`.

## 2. Standalone MCP Server Deployment
* Create a generic FileSystem MCP server using `mcp.server.fastmcp.FastMCP` in a new file `mcp_server.py`.
* Ensure strict bounds: This tool reads/writes ONLY to a sandboxed local `./workspace` directory to prevent unauthorized host OS access. Path checks must include trailing slashes to prevent sibling directory traversal.

## 3. LiveKit Agents MCP Integration (`agent.py`)
* Use standard LiveKit 1.5.0 components verified against the installed library version (`WorkerOptions`, `JobContext`, `livekit.agents.voice.agent_session.AgentSession`, `llm.ToolContext`, `llm.function_tool`).
* Instantiate an `mcp.client.stdio.stdio_client` and connect to the MCP server persistently in the entrypoint function.
* Wrap the MCP client tool invocations using `@llm.function_tool(description="...")` inside an inline class derived from `llm.ToolContext` so that it captures the `mcp_session`. Pass arguments to `call_tool` explicitly as `arguments={"key": val}`.
* Provide the flattened tool list (`fnc_ctx.flatten()`) to the `AgentSession`.
* Run the agent logic wrapped inside the MCP context managers.

## 4. Local Execution & Testing
* Ensure the `./workspace` directory is created.
* Spin up the LiveKit environment (`docker compose up -d`).
* Start the agent daemon which spawns the MCP server locally (`python agent.py start`).
* Verify that J.A.R.V.I.S. can securely execute filesystem actions via the tool grid without latency or hallucinating APIs.
