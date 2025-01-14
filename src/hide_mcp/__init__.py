import anyio
import click
import asyncio
from dotenv import load_dotenv

import uvicorn
from hide_mcp.server import main as server_main
from hide_mcp.sse import starlette_app
from hide_mcp.proxy import run_proxy
from hide_mcp.sandbox import create_sandbox, setup_hide_mcp


@click.group()
def main():
    """
    Main entry point for the MCP package.

    Use subcommands to run different components.
    """
    pass


@main.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type to use (stdio or sse)",
)
@click.option(
    "--port", default=8945, help="Port for SSE server (only used with sse transport)"
)
def server(transport: str, port: int):
    """
    Run the MCP server.
    """
    if transport == "stdio":
        asyncio.run(server_main())
    else:  # sse
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)


@main.command()
@click.argument("remote_url", default="http://localhost:8945/sse")
def proxy(remote_url: str):
    """
    Run an MCP proxy that forwards stdio to a remote SSE server.

    REMOTE_URL: The URL of the remote SSE server.
    """
    load_dotenv()
    anyio.run(run_proxy, remote_url)


@main.command()
@click.option(
    "--timeout",
    default=3600,
    show_default=True,
    type=int,
    help="Sandbox timeout in seconds.",
)
def sandbox(timeout: int) -> None:
    """
    Spin up a new sandbox with hide-mcp sse server.
    """
    load_dotenv()
    sbx = create_sandbox(timeout=timeout)
    try:
        setup_hide_mcp(sbx, verbose=True)
    except Exception:
        click.echo("Failed to set up the sandbox.", err=True)


if __name__ == "__main__":
    main()
