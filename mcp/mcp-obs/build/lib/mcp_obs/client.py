"""HTTP client for VictoriaLogs and VictoriaTraces APIs."""

from __future__ import annotations

import json

import httpx

from mcp_obs.settings import ObsSettings


class ObsClient:
    """Client for querying VictoriaLogs and VictoriaTraces."""

    def __init__(self, settings: ObsSettings) -> None:
        self.victorialogs_url = settings.victorialogs_url
        self.victoriatraces_url = settings.victoriatraces_url
        self._http_client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> ObsClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def logs_search(
        self, query: str, limit: int = 100
    ) -> list[dict]:
        """Search logs using LogsQL query.
        
        VictoriaLogs returns newline-delimited JSON (stream format).
        """
        client = await self._get_client()
        url = f"{self.victorialogs_url}/select/logsql/query"
        params = {"query": query, "limit": limit}
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        # Parse newline-delimited JSON
        results = []
        for line in response.text.strip().split('\n'):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results

    async def logs_error_count(
        self, service: str | None = None, time_range: str = "1h"
    ) -> list[dict]:
        """Count errors per service over a time window."""
        client = await self._get_client()
        if service:
            query = f'_time:{time_range} service.name:"{service}" severity:ERROR'
        else:
            query = f"_time:{time_range} severity:ERROR"
        url = f"{self.victorialogs_url}/select/logsql/query"
        params = {"query": query, "limit": 1000}
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        # Parse newline-delimited JSON
        results = []
        for line in response.text.strip().split('\n'):
            if line.strip():
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        # Count errors by service
        error_counts: dict[str, int] = {}
        for entry in results:
            if isinstance(entry, dict):
                service_name = entry.get("service.name", "unknown")
                error_counts[service_name] = error_counts.get(service_name, 0) + 1
        
        return [{"service": svc, "error_count": count} for svc, count in error_counts.items()]

    async def traces_list(
        self, service: str | None = None, limit: int = 20
    ) -> list[dict]:
        """List recent traces, optionally filtered by service."""
        client = await self._get_client()
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
        params = {"limit": limit}
        if service:
            params["service"] = service
        else:
            # If no service specified, get traces without filtering
            # Use a different endpoint or approach
            url = f"{self.victoriatraces_url}/select/jaeger/api/services"
            response = await client.get(url)
            response.raise_for_status()
            services = response.json().get("data", []) if isinstance(response.json(), dict) else response.json()
            if not services:
                return []
            # Get traces from the first available service
            params = {"limit": limit, "service": services[0] if isinstance(services[0], str) else services[0].get("name", "")}
            url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
            response = await client.get(url, params=params)
        
        response.raise_for_status()
        data = response.json()
        # Jaeger API returns {"data": [...]}
        return data.get("data", []) if isinstance(data, dict) else []

    async def traces_get(self, trace_id: str) -> dict:
        """Fetch a specific trace by ID."""
        client = await self._get_client()
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces/{trace_id}"
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        # Jaeger API returns {"data": [...]}
        traces = data.get("data", []) if isinstance(data, dict) else []
        return traces[0] if traces else {}
