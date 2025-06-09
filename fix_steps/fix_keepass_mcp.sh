#!/bin/bash
# Make this script executable: chmod +x fix_keepass_mcp.sh
# Step-by-step fix for KeePass MCP server

set -e

echo "=== KeePass MCP Server Fix Process ==="
echo ""

# Step 1: Test current setup
echo "Step 1: Testing current setup..."
cd /home/nidal/claude_projects/keepass-mcp-server
source venv/bin/activate

export PYTHONPATH="/home/nidal/claude_projects/keepass-mcp-server/src"
export KEEPASS_DB_PATH="/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx"
export KEEPASS_ACCESS_MODE="readwrite"
export USE_KEYCHAIN="false"

python debug_server.py
echo ""

# Step 2: Show current Claude config
echo "Step 2: Current Claude Desktop configuration:"
echo "Please check your current config:"
echo "cat ~/.config/claude-desktop/claude_desktop_config.json"
echo ""

# Step 3: Create the correct config
echo "Step 3: Creating correct configuration..."
cat > claude_config_correct.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/nidal/currency-exchange",
        "/home/nidal/claude_projects"
      ]
    },
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase@latest",
        "--access-token",
        "sbp_4d1a6b02c371927b1a27cbc82489ed1c87d88b26"
      ]
    },
    "keepass": {
      "command": "/home/nidal/claude_projects/keepass-mcp-server/venv/bin/python",
      "args": ["-m", "keepass_mcp_server.fastmcp_server_fixed"],
      "cwd": "/home/nidal/claude_projects/keepass-mcp-server",
      "env": {
        "KEEPASS_DB_PATH": "/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "KEEPASS_AUTO_SAVE": "true",
        "KEEPASS_BACKUP_DIR": "/home/nidal/claude_projects/keepass-mcp-server/backups",
        "KEEPASS_BACKUP_COUNT": "10",
        "KEEPASS_SESSION_TIMEOUT": "3600",
        "KEEPASS_AUTO_LOCK": "1800",
        "LOG_LEVEL": "INFO",
        "AUDIT_LOG": "true",
        "USE_KEYCHAIN": "false",
        "MASTER_PASSWORD_PROMPT": "true",
        "MAX_RETRIES": "3",
        "CACHE_TIMEOUT": "300",
        "MAX_CONCURRENT_OPERATIONS": "5",
        "PYTHONPATH": "/home/nidal/claude_projects/keepass-mcp-server/src"
      }
    }
  }
}
EOF

echo "✅ Created claude_config_correct.json"
echo ""

# Step 4: Test the fixed server
echo "Step 4: Testing the fixed server..."
echo "Testing: python -m keepass_mcp_server.fastmcp_server_fixed"
timeout 5s python -m keepass_mcp_server.fastmcp_server_fixed 2>&1 || echo "Server test completed (timeout expected)"
echo ""

echo "=== MANUAL STEPS REQUIRED ==="
echo ""
echo "1. Copy the correct configuration:"
echo "   cp /home/nidal/claude_projects/keepass-mcp-server/claude_config_correct.json ~/.config/claude-desktop/claude_desktop_config.json"
echo ""
echo "2. Kill Claude Desktop:"
echo "   pkill -f claude-desktop"
echo ""
echo "3. Wait a few seconds:"
echo "   sleep 5"
echo ""
echo "4. Start Claude Desktop:"
echo "   claude-desktop &"
echo ""
echo "5. Check for 'PROVIDED TOOLS: 16 tools' in Claude"
echo ""

echo "=== TROUBLESHOOTING ==="
echo ""
echo "If still having issues, run:"
echo "python -m keepass_mcp_server.fastmcp_server_fixed 2>&1 | head -10"
echo ""
echo "The output should ONLY show logs to stderr, NO stdout text."
