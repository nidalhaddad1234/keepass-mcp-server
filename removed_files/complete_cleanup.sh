#!/bin/bash
# KeePass MCP Server - Complete Post-Migration Cleanup
# Removes all artifacts left over from MCP 1.9.3 → FastMCP migration

set -e

echo "🧹 KeePass MCP Server - Post-Migration Cleanup"
echo "=============================================="
echo ""

# Function to safely remove directory
safe_remove_dir() {
    if [ -d "$1" ]; then
        echo "📁 Removing directory: $1"
        rm -rf "$1"
        echo "✅ Removed: $1"
    else
        echo "ℹ️  Directory not found: $1"
    fi
}

# Function to safely remove file
safe_remove_file() {
    if [ -f "$1" ]; then
        echo "📄 Removing file: $1"
        rm "$1"
        echo "✅ Removed: $1"
    else
        echo "ℹ️  File not found: $1"
    fi
}

echo "🗑️ PHASE 1: Removing old migration artifacts..."
echo "-----------------------------------------------"

# Remove entire deleted_files directory
safe_remove_dir "deleted_files"

echo ""
echo "🗂️ PHASE 2: Cleaning Python cache files..."
echo "-------------------------------------------"

# Remove Python cache files (only in src, not in venv)
find src/ -name "__pycache__" -type d -print0 | while IFS= read -r -d '' dir; do
    echo "📁 Removing cache: $dir"
    rm -rf "$dir"
done

echo "✅ Python cache files cleaned"

echo ""
echo "📦 PHASE 3: Removing build artifacts..."
echo "---------------------------------------"

# Remove build artifacts
safe_remove_dir "src/keepass_mcp_server.egg-info"

echo ""
echo "🧽 PHASE 4: Optional cleanup (uncomment if desired)..."
echo "-----------------------------------------------------"
echo "# The following are optional - uncomment if you want a completely fresh start:"
echo ""
echo "# Remove virtual environment (will need to reinstall packages):"
echo "# safe_remove_dir \"venv\""
echo ""
echo "# Remove temporary script files:"
echo "# safe_remove_file \"remove_old_files.sh\""
echo "# safe_remove_file \"cleanup_migration.sh\""
echo "# safe_remove_file \"cleanup_log.txt\""

echo ""
echo "🎉 CLEANUP COMPLETED!"
echo "===================="
echo ""
echo "✅ Cleaned up:"
echo "   • deleted_files/ directory (old migration artifacts)"
echo "   • Python cache files (__pycache__ in src/)"
echo "   • Build artifacts (.egg-info)"
echo ""
echo "🔄 To rebuild the package:"
echo "   pip install -e ."
echo ""
echo "🚀 To test your cleaned project:"
echo "   ./run_tests.sh all"
echo ""
echo "📝 Your project is now clean and ready for use with FastMCP!"
