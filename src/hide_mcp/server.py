import logging
from dotenv import load_dotenv
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from hide_mcp.logging_utils import setup_logging
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl

from hide_mcp.sandbox import create_sandbox, setup_hide_mcp
from hide_mcp.tools.base import ToolError, ToolResult
from hide_mcp.tools.bash import BashTool
from hide_mcp.tools.edit import EditTool

# Setup logging
load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)
# Store Hide client

server = Server("hide-mcp")

edit_tool = EditTool()
bash_tool = BashTool()

# Project ID is set when a client reads resource
PROJECT_URL = None


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available Hide projects as resources.
    Each project is exposed as a resource with a hide:// URI scheme.
    """
    resources = []
    # for project in client.get_projects():
    #     resources.append(
    #         types.Resource(
    #             uri=AnyUrl(f"hide://projects/{project.id}"),
    #             name=f"{project.id} ({project.repository.url})",
    #             description=f"Hide project from {project.repository.url}",
    #             # mimeType="application/x-hide-project",
    #         )
    #     )
    resources.append(
        types.Resource(
            uri=AnyUrl("hide://projects/new"),
            name="New Hide Project",
        )
    )
    return resources


@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a Hide project."""
    global PROJECT_URL
    if str(uri).startswith("hide://projects/"):
        project_id = str(uri).split("/")[-1]
    else:
        raise ValueError(f"Unknown resource: {uri}")

    if project_id == "new":
        sbx = create_sandbox()
        url = setup_hide_mcp(sbx)
        PROJECT_URL = url
        # Access the current request context
        ctx = server.request_context
        logger.info(f"Sending notification: tools/list_changed")
        await ctx.session.send_tool_list_changed()
        return "New project"
    else:
        return f"Project {project_id}"


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
    global PROJECT_URL

    if PROJECT_URL:
        async with sse_client(PROJECT_URL) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()

                result = await session.call_tool(name, arguments)
                if result.isError:
                    if len(result.content) > 1:
                        logger.warning(
                            "Multiple contents returned in the tool error. Expected only one."
                        )
                    if not isinstance(result.content[0], types.TextContent):
                        logger.warning(
                            "Unexpected content type returned in the tool error. Expected only TextContent."
                        )
                    raise ToolError(
                        ",".join(
                            content.text
                            for content in result.content
                            if isinstance(content, types.TextContent)
                        )
                    )

                return result.content

    logger.warning("No project set. Running tool locally.")

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


async def run_server(read_stream, write_stream):
    """Run the MCP server with given streams."""
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


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await run_server(read_stream, write_stream)
