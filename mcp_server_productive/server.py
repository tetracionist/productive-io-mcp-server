import argparse
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, Optional, cast, Literal

import yaml
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Server metadata
server_name = "mcp-server-productive"
tag_major_version = 1
tag_minor_version = 0


class ProductiveService:
    """
    Productive.io service configuration and management.
    
    This class handles the configuration and setup of Productive.io API access
    including authentication and tool configuration.
    
    Parameters
    ----------
    service_config_file : str
        Path to the service configuration YAML file
    transport : str
        Transport for the MCP server
    api_token : str
        Productive.io API token
    org_id : str
        Productive.io organization ID
    endpoint : str, default="/productive-mcp"
        Custom endpoint path for HTTP transports
    """
    
    def __init__(
        self,
        service_config_file: Optional[str],
        transport: str,
        api_token: str,
        org_id: str,
        endpoint: str = "/productive-mcp",
    ):
        if not api_token or not org_id:
            raise ValueError("API token and organization ID are required")
        
        self.api_token = api_token
        self.org_id = org_id
        self.base_url = "https://api.productive.io/api/v2"
        self.transport = cast(
            Literal["stdio", "http", "sse", "streamable-http"], transport
        )
        self.endpoint = endpoint
        
        # Tool configuration
        self.projects_enabled = True
        self.tasks_enabled = True
        self.time_entries_enabled = True
        self.deals_enabled = True
        self.companies_enabled = True
        self.people_enabled = True
        self.pages_enabled = True
        
        # Load service configuration if provided
        if service_config_file:
            self.service_config_file = str(Path(service_config_file).expanduser().resolve())
            self.config_path_uri = Path(self.service_config_file).as_uri()
            self.unpack_service_specs()
        else:
            self.service_config_file = None
            self.config_path_uri = None
    
    def unpack_service_specs(self) -> None:
        """
        Load and parse service specifications from configuration file.
        
        Reads the YAML configuration file and extracts tool configurations.
        """
        try:
            with open(self.service_config_file, "r") as file:
                service_config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Service configuration file not found: {self.service_config_file}")
            raise
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error loading service config: {e}")
            raise
        
        try:
            tools_config = service_config.get("tools", {})
            self.projects_enabled = tools_config.get("projects", True)
            self.tasks_enabled = tools_config.get("tasks", True)
            self.time_entries_enabled = tools_config.get("time_entries", True)
            self.deals_enabled = tools_config.get("deals", True)
            self.companies_enabled = tools_config.get("companies", True)
            self.people_enabled = tools_config.get("people", True)
            self.pages_enabled = tools_config.get("pages", True)
        except Exception as e:
            print(f"Error extracting service specifications: {e}")
            raise
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls."""
        return {
            "X-Auth-Token": self.api_token,
            "X-Organization-Id": self.org_id,
            "Content-Type": "application/vnd.api+json",
        }
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to Productive API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}{endpoint}",
                headers=self.get_headers(),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to Productive API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers=self.get_headers(),
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PATCH request to Productive API"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}{endpoint}",
                headers=self.get_headers(),
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()


def get_var(var_name: str, env_var_name: str, args) -> Optional[str]:
    """
    Retrieve variable value from command line arguments or environment variables.
    
    Parameters
    ----------
    var_name : str
        The attribute name to check in the command line arguments object
    env_var_name : str
        The environment variable name to check if command line arg is not provided
    args : argparse.Namespace
        Parsed command line arguments object
    
    Returns
    -------
    Optional[str]
        The variable value if found in either source, None otherwise
    """
    if hasattr(args, var_name) and getattr(args, var_name):
        return getattr(args, var_name)
    if env_var_name in os.environ:
        return os.environ[env_var_name]
    return None


def parse_arguments():
    """Parse command line arguments once at startup."""
    parser = argparse.ArgumentParser(description="Productive.io MCP Server")
    
    parser.add_argument(
        "--api-token",
        required=False,
        help="Productive.io API token (or set PRODUCTIVE_API_TOKEN env var)",
    )
    parser.add_argument(
        "--org-id",
        required=False,
        help="Productive.io organization ID (or set PRODUCTIVE_ORG_ID env var)",
    )
    parser.add_argument(
        "--service-config-file",
        required=False,
        help="Path to service specification file",
    )
    parser.add_argument(
        "--transport",
        required=False,
        choices=["stdio", "http", "sse", "streamable-http"],
        help="Transport for the MCP server",
        default="stdio",
    )
    parser.add_argument(
        "--endpoint",
        required=False,
        help="Endpoint path for the MCP server (default: /productive-mcp)",
        default="/productive-mcp",
    )
    
    return parser.parse_args()


def create_lifespan(args):
    """Create a lifespan function with captured arguments."""
    
    @asynccontextmanager
    async def create_productive_service(
        server: FastMCP,
    ) -> AsyncIterator[ProductiveService]:
        """
        Create main entry point for the Productive.io MCP server.
        
        Uses pre-parsed command line arguments to create and configure the service.
        """
        api_token = get_var("api_token", "PRODUCTIVE_API_TOKEN", args)
        org_id = get_var("org_id", "PRODUCTIVE_ORG_ID", args)
        service_config_file = get_var("service_config_file", "SERVICE_CONFIG_FILE", args)
        endpoint = os.environ.get("PRODUCTIVE_MCP_ENDPOINT", args.endpoint)
        
        if not api_token or not org_id:
            raise ValueError(
                "API token and organization ID must be provided via arguments or environment variables"
            )
        
        productive_service = None
        try:
            productive_service = ProductiveService(
                service_config_file=service_config_file,
                transport=args.transport,
                api_token=api_token,
                org_id=org_id,
                endpoint=endpoint or args.endpoint,
            )
            
            # Initialize tools and resources
            print("Initializing tools and resources...")
            initialize_tools(productive_service, server)
            if productive_service.config_path_uri:
                initialize_resources(productive_service, server)
            
            yield productive_service
        except Exception as e:
            print(f"Error creating Productive service: {e}")
            raise
        finally:
            if productive_service is not None:
                print("Cleaning up Productive service...")
    
    return create_productive_service


def initialize_resources(productive_service: ProductiveService, server: FastMCP):
    """Initialize MCP resources."""
    
    @server.resource(productive_service.config_path_uri)
    async def get_tools_config():
        """
        Tools Specification Configuration.
        
        Provides access to the YAML tools configuration file as JSON.
        """
        try:
            with open(productive_service.service_config_file, "r") as file:
                tools_config = yaml.safe_load(file)
            return tools_config
        except Exception as e:
            print(f"Error loading tools config: {e}")
            raise


def initialize_tools(productive_service: ProductiveService, server: FastMCP):
    """Initialize all MCP tools based on service configuration."""
    
    # Helper function for summarization
    def summarize_tasks(data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize task data to reduce tokens."""
        items = data.get("data", [])
        if not isinstance(items, list):
            items = [items]
        
        summarized = []
        for item in items:
            attrs = item.get("attributes", {})
            relationships = item.get("relationships", {})
            
            summarized.append({
                "id": item.get("id"),
                "title": attrs.get("title"),
                "number": attrs.get("task_number"),
                "closed": attrs.get("closed", False),
                "due_date": attrs.get("due_date"),
                "assignee_id": (
                    relationships.get("assignee", {}).get("data", {}).get("id")
                    if relationships.get("assignee", {}).get("data")
                    else None
                ),
                "project_id": (
                    relationships.get("project", {}).get("data", {}).get("id")
                    if relationships.get("project", {}).get("data")
                    else None
                ),
            })
        
        links = data.get("links", {})
        return {
            "count": len(summarized),
            "tasks": summarized,
            "pagination": {
                "has_next": links.get("next") is not None,
                "has_prev": links.get("prev") is not None,
                "next_page": links.get("next"),
            },
            "note": "Use get_task(task_id) for full task details"
        }
    
    # Tasks tools with optimization
    if productive_service.tasks_enabled:
        
        @server.tool()
        async def count_tasks(
            project_id: Optional[str] = None,
            assignee_id: Optional[str] = None,
            closed: Optional[bool] = None,
        ) -> str:
            """
            Get the count of tasks matching filters.
            Use this FIRST before listing tasks to check if pagination is needed.
            
            Args:
                project_id: Filter by project ID
                assignee_id: Filter by assignee ID
                closed: Filter by closed status
            """
            params = {"page[number]": 1, "page[size]": 1}
            
            if project_id:
                params["filter[project_id]"] = project_id
            if assignee_id:
                params["filter[assignee_id]"] = assignee_id
            if closed is not None:
                params["filter[closed]"] = str(closed).lower()
            
            result = await productive_service.get("/tasks", params=params)
            
            # Parse last page to estimate count
            links = result.get("links", {})
            last_link = links.get("last", "")
            
            import re
            total_pages = 1
            if last_link:
                match = re.search(r'page\[number\]=(\d+)', last_link)
                if match:
                    total_pages = int(match.group(1))
            
            estimated_total = total_pages * 30  # Default page size
            
            info = {
                "estimated_total": estimated_total,
                "estimated_pages": total_pages,
                "recommendation": (
                    f"Approximately {estimated_total} tasks found. "
                    f"Recommend requesting pages 1-{min(3, total_pages)} with page_size=10 "
                    f"to stay under token limits."
                )
            }
            
            return json.dumps(info, indent=2)
        
        @server.tool()
        async def list_tasks(
            project_id: Optional[str] = None,
            assignee_id: Optional[str] = None,
            closed: Optional[bool] = None,
            page: int = 1,
            page_size: int = 10,
        ) -> str:
            """
            List tasks from Productive.io with automatic summarization.
            Returns only essential fields to minimize token usage.
            
            IMPORTANT: For projects with many tasks:
            1. First use count_tasks() to check total count
            2. Then request specific pages with page_size=10
            
            Args:
                project_id: Filter by project ID
                assignee_id: Filter by assignee ID
                closed: Filter by closed status
                page: Page number (default: 1)
                page_size: Results per page (default: 10, max: 20)
            """
            # Enforce limits
            page_size = min(page_size, 20)
            
            params = {
                "page[number]": page,
                "page[size]": page_size
            }
            
            if project_id:
                params["filter[project_id]"] = project_id
            if assignee_id:
                params["filter[assignee_id]"] = assignee_id
            if closed is not None:
                params["filter[closed]"] = str(closed).lower()
            
            result = await productive_service.get("/tasks", params=params)
            summarized = summarize_tasks(result)
            
            return json.dumps(summarized, indent=2)
        
        @server.tool()
        async def get_task(task_id: str) -> str:
            """
            Get FULL details of a specific task.
            Use this after list_tasks to get complete information for specific tasks.
            
            Args:
                task_id: The ID of the task
            """
            result = await productive_service.get(f"/tasks/{task_id}")
            return json.dumps(result, indent=2)

def main():
    args = parse_arguments()
    
    # Create server with lifespan that has access to args
    server = FastMCP("Productive.io MCP Server", lifespan=create_lifespan(args))
    
    try:
        print("Starting Productive.io MCP Server...")
        
        if args.transport and args.transport in ["http", "sse", "streamable-http"]:
            endpoint = os.environ.get("PRODUCTIVE_MCP_ENDPOINT", args.endpoint)
            print(f"Starting server with transport: {args.transport}")
            print(f"Endpoint: {endpoint}")
            print(f"URL: http://0.0.0.0:9000{endpoint}")
            server.run(
                transport=args.transport, 
                host="0.0.0.0", 
                port=9000, 
                path=endpoint
            )
        else:
            print(f"Starting server with transport: {args.transport or 'stdio'}")
            server.run(transport=args.transport or "stdio")
    
    except Exception as e:
        print(f"Error starting MCP server: {e}")
        raise


if __name__ == "__main__":
    main()