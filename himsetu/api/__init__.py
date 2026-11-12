"""HIMSETU — REST API Package.

Provides high-performance asynchronous REST endpoints for lunar dataset ingestion,
geospatial queries, spatial feature alignment, and system health diagnostics.
"""

from himsetu.api.app import create_app

__all__ = ["create_app"]
