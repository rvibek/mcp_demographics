# UNHCR Demographics MCP Server

A Model Context Protocol (MCP) server for accessing UNHCR refugee demographic statistics.

## Features

- Provides a `get_demographics` tool to fetch refugee statistics from UNHCR API
- Supports filtering by year, country of origin (COO), and country of asylum (COA)
- Returns data in JSON format

## Requirements

- Python 3.x
- `requests` package

## Installation

1. Install dependencies:
```bash
pip install requests
```

2. Run the server:
```bash
python unhcr_demographics.py
```

## Usage

The server provides one tool:

### get_demographics

Fetch refugee demographic statistics from UNHCR API.

**Parameters:**
- `year` (required): Year of data to fetch (1950-2025)
- `coo` (optional): Country of Origin ISO3 code
- `coa` (optional): Country of Asylum ISO3 code  
- `limit` (optional): Maximum results to return (default: 100)

**Example Request:**
```json
{
  "method": "callTool",
  "params": {
    "name": "get_demographics",
    "arguments": {
      "year": 2023,
      "coo": "SYR",
      "limit": 50
    }
  }
}
```

## License

MIT
