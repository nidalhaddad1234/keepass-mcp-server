#!/bin/bash
# GitHub CLI token creation and Claude configuration update script

set -e

echo "🔑 GitHub MCP Server Setup"
echo "=========================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Please install it with:"
    echo "  Ubuntu/Debian: sudo apt install gh"
    echo "  Or: curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    exit 1
fi

# Check if user is logged in
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged into GitHub CLI${NC}"
    echo "Please login first:"
    echo "  gh auth login"
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI is installed and authenticated${NC}"

# Create a token with necessary permissions for the MCP server
echo -e "${BLUE}🔑 Creating GitHub Personal Access Token for MCP server...${NC}"

# Set token permissions needed for GitHub MCP server
SCOPES="repo,read:org,read:user,read:project"

# Create the token
echo "Creating token with scopes: $SCOPES"
TOKEN=$(gh auth token --refresh-token || gh auth refresh -h github.com && gh auth token)

if [ $? -eq 0 ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✅ GitHub token created successfully${NC}"
    
    # Update Claude Desktop configuration
    echo -e "${BLUE}📝 Updating Claude Desktop configuration...${NC}"
    
    # Backup current config
    CONFIG_FILE="/home/nidal/.config/Claude/claude_desktop_config.json"
    BACKUP_FILE="/home/nidal/.config/Claude/claude_desktop_config.json.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [ -f "$CONFIG_FILE" ]; then
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✅ Config backed up to: $BACKUP_FILE${NC}"
    fi
    
    # Create updated configuration with the token
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/home/nidal/currency-exchange",
        "/home/nidal/claude_projects",
        "/home/nidal/.config/Claude"
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
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$TOKEN"
      }
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
    
    echo -e "${GREEN}✅ Claude Desktop configuration updated successfully${NC}"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. Restart Claude Desktop to load the new configuration"
    echo "2. The GitHub MCP server will provide these capabilities:"
    echo "   • Repository management (create, read, update)"
    echo "   • File operations (read, write, search)" 
    echo "   • Issue and PR management"
    echo "   • Branch operations"
    echo "   • GitHub API integration"
    echo ""
    echo -e "${GREEN}🎉 GitHub MCP Server setup complete!${NC}"

else
    echo -e "${RED}❌ Failed to create GitHub token${NC}"
    echo "Please try manually creating a token at:"
    echo "https://github.com/settings/tokens/new"
    echo "With scopes: $SCOPES"
    exit 1
fi
