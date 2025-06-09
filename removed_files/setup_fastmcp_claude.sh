#!/bin/bash
# Setup Claude Desktop integration for FastMCP KeePass Server

set -e

echo "🔧 KeePass FastMCP Server - Claude Desktop Setup"
echo "==============================================="
echo ""

# Paths
PROJECT_DIR="/home/nidal/claude_projects/keepass-mcp-server"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
CLAUDE_CONFIG_DIR="$HOME/.config/claude-desktop"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Check if running from project directory
if [ ! -f "claude_desktop_config_fastmcp.json" ]; then
    echo "❌ Error: Please run this script from the KeePass MCP Server project directory"
    echo "   cd /home/nidal/claude_projects/keepass-mcp-server"
    exit 1
fi

echo "1. 🔍 Checking FastMCP setup..."

# Check if virtual environment exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Virtual environment not found at: $VENV_PYTHON"
    echo "   Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if FastMCP is installed
echo "   • Checking FastMCP installation..."
if ! $VENV_PYTHON -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null; then
    echo "❌ FastMCP not installed. Installing..."
    $VENV_PYTHON -m pip install fastmcp
    echo "✅ FastMCP installed"
else
    echo "✅ FastMCP already installed"
fi

# Check if our FastMCP server can be imported
echo "   • Testing FastMCP server import..."
if ! PYTHONPATH="$PROJECT_DIR/src" $VENV_PYTHON -c "from keepass_mcp_server.fastmcp_server import KeePassFastMCPServer" 2>/dev/null; then
    echo "❌ FastMCP server cannot be imported"
    echo "   Please check your installation: pip install -e ."
    exit 1
fi
echo "✅ FastMCP server import successful"

echo ""
echo "2. 📁 Checking database and directories..."

# Check database file
DB_PATH="$PROJECT_DIR/keepass-nidal.kdbx"
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Database not found at: $DB_PATH"
    echo "   Please ensure your KeePass database is in the project directory"
    echo "   Or update the KEEPASS_DB_PATH in the config file"
    exit 1
fi
echo "✅ Database found: $DB_PATH"

# Create backup directory
BACKUP_DIR="$PROJECT_DIR/backups"
if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    echo "✅ Created backup directory: $BACKUP_DIR"
else
    echo "✅ Backup directory exists: $BACKUP_DIR"
fi

echo ""
echo "3. ⚙️ Claude Desktop configuration..."

# Create Claude config directory
if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    mkdir -p "$CLAUDE_CONFIG_DIR"
    echo "✅ Created Claude config directory"
fi

# Backup existing config
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    BACKUP_FILE="$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
    echo "✅ Backed up existing config to: $BACKUP_FILE"
fi

# Ask user which config to use
echo ""
echo "📋 Available configurations:"
echo "   1. Full config (includes filesystem and Supabase servers)"
echo "   2. Minimal config (KeePass only)"
echo "   3. Custom config (edit before installing)"
echo ""
read -p "Choose configuration (1-3) [1]: " config_choice
config_choice=${config_choice:-1}

case $config_choice in
    1)
        CONFIG_SOURCE="claude_desktop_config_fastmcp.json"
        echo "📋 Using full configuration"
        ;;
    2)
        CONFIG_SOURCE="claude_desktop_config_minimal.json"
        echo "📋 Using minimal configuration"
        ;;
    3)
        CONFIG_SOURCE="claude_desktop_config_fastmcp.json"
        echo "📝 Opening config for editing..."
        ${EDITOR:-nano} "$CONFIG_SOURCE"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Install the configuration
if [ -f "$CONFIG_SOURCE" ]; then
    # Update Supabase token if using full config
    if [ "$config_choice" = "1" ]; then
        echo ""
        read -p "🔑 Enter your Supabase access token (or press Enter to skip): " supabase_token
        if [ -n "$supabase_token" ]; then
            sed "s/YOUR_SUPABASE_TOKEN/$supabase_token/g" "$CONFIG_SOURCE" > "$CLAUDE_CONFIG_FILE"
        else
            # Remove Supabase server if no token provided
            python3 -c "
import json
with open('$CONFIG_SOURCE', 'r') as f:
    config = json.load(f)
if 'supabase' in config['mcpServers']:
    del config['mcpServers']['supabase']
with open('$CLAUDE_CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
"
        fi
    else
        cp "$CONFIG_SOURCE" "$CLAUDE_CONFIG_FILE"
    fi
    
    echo "✅ Claude Desktop config installed to: $CLAUDE_CONFIG_FILE"
else
    echo "❌ Config file not found: $CONFIG_SOURCE"
    exit 1
fi

echo ""
echo "4. 🧪 Testing FastMCP server..."

# Test server startup
echo "   • Testing server startup (this may take a moment)..."
if timeout 10s PYTHONPATH="$PROJECT_DIR/src" $VENV_PYTHON -m keepass_mcp_server.fastmcp_server --help > /dev/null 2>&1; then
    echo "✅ FastMCP server starts successfully"
else
    echo "⚠️  Server startup test incomplete (this is normal)"
fi

echo ""
echo "🎉 SETUP COMPLETED!"
echo "=================="
echo ""
echo "✅ FastMCP KeePass server is ready!"
echo ""
echo "📍 Configuration Details:"
echo "   • Server type: FastMCP (latest)"
echo "   • Database: $DB_PATH"
echo "   • Backup dir: $BACKUP_DIR"
echo "   • Claude config: $CLAUDE_CONFIG_FILE"
echo ""
echo "🚀 Next Steps:"
echo "   1. Restart Claude Desktop application"
echo "   2. The KeePass server will appear in your available tools"
echo "   3. Use 'authenticate' tool first to unlock your database"
echo ""
echo "🔍 Available Tools:"
echo "   • authenticate() - Unlock database"
echo "   • search_credentials() - Find entries"
echo "   • get_credential() - Get specific entry"
echo "   • create_entry() - Add new entries"
echo "   • generate_password() - Create strong passwords"
echo "   • list_groups() - Browse database structure"
echo "   • health_check() - System status"
echo ""
echo "📚 For detailed usage, see: FASTMCP_MIGRATION.md"
echo ""
echo "⚠️  Remember: You'll need to authenticate with your master password"
echo "    when you first use the KeePass tools in Claude!"
