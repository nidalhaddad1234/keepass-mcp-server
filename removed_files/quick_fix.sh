#!/bin/bash
echo "🚀 KeePass FastMCP Server - Quick Fix"
echo "===================================="

cd /home/nidal/claude_projects/keepass-mcp-server

echo "1. Installing FastMCP..."
./venv/bin/python -m pip install fastmcp

echo "2. Reinstalling package..."
./venv/bin/python -m pip install -e .

echo "3. Testing imports..."
./venv/bin/python -c "
import sys
sys.path.insert(0, 'src')
from mcp.server.fastmcp import FastMCP
from keepass_mcp_server.fastmcp_server import KeePassFastMCPServer
print('✅ All imports successful!')
"

echo ""
echo "🎉 FastMCP is now installed!"
echo ""
echo "📋 Use this Claude Desktop config:"
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
echo "✅ Ready! Restart Claude Desktop and test."
