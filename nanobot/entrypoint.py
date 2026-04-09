#!/usr/bin/env python3
"""
Entrypoint for nanobot Docker container.

Resolves environment variables into config at runtime, then launches nanobot gateway
and the OpenAI-compatible HTTP API server.
"""

import json
import os
import subprocess
import sys
import threading
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

    # Write resolved config
    with open(resolved_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Using config: {resolved_path}", file=sys.stderr)

    # Run nanobot gateway using the venv's Python and nanobot CLI
    # The venv is at /app/nanobot/.venv (not overwritten by volume mounts)
    venv_python = "/app/nanobot/.venv/bin/python"

    # Start the OpenAI-compatible HTTP API server in a background thread so
    # external services (like the Telegram bot) can call nanobot via HTTP.
    gateway_port = config["gateway"]["port"]
    api_server_cmd = [
        venv_python,
        "-m",
        "nanobot",
        "serve",
        "--port",
        str(gateway_port),
        "--host",
        "0.0.0.0",
        "--config",
        str(resolved_path),
        "--workspace",
        str(workspace_path),
    ]

    def run_api_server():
        """Run the HTTP API server in a background thread."""
        subprocess.run(api_server_cmd, check=True)

    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    print(f"Started HTTP API server on 0.0.0.0:{gateway_port}", file=sys.stderr)

    # Run the gateway in the main thread (it's a long-running process)
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
