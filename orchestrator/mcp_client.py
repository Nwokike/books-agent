import os
import httpx
import json
import asyncio
import mimetypes
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
    Supports file uploads for 'create_books' and 'create_archives'.
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

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            # --- Robust File Upload Logic ---
            if tool_name in ["create_books", "create_archives"] and "body" in (arguments or {}):
                body = arguments["body"].copy()
                
                # Check for local file paths in common media fields
                media_key = None
                media_raw = None
                for key in ["cover_image", "image", "audio", "video", "document"]:
                    if key in body and isinstance(body[key], str) and body[key].startswith("file://"):
                        media_key = key
                        media_raw = body[key]
                        break
                
                if media_key and media_raw:
                    file_path = media_raw.replace("file://", "", 1)
                    if os.path.exists(file_path):
                        # Pop the field from JSON body as it will be sent as multipart/form-data
                        body.pop(media_key)
                        
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if not mime_type:
                            mime_type = "application/octet-stream"

                        with open(file_path, "rb") as f:
                            files = {media_key: (os.path.basename(file_path), f, mime_type)}
                            
                            # Determine the correct REST endpoint
                            resource = "books" if tool_name == "create_books" else "archives"
                            rest_url = MCP_URL.replace("/api/mcp/", f"/api/v1/{resource}/")
                            
                            mp_headers = headers.copy()
                            mp_headers.pop("Content-Type", None) # httpx sets this for multipart
                            
                            # JSON-serialize nested dictionaries for multipart compatibility
                            # DRF MultiPartParser expects JSON strings for JSONField
                            for key, value in body.items():
                                if isinstance(value, dict):
                                    body[key] = json.dumps(value)
                            
                            # Send as Multipart Form Data
                            response = await client.post(rest_url, data=body, files=files, headers=mp_headers)
                            response.raise_for_status()
                            
                            resp_json = response.json()
                            item_id = resp_json.get("id") or resp_json.get("slug") or "Unknown"
                            return {"id": item_id, "raw_response": resp_json}

            # --- Standard JSON-RPC fallback ---
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
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
