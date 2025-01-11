from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

from hide_mcp import server

sse = SseServerTransport("/messages")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run_server(streams[0], streams[1])


async def handle_messages(request):
    # TODO: remove this hack once https://github.com/modelcontextprotocol/python-sdk/pull/83 is merged
    # Create a dummy response that we'll return to Starlette
    from starlette.responses import Response

    response = Response("", status_code=202)

    async def send_wrapper(message):
        # Skip sending response since we're handling it at the Starlette level
        if (
            message["type"] != "http.response.start"
            and message["type"] != "http.response.body"
        ):
            await request._send(message)

    await sse.handle_post_message(request.scope, request.receive, send_wrapper)
    return response


starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)
