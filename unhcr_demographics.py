#!/usr/bin/env python3

import json
import signal
import sys
from typing import Any, Dict, List, Optional

import requests
import websocket


class ErrorCode:
    METHOD_NOT_FOUND = "MethodNotFound"
    INVALID_ARGUMENTS = "InvalidArguments"
    INTERNAL_ERROR = "InternalError"

class McpError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")

class UnhcrDemographicsServer:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, signum, frame):
        print("Shutting down UNHCR Demographics MCP server...", file=sys.stderr)
        self.running = False
        sys.exit(0)

    def list_tools(self) -> Dict[str, Any]:
        return {
            "tools": [{
                "name": "get_demographics",
                "description": "Fetch refugee demographic statistics from UNHCR API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "year": {"type": "integer", "description": "Year of data to fetch"},
                        "coo": {"type": "string", "description": "Country of Origin ISO3 code"},
                        "coa": {"type": "string", "description": "Country of Asylum ISO3 code"},
                        "limit": {"type": "integer", "description": "Max results", "default": 100}
                    },
                    "required": ["year"],
                    "additionalProperties": False
                }
            }]
        }

    def get_demographics(self, args: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        year = args.get("year")
        coo = args.get("coo")
        coa = args.get("coa")
        limit = args.get("limit", 100)

        if not isinstance(year, int) or year < 1950 or year > 2025:
            raise McpError(ErrorCode.INVALID_ARGUMENTS, f"Invalid year: {year}")

        try:
            response = requests.get(
                "https://api.unhcr.org/population/v1/demographics/",
                params={
                    "year": year,
                    "coo": coo.upper() if coo else None,
                    "coa": coa.upper() if coa else None,
                    "limit": limit
                },
                headers={"Accept": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            raw_data = response.json()
            print(f"Raw API response: {json.dumps(raw_data, indent=2)}", file=sys.stderr)

            data = raw_data.get("data", raw_data)
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]
                else:
                    raise ValueError("Unexpected API response format")

            return {
                "content": [{
                    "type": "text",
                    "text": json.dumps(data, indent=2) if data else "No data available"
                }]
            }
        except requests.RequestException as e:
            return {
                "content": [{"type": "text", "text": f"UNHCR API error: {str(e)}"}],
                "isError": True
            }
        except Exception as e:
            raise McpError(ErrorCode.INTERNAL_ERROR, f"Failed to fetch demographics: {str(e)}")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        request_id = request.get("id", 0)
        method = request.get("method")
        params = request.get("params", {})

        try:
            if method == "listTools":
                result = self.list_tools()
            elif method == "callTool":
                tool_name = params.get("name")
                if tool_name != "get_demographics":
                    raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Unknown tool: {tool_name}")
                result = self.get_demographics(params.get("arguments", {}))
            else:
                raise McpError(ErrorCode.METHOD_NOT_FOUND, f"Unknown method: {method}")
            return {"id": request_id, "result": result}
        except McpError as e:
            return {"id": request_id, "error": {"code": e.code, "message": e.message}}
        except Exception as e:
            return {"id": request_id, "error": {"code": ErrorCode.INTERNAL_ERROR, "message": str(e)}}

    def on_message(self, ws, message):
        print(f"Received: {message}", file=sys.stderr)
        try:
            request = json.loads(message)
            response = self.handle_request(request)
            print(f"Sending: {json.dumps(response)}", file=sys.stderr)
            ws.send(json.dumps(response))
        except Exception as e:
            error_response = {"id": 0, "error": {"code": ErrorCode.INTERNAL_ERROR, "message": str(e)}}
            print(f"Error: {str(e)}", file=sys.stderr)
            ws.send(json.dumps(error_response))

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}", file=sys.stderr)

    def on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed", file=sys.stderr)
        self.running = False

    def on_open(self, ws):
        print("WebSocket connection opened", file=sys.stderr)

    def run(self):
        print("Starting WebSocket server...", file=sys.stderr)
        ws_url = "wss://server.smithery.ai/@rvibek/mcp_demographics"
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        ws.run_forever()

if __name__ == "__main__":
    server = UnhcrDemographicsServer()
    server.run()