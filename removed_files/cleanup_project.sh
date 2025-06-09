#!/bin/bash
echo "🗑️ Cleaning up unnecessary files from KeePass MCP Server project"
echo "================================================================"

# Files to delete (troubleshooting/debug files no longer needed)
FILES_TO_DELETE=(
    "fix_mcp_1_9_3.py"
    "fix_mcp_compatibility.py" 
    "investigate_mcp.py"
    "find_mcp_types.py"
    "test_mcp_capabilities.py"
    "debug_startup.py"
    "test_fastmcp_migration.py"
    "simple_test.py"
    "manual_test.py"
    "test_mcp_stdio.py"
    "test_server.py"
    "claude_desktop_config_fixed.json"
    "claude_desktop_config_minimal.json"
    "debug_server.sh"
    "check_config.sh"
)

# Keep track of what we delete
DELETED_COUNT=0
MISSING_COUNT=0

echo "Removing troubleshooting and debug files..."
echo ""

for file in "${FILES_TO_DELETE[@]}"; do
    if [ -f "$file" ]; then
        echo "🗑️  Deleting: $file"
        rm "$file"
        ((DELETED_COUNT++))
    else
        echo "⚠️  Not found: $file"
        ((MISSING_COUNT++))
    fi
done

echo ""
echo "📊 Cleanup Summary:"
echo "   Deleted: $DELETED_COUNT files"
echo "   Missing: $MISSING_COUNT files"
echo ""

# Update requirements.txt to use the FastMCP version
if [ -f "requirements.txt" ]; then
    echo "📝 Updating requirements.txt to FastMCP version..."
    cp "requirements-fastmcp.txt" "requirements.txt"
    rm "requirements-fastmcp.txt"
    echo "✅ Updated requirements.txt"
else
    echo "⚠️  requirements.txt not found"
fi

echo ""
echo "🎯 Key files remaining:"
echo "   ✅ src/keepass_mcp_server/fastmcp_server.py (NEW FastMCP server)"
echo "   ✅ src/keepass_mcp_server/server.py (original server - can keep as backup)"
echo "   ✅ requirements.txt (updated for FastMCP)"
echo "   ✅ FASTMCP_MIGRATION.md (migration documentation)"
echo "   ✅ All core modules (entry_manager.py, etc.)"
echo ""
echo "🎉 Cleanup complete! Project is now clean and ready for FastMCP."
