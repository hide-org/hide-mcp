import anyio
import logging
import traceback
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
import mcp.types as types
from mcp.client.sse import sse_client
from mcp.server.stdio import stdio_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-proxy")


async def forward_messages(
    source: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception],
    dest: MemoryObjectSendStream[types.JSONRPCMessage],
    direction: str,
) -> None:
    """Forward messages from source to destination"""
    try:
        async for message in source:
            if isinstance(message, Exception):
                logger.error(f"Error in {direction}: {message}")
                continue
            logger.info(f"{direction}: {message}")
            await dest.send(message)
    except Exception as e:
        logger.error(f"Error forwarding {direction}: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")


async def run_proxy(remote_url: str):
    """Run the proxy, connecting stdio to SSE"""
    try:
        async with (
            stdio_server() as (stdio_read, stdio_write),
            sse_client(remote_url) as (sse_read, sse_write),
            anyio.create_task_group() as tg,
        ):
            # Forward messages in both directions
            tg.start_soon(forward_messages, stdio_read, sse_write, "client -> server")
            tg.start_soon(forward_messages, sse_read, stdio_write, "server -> client")
    except Exception as e:
        logger.error(f"Error in run_proxy: {e}")
        logger.error(f"Traceback: {''.join(traceback.format_tb(e.__traceback__))}")
        raise