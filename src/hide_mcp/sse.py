from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

from . import server

sse = SseServerTransport("/messages")


async def handle_sse(scope, receive, send):
    async with sse.connect_sse(scope, receive, send) as streams:
        await server.run_server(streams[0], streams[1])


async def handle_messages(scope, receive, send):
    await sse.handle_post_message(scope, receive, send)


starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)
