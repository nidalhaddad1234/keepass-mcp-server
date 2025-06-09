#!/bin/bash
# KeePass MCP Server - Post-Migration Cleanup Script
# Cleans up files left over from MCP 1.9.3 → FastMCP migration

set -e

echo "🧹 Starting post-migration cleanup..."

# Remove deleted_files directory (old migration artifacts)
if [ -d "deleted_files" ]; then
    echo "📁 Removing deleted_files directory..."
    rm -rf deleted_files/
    echo "✅ deleted_files directory removed"
else
    echo "ℹ️  deleted_files directory not found"
fi

# Remove Python cache files from source directory only
echo "🗂️  Removing Python cache files from src/..."
find src/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✅ Python cache files removed from src/"

# Remove build artifacts
if [ -d "src/keepass_mcp_server.egg-info" ]; then
    echo "📦 Removing build artifacts (.egg-info)..."
    rm -rf src/keepass_mcp_server.egg-info/
    echo "✅ Build artifacts removed"
fi

echo "🎉 Cleanup completed successfully!"
echo ""
echo "Cleaned up:"
echo "  - deleted_files/ directory (old migration artifacts)" 
echo "  - Python cache files in src/"
echo "  - Build artifacts (.egg-info)"
echo ""
echo "To rebuild, run: pip install -e ."

# Now manually execute the cleanup steps
echo "Executing cleanup steps..."
rm -rf deleted_files/ 2>/dev/null || echo "deleted_files not found"
find src/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || echo "No cache files in src/"
rm -rf src/keepass_mcp_server.egg-info/ 2>/dev/null || echo ".egg-info not found"
