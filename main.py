"""
MarkItDown MCP Server - Streamable HTTP / SSE transport
Usado pelo ChatGPT Agent Builder e outros clientes MCP.

Endpoints:
  /mcp          - Streamable HTTP (principal, para ChatGPT)
  /sse          - SSE transport
  /health       - Health check
"""

import contextlib
import os
import sys

from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from mcp.server.streamable._http._manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from mcp.server import Server
import uvicorn

from markitdown import MarkItDown

# ─── MCP Server ───────────────────────────────────────────────────────────────

mcp = FastMCP("markitdown")

@mcp.tool()
async def convert_to_markdown(uri: str) -> str:
    """
    Convert a resource described by an http:, https:, file: or data: URI to markdown.

    Supports:
      - Web pages: https://example.com
      - Local files: file:///path/to/document.pdf
      - Data URIs: data:text/plain;base64,SGVsbG8=
    """
    enable_plugins = os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").strip().lower() in ("true", "1", "yes")
    return MarkItDown(enable_plugins=enable_plugins).convert_uri(uri).markdown


def check_plugins_enabled() -> bool:
    return os.getenv("MARKITDOWN_ENABLE_PLUGINS", "false").strip().lower() in ("true", "1", "yes")


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        event_store=None,
        json_response=True,
        stateless=True,
    )

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            print("Application started with MCP markitdown server")
            yield
        print("Application shutting down")

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app = create_starlette_app(mcp._server, debug=os.getenv("DEBUG", "").lower() == "true")
    uvicorn.run(app, host="0.0.0.0", port=port)
