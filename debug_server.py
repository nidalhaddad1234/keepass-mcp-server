#!/usr/bin/env python3
"""
Test script to debug the KeePass MCP server issue
"""

import sys
import os
sys.path.insert(0, '/home/nidal/claude_projects/keepass-mcp-server/src')

def test_imports():
    """Test if all required modules can be imported"""
    try:
        print("Testing FastMCP import...", file=sys.stderr)
        from mcp.server.fastmcp import FastMCP
        print("✅ FastMCP import successful", file=sys.stderr)
        
        print("Testing KeePass modules...", file=sys.stderr)
        from keepass_mcp_server.config import get_config
        from keepass_mcp_server.keepass_handler import KeePassHandler
        print("✅ KeePass modules import successful", file=sys.stderr)
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}", file=sys.stderr)
        return False

def test_config():
    """Test configuration loading"""
    try:
        print("Testing configuration...", file=sys.stderr)
        
        # Set required environment variables
        os.environ['KEEPASS_DB_PATH'] = '/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx'
        os.environ['KEEPASS_ACCESS_MODE'] = 'readwrite'
        os.environ['USE_KEYCHAIN'] = 'false'
        
        from keepass_mcp_server.config import get_config
        config = get_config()
        print(f"✅ Configuration loaded: {config.database_path}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}", file=sys.stderr)
        return False

def test_fastmcp_server():
    """Test if the fixed FastMCP server can be imported"""
    try:
        print("Testing fixed FastMCP server import...", file=sys.stderr)
        import keepass_mcp_server.fastmcp_server_fixed
        print("✅ Fixed FastMCP server import successful", file=sys.stderr)
        return True
    except Exception as e:
        print(f"❌ Fixed FastMCP server import error: {e}", file=sys.stderr)
        return False

def main():
    print("=== KeePass MCP Server Debug Test ===", file=sys.stderr)
    
    # Test 1: Imports
    if not test_imports():
        return
    
    # Test 2: Configuration
    if not test_config():
        return
    
    # Test 3: Fixed server
    if not test_fastmcp_server():
        return
    
    print("✅ All tests passed! The fixed server should work.", file=sys.stderr)
    print("", file=sys.stderr)
    print("Next steps:", file=sys.stderr)
    print("1. Update your Claude Desktop config to use: keepass_mcp_server.fastmcp_server_fixed", file=sys.stderr)
    print("2. Restart Claude Desktop", file=sys.stderr)

if __name__ == "__main__":
    main()
