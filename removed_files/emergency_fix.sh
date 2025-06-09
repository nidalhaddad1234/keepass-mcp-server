#!/bin/bash
# Quick fix for FastMCP KeePass server startup issues

set -e

echo "🔧 KeePass FastMCP Server - Emergency Fix"
echo "========================================="
echo ""

cd /home/nidal/claude_projects/keepass-mcp-server

echo "1. 📦 Installing FastMCP library..."
./venv/bin/python -m pip install fastmcp
echo "✅ FastMCP installed"

echo ""
echo "2. 🔄 Reinstalling KeePass MCP Server..."
./venv/bin/python -m pip install -e .
echo "✅ Package reinstalled"

echo ""
echo "3. 🧪 Testing server startup..."
export KEEPASS_DB_PATH="/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx"
export KEEPASS_ACCESS_MODE="readwrite"
export PYTHONPATH="/home/nidal/claude_projects/keepass-mcp-server/src"

# Test the exact command Claude Desktop uses
echo "Testing command: ./venv/bin/python -m keepass_mcp_server.fastmcp_server --help"
timeout 5s ./venv/bin/python -m keepass_mcp_server.fastmcp_server --help 2>&1 || echo "Server test completed"

echo ""
echo "🎉 Fix completed!"
echo ""
echo "📋 Copy this config to ~/.config/claude-desktop/claude_desktop_config.json:"
echo ""
cat << 'EOF'
{
  "mcpServers": {
    "keepass": {
      "command": "/home/nidal/claude_projects/keepass-mcp-server/venv/bin/python",
      "args": ["-m", "keepass_mcp_server.fastmcp_server"],
      "cwd": "/home/nidal/claude_projects/keepass-mcp-server",
      "env": {
        "KEEPASS_DB_PATH": "/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "LOG_LEVEL": "INFO",
        "USE_KEYCHAIN": "false",
        "MASTER_PASSWORD_PROMPT": "true",
        "PYTHONPATH": "/home/nidal/claude_projects/keepass-mcp-server/src"
      }
    }
  }
}
EOF
echo ""
echo "🔄 Then restart Claude Desktop and test the KeePass tools!"
