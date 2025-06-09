"""
KeePass MCP Server - Secure credential management for AI agents.

This package provides a Model Context Protocol (MCP) server that integrates
with KeePass databases to provide secure credential retrieval and management
for AI agents and browser automation.
"""

__version__ = "1.0.0"
__author__ = "KeePass MCP Server Team"
__email__ = "support@keepass-mcp.com"

from .exceptions import (
    AuthenticationError,
    DatabaseError,
    KeePassMCPError,
    SecurityError,
    ValidationError,
)
from .keepass_handler import KeePassHandler
from .server import KeePassMCPServer

__all__ = [
    "KeePassMCPServer",
    "KeePassHandler",
    "KeePassMCPError",
    "DatabaseError",
    "AuthenticationError",
    "ValidationError",
    "SecurityError",
]
