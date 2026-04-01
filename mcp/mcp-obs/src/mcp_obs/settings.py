"""Settings for the observability MCP server."""

import os


class ObsSettings:
    """Configuration for VictoriaLogs and VictoriaTraces connections."""

    def __init__(self) -> None:
        self.victorialogs_url = os.environ.get(
            "NANOBOT_VICTORIALOGS_URL", "http://victorialogs:9428"
        )
        self.victoriatraces_url = os.environ.get(
            "NANOBOT_VICTORIATRACES_URL", "http://victoriatraces:10428"
        )


def resolve_settings() -> ObsSettings:
    """Resolve settings from environment variables."""
    return ObsSettings()
