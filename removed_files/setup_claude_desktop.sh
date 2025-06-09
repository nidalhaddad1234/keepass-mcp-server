#!/bin/bash
# Claude Desktop Integration Setup Script for KeePass MCP Server

set -e

echo "🤖 Setting up KeePass MCP Server for Claude Desktop..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS and set config path
detect_config_path() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        CONFIG_DIR="$HOME/Library/Application Support/Claude"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        CONFIG_DIR="$HOME/.config/Claude"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        CONFIG_DIR="$APPDATA/Claude"
    else
        echo -e "${RED}❌ Unsupported operating system: $OSTYPE${NC}"
        exit 1
    fi
    
    CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    echo -e "${BLUE}📍 Claude Desktop config location: $CONFIG_FILE${NC}"
}

# Create config directory if it doesn't exist
create_config_dir() {
    if [ ! -d "$CONFIG_DIR" ]; then
        echo -e "${YELLOW}📁 Creating Claude config directory...${NC}"
        mkdir -p "$CONFIG_DIR"
    fi
}

# Get user's KeePass database path
get_database_path() {
    echo -e "${YELLOW}🔍 Please provide your KeePass database information:${NC}"
    
    while true; do
        read -p "📂 Path to your KeePass database (.kdbx file): " DB_PATH
        
        if [ -f "$DB_PATH" ]; then
            # Convert to absolute path
            DB_PATH=$(realpath "$DB_PATH")
            echo -e "${GREEN}✅ Database found: $DB_PATH${NC}"
            break
        else
            echo -e "${RED}❌ File not found: $DB_PATH${NC}"
            echo "Please enter a valid path to your .kdbx file"
        fi
    done
    
    # Optional key file
    read -p "🔑 Path to key file (optional, press Enter to skip): " KEY_FILE
    if [ -n "$KEY_FILE" ] && [ -f "$KEY_FILE" ]; then
        KEY_FILE=$(realpath "$KEY_FILE")
        echo -e "${GREEN}✅ Key file found: $KEY_FILE${NC}"
    else
        KEY_FILE=""
        echo -e "${YELLOW}ℹ️ No key file specified${NC}"
    fi
    
    # Backup directory
    read -p "💾 Backup directory (default: ./keepass_backups): " BACKUP_DIR
    if [ -z "$BACKUP_DIR" ]; then
        BACKUP_DIR="$HOME/keepass_backups"
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    BACKUP_DIR=$(realpath "$BACKUP_DIR")
    echo -e "${GREEN}✅ Backup directory: $BACKUP_DIR${NC}"
}

# Get project path
get_project_path() {
    PROJECT_PATH=$(realpath "$(dirname "$0")")
    echo -e "${BLUE}📁 Project path: $PROJECT_PATH${NC}"
    
    # Check if we're in the right directory
    if [ ! -f "$PROJECT_PATH/setup.py" ] || [ ! -d "$PROJECT_PATH/src/keepass_mcp_server" ]; then
        echo -e "${RED}❌ Error: Not in KeePass MCP Server project directory${NC}"
        echo "Please run this script from the keepass-mcp-server directory"
        exit 1
    fi
}

# Install the package
install_package() {
    echo -e "${YELLOW}📦 Installing KeePass MCP Server package...${NC}"
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        echo -e "${BLUE}🔋 Using existing virtual environment${NC}"
        source venv/bin/activate
    else
        echo -e "${YELLOW}🔋 Creating virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # Install dependencies and package
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .
    
    echo -e "${GREEN}✅ Package installed successfully${NC}"
    
    # Get Python path
    PYTHON_PATH=$(which python)
    echo -e "${BLUE}🐍 Python path: $PYTHON_PATH${NC}"
}

