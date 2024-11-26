# hide-mcp MCP server

A MCP server for Hide

## Components

### Tools

The server implements several tools for interacting with Hide projects:

- list_tasks: Lists available tasks in the project
  - Takes no arguments
  - Returns list of tasks with their aliases and commands

- run_task: Executes a task in the project
  - Takes either "command" or "alias" as required string argument
  - Optional "timeout" integer argument in seconds
  - Returns task execution results including exit code, stdout and stderr

- create_file: Creates a new file in the project
  - Takes "path" and "content" as required string arguments
  - Returns details of created file

- insert_lines: Inserts lines at a specific position in a file
  - Takes "path", "start_line" (1-indexed), and "content" as required arguments
  - Returns details of updated file

- replace_lines: Replaces lines between start and end positions in a file
  - Takes "path", "start_line", "end_line" (1-indexed), and "content" as required arguments
  - Returns details of updated file

- append_lines: Appends lines to end of a file
  - Takes "path" and "content" as required string arguments
  - Returns details of updated file

- get_file: Reads contents of a file
  - Takes "path" as required string argument
  - Returns file contents

- delete_file: Removes a file from the project
  - Takes "path" as required string argument
  - Returns deletion status

- list_files: Lists all files in the project
  - Takes no arguments
  - Returns tree view of project files

## Quickstart

### Install

#### Claude Desktop

On MacOS: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
On Windows: `%APPDATA%/Claude/claude_desktop_config.json`

<details>
  <summary>Development/Unpublished Servers Configuration</summary>
  ```
  "mcpServers": {
    "hide-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/hide-mcp",
        "run",
        "hide-mcp"
      ]
    }
  }
  ```
</details>

<details>
  <summary>Published Servers Configuration</summary>
  ```
  "mcpServers": {
    "hide-mcp": {
      "command": "uvx",
      "args": [
        "hide-mcp"
      ]
    }
  }
  ```
</details>

## Development

### Building and Publishing

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
```bash
uv sync
```

2. Build package distributions:
```bash
uv build
```

This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
```bash
uv publish
```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/hide-mcp run hide-mcp
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.