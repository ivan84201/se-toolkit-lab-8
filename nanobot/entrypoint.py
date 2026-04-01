#!/usr/bin/env python3
"""
Entrypoint for nanobot Docker container.

Resolves environment variables into config at runtime, then launches nanobot gateway.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    # Paths
    config_path = Path("/app/nanobot/config.json")
    resolved_path = Path("/tmp/config.resolved.json")
    workspace_path = Path("/app/nanobot/workspace")

    # Read config.json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Override provider API key and base URL from env vars
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base_url = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config["providers"]["custom"]["apiKey"] = llm_api_key
    if llm_api_base_url:
        config["providers"]["custom"]["apiBase"] = llm_api_base_url
    if llm_api_model:
        config["agents"]["defaults"]["model"] = llm_api_model

    # Override gateway host/port from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host:
        config["gateway"]["host"] = gateway_host
    if gateway_port:
        config["gateway"]["port"] = int(gateway_port)

    # Override MCP server env vars (LMS backend URL and API key)
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")                                                                                                                        
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")                                                                                                                                
                                                                                                                                                                                         
    if "tools" in config and "mcpServers" in config["tools"]:                                                                                                                          
        if "lms" in config["tools"]["mcpServers"]:                                                                                                                                     
            if lms_backend_url:                                                                                                                                                        
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = (                                                                                             
                    lms_backend_url                                                                                                                                                    
                )                                                                                                                                                                      
            if lms_api_key:                                                                                                                                                            
                config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = (                                                                                                 
                    lms_api_key                                                                                                                                                        
                )

    # Configure webchat MCP server for structured UI message delivery
    nanobot_access_key = os.environ.get("NANOBOT_ACCESS_KEY")
    nanobot_gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    nanobot_gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if nanobot_access_key and nanobot_gateway_host and nanobot_gateway_port:
        ui_relay_url = f"http://{nanobot_gateway_host}:{nanobot_gateway_port}"
        if "mcp_webchat" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["mcp_webchat"] = {
                "command": "python",
                "args": ["-m", "mcp_webchat"],
                "env": {
                    "NANOBOT_UI_RELAY_URL": ui_relay_url,
                    "NANOBOT_ACCESS_KEY": nanobot_access_key
                }
            }
        else:
            config["tools"]["mcpServers"]["mcp_webchat"]["env"]["NANOBOT_UI_RELAY_URL"] = ui_relay_url
            config["tools"]["mcpServers"]["mcp_webchat"]["env"]["NANOBOT_ACCESS_KEY"] = nanobot_access_key

    # Write resolved config
    with open(resolved_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}", file=sys.stderr)

    # Run nanobot gateway using the venv's Python and nanobot CLI
    # The venv is at /app/nanobot/.venv (not overwritten by volume mounts)
    venv_python = "/app/nanobot/.venv/bin/python"
    
    subprocess.run([
        venv_python,
        "-m",
        "nanobot.cli.commands",
        "gateway",
        "--config",
        str(resolved_path),
        "--workspace",
        str(workspace_path),
    ], check=True)


if __name__ == "__main__":
    main()
