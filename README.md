# MCP Hide

Implements Anthropic's [Model Context Protocol](https://www.anthropic.com/news/model-context-protocol) for Hide.

## Capabilities

The server implements several tools for interacting with Hide projects:

### Project Tasks

| Tool         | Description                          | Arguments                                                                                   | Returns                                            |
| ------------ | ------------------------------------ | ------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `list_tasks` | Lists available tasks in the project | None                                                                                        | List of tasks with aliases and commands            |
| `run_task`   | Executes a task in the project       | Required:<br>- `command` or `alias` (string)<br>Optional:<br>- `timeout` (integer, seconds) | Task execution results (exit code, stdout, stderr) |

### File Operations

| Tool            | Description                        | Arguments                                                                                                                          | Returns                    |
| --------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| `create_file`   | Creates a new file                 | Required:<br>- `path` (string)<br>- `content` (string)                                                                             | Created file details       |
| `insert_lines`  | Inserts lines at specific position | Required:<br>- `path` (string)<br>- `start_line` (integer, 1-indexed)<br>- `content` (string)                                      | Updated file details       |
| `replace_lines` | Replaces lines between positions   | Required:<br>- `path` (string)<br>- `start_line` (integer, 1-indexed)<br>- `end_line` (integer, 1-indexed)<br>- `content` (string) | Updated file details       |
| `append_lines`  | Appends lines to end of file       | Required:<br>- `path` (string)<br>- `content` (string)                                                                             | Updated file details       |
| `get_file`      | Reads file contents                | Required:<br>- `path` (string)                                                                                                     | File contents              |
| `delete_file`   | Removes a file                     | Required:<br>- `path` (string)                                                                                                     | Deletion status            |
| `list_files`    | Lists all project files            | None                                                                                                                               | Tree view of project files |

## Quickstart

Install [Claude Desktop](https://claude.ai/download)

Configure Claude Desktop by modifying its configuration file:

-   **MacOS**: `~/Library/Application\ Support/Claude/claude_desktop_config.json`
-   **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

#### Configuration Options

<details>
<summary>💻 Development Setup</summary>

```json
{
    "mcpServers": {
        "hide-mcp": {
            "command": "uv",
            "args": ["--directory", "/path/to/hide-mcp", "run", "hide-mcp"]
        }
    }
}
```

</details>

<details>
<summary>🚀 Production Setup</summary>

```json
{
    "mcpServers": {
        "hide-mcp": {
            "command": "uvx",
            "args": ["hide-mcp"]
        }
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

-   Token: `--token` or `UV_PUBLISH_TOKEN`
-   Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).

You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/hide-mcp run hide-mcp
```

Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
