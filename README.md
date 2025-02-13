# hide-mcp MCP server

A MCP server for Hide

## Components

### Tools

The server implements two tools adapted from [Anthropic's computer-use-demo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo/computer_use_demo/tools):

#### Text Editor
For viewing and editing files. Features file viewing with line numbers, directory listing, file creation, string replacement with exact matching, line insertion, and edit history. 

#### Bash
A persistent bash shell with support for common Linux/Python packages, background processes and automatic output truncation. 

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

### Packaging

To package the service into a standalone executable:

```bash
uv run pyinstaller hide-mcp.spec
```

This will create a standalone executable in the `dist/` directory.

### Debugging

Since MCP servers run over stdio, debugging can be challenging. For the best debugging
experience, we strongly recommend using the [MCP Inspector](https://github.com/modelcontextprotocol/inspector).


You can launch the MCP Inspector via [`npm`](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) with this command:

```bash
npx @modelcontextprotocol/inspector uv --directory /path/to/hide-mcp run hide-mcp
```


Upon launching, the Inspector will display a URL that you can access in your browser to begin debugging.
