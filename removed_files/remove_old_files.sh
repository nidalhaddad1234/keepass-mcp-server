#!/bin/bash
# Simple deletion of old migration files

# List of files to delete from deleted_files/
files_to_delete=(
    "claude_desktop_config_fixed.json"
    "claude_desktop_config_minimal.json" 
    "debug_server.sh"
    "debug_startup.py"
    "find_mcp_types.py"
    "fix_mcp_1_9_3.py"
    "fix_mcp_compatibility.py"
    "investigate_mcp.py"
    "manual_test.py"
    "simple_test.py"
    "test_fastmcp_migration.py"
    "test_mcp_capabilities.py"
    "test_mcp_stdio.py"
    "test_server.py"
    "cleanup_completed.txt"
)

echo "🗑️ Removing old migration files..."

for file in "${files_to_delete[@]}"; do
    if [ -f "deleted_files/$file" ]; then
        rm "deleted_files/$file"
        echo "✅ Removed: $file"
    fi
done

# Remove the now-empty deleted_files directory
if [ -d "deleted_files" ]; then
    rmdir deleted_files
    echo "✅ Removed: deleted_files directory"
fi

echo "🎉 Old migration files cleanup completed!"
