import os
import json
import asyncio
from typing import Any

import httpx
from mcp.server import Server
from mcp import types

API_BASE = os.environ.get("GSD_API_URL", "http://localhost:8000").rstrip("/")
# Required: the GSD API rejects every request without it. Read at import so a
# missing secret crashes the pod at startup instead of 401ing on each tool call.
API_TOKEN = os.environ["API_TOKEN"]

server = Server("gsd-mcp")


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=API_BASE,
        headers={"X-API-Token": API_TOKEN},
        timeout=10.0,
    )


def _fmt(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="capture_to_inbox",
            description=(
                "Send a quick capture to the GSD inbox. "
                "Use this to record something for later processing — "
                "mirrors the Siri voice capture pipeline."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="list_tags",
            description=(
                "Return all GSD tags with UUIDs, names, and categories. "
                "Call this before creating tasks with tags."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="list_projects",
            description=(
                "Return all GSD projects with UUIDs and status. "
                "Call this before assigning tasks to a project."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="create_task",
            description=(
                "Create a next-action with full control. "
                "Use list_tags() and list_projects() first for valid UUIDs. "
                "status: inbox | active | pending | complete."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "notes": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["inbox", "active", "pending", "complete"],
                    },
                    "project_id": {"type": "string"},
                    "tag_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="create_project",
            description="Create a new GSD project (supports 2-level hierarchy via parent_id).",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "parent_id": {"type": "string"},
                },
                "required": ["name"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with _client() as client:
        if name == "capture_to_inbox":
            payload: dict = {"title": arguments["title"], "status": "inbox"}
            if notes := arguments.get("notes"):
                payload["notes"] = notes
            resp = await client.post("/next-actions", json=payload)
            resp.raise_for_status()
            return [types.TextContent(type="text", text=_fmt(resp.json()))]

        elif name == "list_tags":
            resp = await client.get("/tags")
            resp.raise_for_status()
            return [types.TextContent(type="text", text=_fmt(resp.json()))]

        elif name == "list_projects":
            resp = await client.get("/projects", params={"root_only": "false"})
            resp.raise_for_status()
            return [types.TextContent(type="text", text=_fmt(resp.json()))]

        elif name == "create_task":
            payload = {"title": arguments["title"]}
            for key in ("notes", "status", "project_id", "tag_ids"):
                if val := arguments.get(key):
                    payload[key] = val
            resp = await client.post("/next-actions", json=payload)
            resp.raise_for_status()
            return [types.TextContent(type="text", text=_fmt(resp.json()))]

        elif name == "create_project":
            payload = {"name": arguments["name"]}
            for key in ("description", "parent_id"):
                if val := arguments.get(key):
                    payload[key] = val
            resp = await client.post("/projects", json=payload)
            resp.raise_for_status()
            return [types.TextContent(type="text", text=_fmt(resp.json()))]

        else:
            raise ValueError(f"Unknown tool: {name}")


def _build_sse_app():
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
    from starlette.routing import Mount, Route

    sse = SseServerTransport("/messages/")

    # A Route, not a Mount: under Mount("/sse") the transport prefixes the
    # mount's root_path and advertises /sse/messages/, which lands back in this
    # handler instead of handle_post_message and stalls the handshake forever.
    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
        return Response()

    async def handle_health(request: Request):
        return JSONResponse({"status": "ok"})

    return Starlette(
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )


def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        import uvicorn
        uvicorn.run(_build_sse_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
    else:
        async def _run():
            from mcp.server.stdio import stdio_server
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )
        asyncio.run(_run())


if __name__ == "__main__":
    main()
