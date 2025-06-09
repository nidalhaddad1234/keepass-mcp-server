#!/usr/bin/env python3
"""
Entry point for KeePass MCP Server when run as a module.
"""

if __name__ == "__main__":
    from .server import main
    main()
