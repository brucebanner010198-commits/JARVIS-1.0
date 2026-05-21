from mcp.server.fastmcp import FastMCP
import os

# Create an MCP server
mcp = FastMCP("FileServer")

# Restrict file access to a specific workspace to prevent unauthorized host access
WORKSPACE_DIR = os.path.abspath("./workspace") + os.sep
os.makedirs(WORKSPACE_DIR, exist_ok=True)

@mcp.tool()
def read_file(filename: str) -> str:
    """Read a file from the workspace."""
    filepath = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    if not filepath.startswith(WORKSPACE_DIR):
        return "Access Denied: Path outside workspace"

    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"File {filename} not found."
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def write_file(filename: str, content: str) -> str:
    """Write content to a file in the workspace."""
    filepath = os.path.abspath(os.path.join(WORKSPACE_DIR, filename))
    if not filepath.startswith(WORKSPACE_DIR):
        return "Access Denied: Path outside workspace"

    try:
        with open(filepath, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {filename}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_files() -> str:
    """List all files in the workspace."""
    try:
        files = os.listdir(WORKSPACE_DIR)
        if not files:
            return "Workspace is empty."
        return "\n".join(files)
    except Exception as e:
        return f"Error listing files: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
