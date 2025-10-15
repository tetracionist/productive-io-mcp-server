# Productive.io MCP Server

A Model Context Protocol (MCP) server that provides integration with [Productive.io](https://productive.io), enabling AI assistants like Claude to interact with your Productive.io workspace for project management, task tracking, time entries, and more.

## Features

- **Task Management**: List, filter, and retrieve task details with smart pagination
- **Project Access**: Query projects and their details
- **Time Tracking**: Manage time entries
- **Business Development**: Access deals and companies
- **Team Management**: Query people and team members
- **Knowledge Base**: Access Productive.io pages
- **Configurable Tools**: Enable/disable specific tools via YAML configuration
- **Multiple Transport Options**: stdio, HTTP, SSE, or streamable-HTTP
- **Docker Support**: Ready-to-deploy containerized setup

## Installation

### Prerequisites

- Productive.io account with API access
- Docker and Docker Compose (recommended)
- OR Python 3.12+ and [uv](https://github.com/astral-sh/uv) for local installation

### Docker Installation (Recommended)

Docker is the easiest way to get started with the Productive.io MCP server.

1. Clone the repository:
```bash
git clone https://github.com/yourusername/productive-io-mcp-server.git
cd productive-io-mcp-server
```

2. Create a `.env` file with your credentials:
```env
PRODUCTIVE_API_TOKEN=your_api_token_here
PRODUCTIVE_ORG_ID=your_organization_id_here
```

3. Build and start the server:
```bash
docker compose up -d
```

The server will be available at `http://localhost:9000/productive-mcp`

### Local Installation (Alternative)

If you prefer to run without Docker:

1. Clone the repository:
```bash
git clone https://github.com/yourusername/productive-io-mcp-server.git
cd productive-io-mcp-server
```

2. Install dependencies using uv:
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
PRODUCTIVE_API_TOKEN=your_api_token_here
PRODUCTIVE_ORG_ID=your_organization_id_here
```

To obtain your API credentials:
1. Log into your Productive.io account
2. Navigate to Settings > API
3. Generate an API token
4. Note your Organization ID from the URL or settings

### Tool Configuration (Optional)

Create a `config.yaml` file to enable/disable specific tools:

```yaml
tools:
  projects: true
  tasks: true
  time_entries: true
  deals: true
  companies: true
  people: true
  pages: true
```

## Usage

### Quick Start with Docker (Recommended)

1. Start the server using Docker Compose:
```bash
docker compose up -d
```

2. Connect Claude Desktop to the server:
```bash
claude mcp add --transport http productive http://localhost:9000/productive-mcp
```

3. That's it! You can now use Productive.io tools in Claude Desktop.

#### Managing the Docker Server

Check server status and logs:
```bash
docker compose logs -f
```

Stop the server:
```bash
docker compose down
```

Restart the server:
```bash
docker compose restart
```

### Claude Desktop Integration

#### Using Docker (Recommended)

With the Docker container running, add the server to Claude Desktop:

```bash
claude mcp add --transport http productive http://localhost:9000/productive-mcp
```

#### Using Local Installation

If running locally without Docker, you can use stdio transport:

```bash
claude mcp add productive --transport stdio --command "uv" --arg "run" --arg "python" --arg "/absolute/path/to/productive-io-mcp-server/mcp_server_productive/server.py" --arg "--transport" --arg "stdio"
```

Set environment variables:
```bash
export PRODUCTIVE_API_TOKEN=your_api_token_here
export PRODUCTIVE_ORG_ID=your_organization_id_here
```

#### Manual Configuration (Alternative)

You can also manually edit your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

For Docker/HTTP transport:
```json
{
  "mcpServers": {
    "productive": {
      "transport": "http",
      "url": "http://localhost:9000/productive-mcp"
    }
  }
}
```

For local stdio transport:
```json
{
  "mcpServers": {
    "productive": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/absolute/path/to/productive-io-mcp-server/mcp_server_productive/server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "PRODUCTIVE_API_TOKEN": "your_api_token_here",
        "PRODUCTIVE_ORG_ID": "your_organization_id_here"
      }
    }
  }
}
```

### Running Locally Without Docker

#### HTTP Transport

```bash
uv run python mcp_server_productive/server.py \
  --transport streamable-http \
  --endpoint /productive-mcp