# Create Claude Desktop configuration
create_claude_config() {
    echo -e "${YELLOW}⚙️ Creating Claude Desktop configuration...${NC}"
    
    # Backup existing config if it exists
    if [ -f "$CONFIG_FILE" ]; then
        BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}💾 Backing up existing config to: $BACKUP_FILE${NC}"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        
        # Read existing config
        EXISTING_CONFIG=$(cat "$CONFIG_FILE")
    else
        EXISTING_CONFIG="{}"
    fi
    
    # Create new configuration
    cat > "$CONFIG_FILE" << EOF
{
  "mcpServers": {
    "keepass": {
      "command": "$PYTHON_PATH",
      "args": ["-m", "keepass_mcp_server"],
      "env": {
        "KEEPASS_DB_PATH": "$DB_PATH",
$([ -n "$KEY_FILE" ] && echo "        \"KEEPASS_KEY_FILE\": \"$KEY_FILE\",")
        "KEEPASS_BACKUP_DIR": "$BACKUP_DIR",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "KEEPASS_AUTO_SAVE": "true",
        "KEEPASS_BACKUP_COUNT": "10",
        "KEEPASS_SESSION_TIMEOUT": "3600",
        "KEEPASS_AUTO_LOCK": "1800",
        "LOG_LEVEL": "INFO",
        "USE_KEYCHAIN": "true",
        "MASTER_PASSWORD_PROMPT": "true",
        "MAX_RETRIES": "3",
        "CACHE_TIMEOUT": "300",
        "MAX_CONCURRENT_OPERATIONS": "5"
      }
    }
  }
}
EOF

    echo -e "${GREEN}✅ Claude Desktop configuration created${NC}"
    echo -e "${BLUE}📁 Config file: $CONFIG_FILE${NC}"
}

# Test the configuration
test_configuration() {
    echo -e "${YELLOW}🧪 Testing MCP server configuration...${NC}"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test server startup
    echo -e "${BLUE}🚀 Testing server startup (5 second test)...${NC}"
    
    # Set environment variables
    export KEEPASS_DB_PATH="$DB_PATH"
    export KEEPASS_BACKUP_DIR="$BACKUP_DIR"
    export KEEPASS_ACCESS_MODE="readwrite"
    export LOG_LEVEL="INFO"
    
    if [ -n "$KEY_FILE" ]; then
        export KEEPASS_KEY_FILE="$KEY_FILE"
    fi
    
    # Run server test
    timeout 5s python -m keepass_mcp_server > /dev/null 2>&1 &
    SERVER_PID=$!
    
    sleep 2
    
    if kill -0 $SERVER_PID 2>/dev/null; then
        echo -e "${GREEN}✅ Server started successfully${NC}"
        kill $SERVER_PID 2>/dev/null || true
    else
        echo -e "${RED}❌ Server failed to start${NC}"
        echo "Check the logs for details"
        return 1
    fi
}

# Show usage instructions
show_instructions() {
    echo -e "\n${GREEN}🎉 Setup completed successfully!${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo ""
    echo "1. 🔄 Restart Claude Desktop application"
    echo ""
    echo "2. 🔐 In Claude, try these commands:"
    echo "   • \"Please unlock my KeePass database\""
    echo "   • \"Search for my GitHub credentials\""
    echo "   • \"Generate a strong password\""
    echo "   • \"Show me all my entries\""
    echo ""
    echo "3. 🔍 Troubleshooting:"
    echo "   • Check Claude Desktop logs if MCP doesn't connect"
    echo "   • Verify database password when prompted"
    echo "   • Config file: $CONFIG_FILE"
    echo ""
    echo -e "${BLUE}🛡️ Security Notes:${NC}"
    echo "   • Your master password is never stored"
    echo "   • Database remains encrypted"
    echo "   • Backups are created automatically"
    echo ""
    echo -e "${GREEN}✨ Enjoy secure password management with Claude!${NC}"
}

# Main function
main() {
    echo -e "${BLUE}🔧 KeePass MCP Server - Claude Desktop Integration${NC}"
    echo "=================================================="
    
    detect_config_path
    create_config_dir
    get_project_path
    get_database_path
    install_package
    create_claude_config
    
    if test_configuration; then
        show_instructions
    else
        echo -e "${RED}❌ Setup completed with warnings. Check configuration.${NC}"
        exit 1
    fi
}

# Check if running interactively
if [ -t 0 ]; then
    main "$@"
else
    echo "This script requires interactive input. Please run it directly."
    exit 1
fi
