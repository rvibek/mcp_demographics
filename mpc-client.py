#!/usr/bin/env python3
import json
import subprocess
import sys


class McpClient:
    def __init__(self, server_path: str):
        self.process = subprocess.Popen(
            [server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  # Line-buffered
        )
        # Print initial server output (e.g., "running on stdio")
        print(self.process.stderr.readline().strip(), file=sys.stderr)

    def send_request(self, request: dict) -> dict:
        # Send request to server's stdin
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()

        # Read response from server's stdout
        response_line = self.process.stdout.readline().strip()
        return json.loads(response_line)

    def close(self):
        self.process.terminate()

if __name__ == "__main__":
    client = McpClient("./unhcr_demographics.py")

    # Test listTools
    request = {"method": "listTools", "id": 1}
    response = client.send_request(request)
    print("List Tools Response:", json.dumps(response, indent=2))

    # Test get_demographics
    request = {
        "method": "callTool",
        "id": 2,
        "params": {"name": "get_demographics", "arguments": {"year": 2022}}
    }
    response = client.send_request(request)
    print("Get Demographics Response:", json.dumps(response, indent=2))

    client.close()