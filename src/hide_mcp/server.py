from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import hide
from hide import model

# Store Hide client and active projects
client = hide.Client()
# projects: dict[str, model.Project] = {}

server = Server("hide-mcp")

PROJECT_ID = "FILL ME"  # default Hide project ID to use

# @server.list_resources()
# async def handle_list_resources() -> list[types.Resource]:
#     """
#     List available Hide projects as resources.
#     Each project is exposed as a resource with a hide:// URI scheme.
#     """
#     resources = []
#     for project_id, project in projects.items():
#         resources.append(
#             types.Resource(
#                 uri=AnyUrl(f"hide://projects/{project_id}"),
#                 name=f"Project: {project_id}",
#                 description=f"Hide project from {project.repository.url}",
#                 # mimeType="application/x-hide-project",
#             )
#         )
#     return resources

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools for interacting with Hide projects.
    """
    return [
        types.Tool(
            name="list_tasks",
            description="List the available tasks in the project.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="run_task", 
            description="Run a task in the project. Provide either command or alias. Set timeout in seconds. Command will be executed in the shell. For the list of available tasks and their aliases, use the `list_tasks` tool.",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "alias": {"type": "string"},
                    "timeout": {"type": "integer"},
                },
                "oneOf": [
                    {"required": ["command"]},
                    {"required": ["alias"]}
                ]
            },
        ),
        types.Tool(
            name="create_file",
            description="Create a new file in the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        ),
        types.Tool(
            name="insert_lines",
            description="Insert lines at a specific position in a file. Lines are 1-indexed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "content": {"type": "string"},
                },
                "required": ["path", "start_line", "content"],
            },
        ),
        types.Tool(
            name="replace_lines",
            description="Replace lines in a file between start (inclusive) and end (exclusive) positions. Lines are 1-indexed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "end_line": {"type": "integer"},
                    "content": {"type": "string"},
                },
                "required": ["path", "start_line", "end_line", "content"],
            },
        ),
        types.Tool(
            name="append_lines",
            description="Append lines to a file in the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        ),
        types.Tool(
            name="get_file",
            description="Read the contents of a file from the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="delete_file",
            description="Delete a file from the project",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="list_files",
            description="List all files in the project",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests for Hide operations.
    """
    if not arguments:
        arguments = {}

    match name:
        case "list_tasks":
            tasks = client.get_tasks(project_id=PROJECT_ID)
            task_list = "\n".join([f"- {task.alias}: {task.command}" for task in tasks])
            return [types.TextContent(type="text", text=f"Available tasks:\n{task_list}")]

        case "run_task":
            command = arguments.get("command")
            alias = arguments.get("alias")
            timeout = arguments.get("timeout")

            result = client.run_task(
                project_id=PROJECT_ID,
                command=command,
                alias=alias,
                timeout=timeout
            )
            return [types.TextContent(type="text", text=f"Task exited with code {result.exit_code}\nTask stdout:\n{result.stdout}\nTask stderr:\n{result.stderr}")]

        case "create_file":
            path = arguments["path"]
            content = arguments["content"]

            created_file = client.create_file(
                project_id=PROJECT_ID,
                path=path,
                content=content
            )
            return [types.TextContent(type="text", text=f"File created successfully:\n{str(created_file)}")]

        case "insert_lines":
            path = arguments["path"]
            start_line = arguments["start_line"]
            content = arguments["content"]

            file = client.get_file(project_id=PROJECT_ID, path=path)
            file = file.insert_lines(start_line, content)
            updated_file = client.update_file(
                project_id=PROJECT_ID,
                path=path,
                update=model.OverwriteUpdate(content=file.content())
            )
            return [types.TextContent(type="text", text=f"Lines inserted successfully:\n{str(updated_file)}")]

        case "replace_lines":
            path = arguments["path"]
            start_line = arguments["start_line"]
            end_line = arguments["end_line"]
            content = arguments["content"]

            file = client.get_file(project_id=PROJECT_ID, path=path)
            file = file.replace_lines(start_line, end_line, content)
            updated_file = client.update_file(
                project_id=PROJECT_ID,
                path=path,
                update=model.OverwriteUpdate(content=file.content())
            )
            return [types.TextContent(type="text", text=f"Lines replaced successfully:\n{str(updated_file)}")]

        case "append_lines":
            path = arguments["path"]
            content = arguments["content"]

            file = client.get_file(project_id=PROJECT_ID, path=path)
            file = file.append_lines(content)
            updated_file = client.update_file(
                project_id=PROJECT_ID,
                path=path,
                update=model.OverwriteUpdate(content=file.content())
            )
            return [types.TextContent(type="text", text=f"Lines appended to {path} successfully\n{str(updated_file)}")]

        case "get_file":
            path = arguments["path"]

            file_content = client.get_file(project_id=PROJECT_ID, path=path)
            return [types.TextContent(type="text", text=str(file_content))]

        case "delete_file":
            path = arguments["path"]

            deleted = client.delete_file(project_id=PROJECT_ID, file=path)
            message = f"File deleted: {path}" if deleted else f"Failed to delete file: {path}"
            return [types.TextContent(type="text", text=message)]

        case "list_files":
            files = client.list_files(project_id=PROJECT_ID, format=model.ListFilesFormat.TREE)
            if isinstance(files, list):
                file_list = "\n".join([file.path for file in files])
                return [types.TextContent(type="text", text=f"Project files:\n{file_list}")]
            return [types.TextContent(type="text", text=f"Project files:\n{files}")]

        case _:
            raise ValueError(f"Unknown tool: {name}")

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
