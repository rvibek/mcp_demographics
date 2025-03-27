#!/usr/bin/env python3

import json
import signal
import sys
from typing import Any, Dict, List, Optional

import requests


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

            # Debug: Log raw response
            raw_data = response.json()
            print(f"Raw API response: {json.dumps(raw_data, indent=2)}", file=sys.stderr)

            # Adjust based on actual structure
            data = raw_data.get("data", raw_data)
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]  # Wrap single object in a list
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

    def run(self):
        print("UNHCR Demographics MCP server running on stdio", file=sys.stderr)
        while self.running:
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    print("No input received", file=sys.stderr)
                    continue
                print(f"Received request: {line}", file=sys.stderr)
                request = json.loads(line)
                response = self.handle_request(request)
                print(f"Sending response: {json.dumps(response)}", file=sys.stderr)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError:
                error_response = {"id": 0, "error": {"code": ErrorCode.INVALID_ARGUMENTS, "message": "Invalid JSON"}}
                print(f"Error: Invalid JSON - {line}", file=sys.stderr)
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {"id": 0, "error": {"code": ErrorCode.INTERNAL_ERROR, "message": str(e)}}
                print(f"Error in run loop: {str(e)}", file=sys.stderr)
                print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    server = UnhcrDemographicsServer()
    server.run()