```

The server will be available at `http://localhost:9000/productive-mcp`

#### stdio Transport

```bash
uv run python mcp_server_productive/server.py --transport stdio
```

#### With Configuration File

```bash
uv run python mcp_server_productive/server.py \
  --service-config-file config.yaml \
  --transport stdio
```

## Available Tools

### Task Management

- **`count_tasks`**: Get count of tasks matching filters (useful before pagination)
  - Filters: `project_id`, `assignee_id`, `closed`

- **`list_tasks`**: List tasks with smart pagination and summarization
  - Filters: `project_id`, `assignee_id`, `closed`
  - Parameters: `page`, `page_size` (max 20)
  - Returns: Summarized task data to reduce token usage

- **`get_task`**: Get full details of a specific task
  - Parameters: `task_id`

### More Tools Coming Soon

Additional tools for projects, time entries, deals, companies, people, and pages are being added.

## API Reference

### Command Line Arguments

```
--api-token          Productive.io API token (or use PRODUCTIVE_API_TOKEN env var)
--org-id            Organization ID (or use PRODUCTIVE_ORG_ID env var)
--service-config-file  Path to YAML configuration file
--transport         Transport type: stdio, http, sse, streamable-http (default: stdio)
--endpoint          Custom endpoint path (default: /productive-mcp)
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PRODUCTIVE_API_TOKEN` | Your Productive.io API token | Yes |
| `PRODUCTIVE_ORG_ID` | Your organization ID | Yes |
| `SERVICE_CONFIG_FILE` | Path to YAML config file | No |
| `PRODUCTIVE_MCP_ENDPOINT` | Custom endpoint path | No |

## Development

### Setting Up Development Environment

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run black mcp_server_productive/

# Lint code
uv run ruff check mcp_server_productive/
```

### Project Structure

```
productive-io-mcp-server/
├── mcp_server_productive/
│   └── server.py           # Main server implementation
├── docker/
│   └── server/
│       └── Dockerfile      # Docker container definition
├── docker-compose.yaml     # Docker Compose configuration
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Locked dependencies
└── README.md              # This file
```

## Architecture

The server is built using:
- **FastMCP**: Framework for building MCP servers
- **httpx**: Async HTTP client for Productive.io API
- **python-dotenv**: Environment variable management
- **PyYAML**: Configuration file parsing

### Key Components

- **`ProductiveService`**: Core service class handling API authentication and requests
- **Tool Initialization**: Dynamic tool registration based on configuration
- **Smart Pagination**: Automatic task summarization to reduce token usage
- **Lifespan Management**: Proper resource initialization and cleanup

## Performance Considerations

### Token Optimization

The server implements several strategies to minimize token usage:

1. **Summarized Listings**: `list_tasks` returns only essential fields
2. **Pagination Guidance**: `count_tasks` provides recommendations before large queries
3. **On-Demand Details**: `get_task` fetches full data only when needed
4. **Configurable Page Sizes**: Control how much data is returned per request

### Best Practices

1. Always use `count_tasks` before listing large datasets
2. Request small page sizes (10-20) for initial exploration
3. Use specific filters to narrow down results
4. Use `get_task` for detailed information on specific items

## Troubleshooting

### Authentication Errors

**Issue**: "API token and organization ID are required"
**Solution**: Ensure both `PRODUCTIVE_API_TOKEN` and `PRODUCTIVE_ORG_ID` are set in your environment or `.env` file

### Connection Errors

**Issue**: Cannot connect to Productive.io API
**Solution**:
- Verify your API token is valid and not expired
- Check your organization ID is correct
- Ensure you have network connectivity

### Docker Issues

**Issue**: Container fails to start
**Solution**:
- Check environment variables in `docker-compose.yaml`
- Verify the Docker image built successfully
- Check logs with `docker compose logs`

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

[Add your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Check Productive.io API documentation: https://developer.productive.io/
- Review MCP documentation: https://modelcontextprotocol.io/

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Powered by [Productive.io API](https://developer.productive.io/)
- Part of the [Model Context Protocol](https://modelcontextprotocol.io/) ecosystem
