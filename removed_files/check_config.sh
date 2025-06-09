#!/bin/bash
echo "🔍 Testing KeePass MCP Server Configuration..."
echo "============================================="

# Test 1: Check if Python executable exists
echo "1. Checking Python executable..."
PYTHON_PATH="/home/nidal/claude_projects/keepass-mcp-server/venv/bin/python"
if [ -f "$PYTHON_PATH" ]; then
    echo "✅ Python executable found: $PYTHON_PATH"
    echo "   Python version: $($PYTHON_PATH --version)"
else
    echo "❌ Python executable not found: $PYTHON_PATH"
    exit 1
fi

# Test 2: Check if virtual environment has required packages
echo ""
echo "2. Checking installed packages..."
echo "   MCP library:"
$PYTHON_PATH -c "import mcp; print('✅ MCP installed')" 2>/dev/null || echo "❌ MCP not installed"

echo "   PyKeePass library:"
$PYTHON_PATH -c "import pykeepass; print('✅ PyKeePass installed')" 2>/dev/null || echo "❌ PyKeePass not installed"

echo "   KeePass MCP Server:"
$PYTHON_PATH -c "import keepass_mcp_server; print('✅ KeePass MCP Server installed')" 2>/dev/null || echo "❌ KeePass MCP Server not installed"

# Test 3: Check if database file exists
echo ""
echo "3. Checking database file..."
DB_PATH="/home/nidal/Downloads/keepass-nidal.kdbx"
if [ -f "$DB_PATH" ]; then
    echo "✅ Database file found: $DB_PATH"
    echo "   File size: $(du -h "$DB_PATH" | cut -f1)"
    echo "   Permissions: $(ls -l "$DB_PATH" | cut -d' ' -f1)"
else
    echo "❌ Database file not found: $DB_PATH"
fi

# Test 4: Check backup directory
echo ""
echo "4. Checking backup directory..."
BACKUP_DIR="/home/nidal/claude_projects/keepass-mcp-server/backups"
if [ -d "$BACKUP_DIR" ]; then
    echo "✅ Backup directory exists: $BACKUP_DIR"
else
    echo "⚠️  Backup directory doesn't exist, creating it..."
    mkdir -p "$BACKUP_DIR"
    echo "✅ Backup directory created: $BACKUP_DIR"
fi

# Test 5: Try to run the server with --help to see if it works
echo ""
echo "5. Testing server executable..."
echo "   Trying to run keepass_mcp_server with --help..."
$PYTHON_PATH -m keepass_mcp_server --help 2>&1 | head -10

echo ""
echo "============================================="
echo "🔍 Configuration Check Complete"
echo ""
echo "Next steps:"
echo "1. If any ❌ errors above, fix them first"
echo "2. Restart Claude Desktop completely"
echo "3. Check Claude Desktop logs for MCP server errors"
echo "4. Try: 'Please check my KeePass server health'"
