from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import hide
from pydantic import AnyUrl

from hide_mcp.tools.base import ToolError, ToolResult
from hide_mcp.tools.bash import BashTool
from hide_mcp.tools.edit import EditTool

# Store Hide client
client = hide.Client()

server = Server("hide-mcp")

edit_tool = EditTool()
bash_tool = BashTool()

# Project ID is set when a client reads resource
PROJECT_ID = None


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available Hide projects as resources.
    Each project is exposed as a resource with a hide:// URI scheme.
    """
    resources = []
    for project in client.get_projects():
        resources.append(
            types.Resource(
                uri=AnyUrl(f"hide://projects/{project.id}"),
                name=f"{project.id} ({project.repository.url})",
                description=f"Hide project from {project.repository.url}",
                # mimeType="application/x-hide-project",
            )
        )
    return resources


@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a Hide project."""
    global PROJECT_ID
    if str(uri).startswith("hide://projects/"):
        project_id = str(uri).split("/")[-1]
    else:
        raise ValueError(f"Unknown resource: {uri}")

    try:
        project = client.get_project(project_id)
        PROJECT_ID = project_id
        return f"This project is powered by Hide, a headless IDE for coding agents. Docs at hide.sh.\n\nProject: {project.id}\nRepository: {project.repository.url}"
    except Exception as e:
        raise RuntimeError(f"Error reading project: {str(e)}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools for interacting with Hide projects.
    """
    return [
        types.Tool(
            name=bash_tool.to_params()["name"],
            description=bash_tool.to_params()["description"],
            inputSchema=bash_tool.to_params()["inputSchema"],
        ),
        types.Tool(
            name=edit_tool.to_params()["name"],
            description=edit_tool.to_params()["description"],
            inputSchema=edit_tool.to_params()["inputSchema"],
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Hide operations.
    """
    # if not PROJECT_ID:
    #     raise ValueError("No project ID set. Please select a project resource first.")

    if not arguments:
        arguments = {}

    match name:
        case edit_tool.name:
            result = await edit_tool(**arguments)
            if result.error:
                result_text = _maybe_prepend_system_tool_result(result, result.error)
                raise ToolError(result_text)
            result_text = _maybe_prepend_system_tool_result(result, result.output or "")
            return [types.TextContent(type="text", text=result_text)]

        case bash_tool.name:
            result = await bash_tool(**arguments)
            if result.error:
                result_text = _maybe_prepend_system_tool_result(result, result.error)
                raise ToolError(result_text)
            result_text = _maybe_prepend_system_tool_result(result, result.output or "")
            return [types.TextContent(type="text", text=result_text)]

        case _:
            raise ValueError(f"Unknown tool: {name}")


def _maybe_prepend_system_tool_result(result: ToolResult, result_text: str):
    if result.system:
        result_text = f"<system>{result.system}</system>\n{result_text}"
    return result_text


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="hide-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
