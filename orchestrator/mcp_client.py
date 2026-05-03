import os
import httpx
import json
import asyncio
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Import local MCP tools
import book_metadata_mcp.server as book_mcp

load_dotenv()

# We pull settings from env, matching Igbo Archives deployment.
MCP_URL = "https://igboarchives.com.ng/api/mcp/"
API_TOKEN = os.getenv("IGBO_ARCHIVES_TOKEN")

# Mapping of book-metadata tools to local functions
LOCAL_TOOLS = {
    "search_book": book_mcp.search_book,
    "find_book": book_mcp.find_book,
    "get_metadata": book_mcp.get_metadata,
    "get_cover": book_mcp.get_cover,
    "download_cover": book_mcp.download_cover,
    "bulk_search": book_mcp.bulk_search,
}

async def call_mcp_tool(server_name: str, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Routes MCP tool calls. 'book-metadata' calls stay local; others go to Igbo Archives.
    Includes built-in asynchronous backoff to prevent API rate limiting.
    """
    await asyncio.sleep(1.5)

    # Route to local book-metadata-mcp if requested
    if server_name == "book-metadata":
        if tool_name in LOCAL_TOOLS:
            try:
                # Local tools are synchronous and return JSON strings
                result_str = LOCAL_TOOLS[tool_name](**(arguments or {}))
                return json.loads(result_str)
            except Exception as e:
                return {"error": f"Local MCP Error ({tool_name}): {str(e)}"}
        else:
            return {"error": f"Tool '{tool_name}' not found in local book-metadata-mcp server."}

    # Otherwise, route to remote Igbo Archives server
    if not API_TOKEN:
        return {"error": "IGBO_ARCHIVES_TOKEN not found in environment."}

    headers = {
        "Authorization": f"Token {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Standard JSON-RPC payload for MCP via HTTP
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }

    try:
        # Extended timeout to 45 seconds to account for heavier payloads
        async with httpx.AsyncClient(timeout=45.0) as client:
            
            # Standard JSON-RPC call
            response = await client.post(MCP_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            if "error" in result:
                return {"error": result["error"]}
            
            # MCP response format: result -> content -> [text/json]
            content = result.get("result", {}).get("content", [])
            if content and "text" in content[0]:
                try:
                    return json.loads(content[0]["text"])
                except json.JSONDecodeError:
                    return {"raw_text": content[0]["text"]}
            
            return result.get("result", {})
            
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP Error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Network/MCP Error: {str(e)}"}
