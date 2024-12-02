import click
import asyncio
from . import server
from .sse import starlette_app

@click.command()
@click.option('--transport', type=click.Choice(['stdio', 'sse']), default='stdio',
              help='Transport type to use (stdio or sse)')
@click.option('--port', default=8945, help='Port for SSE server (only used with sse transport)')
def main(transport: str, port: int):
    """Main entry point for the package."""
    if transport == 'stdio':
        asyncio.run(server.main())
    else:  # sse
        import uvicorn
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)

# Optionally expose other important items at package level
__all__ = ['main', 'server']