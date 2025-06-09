#!/usr/bin/env python3
"""
Quick test script for FastMCP KeePass server setup
"""

import sys
import os
import json
from pathlib import Path

def test_fastmcp_setup():
    """Test FastMCP setup and configuration."""
    print("🧪 Testing FastMCP KeePass Server Setup")
    print("======================================")
    print()
    
    errors = []
    warnings = []
    
    # Test 1: Check Python environment
    print("1. 🐍 Python Environment")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    
    # Test 2: Check project structure
    print("\n2. 📁 Project Structure")
    required_files = [
        "src/keepass_mcp_server/fastmcp_server.py",
        "src/keepass_mcp_server/__main_fastmcp__.py",
        "claude_desktop_config_fastmcp.json",
        "claude_desktop_config_minimal.json"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            errors.append(f"Missing file: {file_path}")
    
    # Test 3: Check database file
    print("\n3. 🗄️ Database File")
    db_path = "keepass-nidal.kdbx"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"   ✅ Database found: {db_path} ({size} bytes)")
    else:
        print(f"   ❌ Database not found: {db_path}")
        errors.append("KeePass database file not found")
    
    # Test 4: Check backup directory
    print("\n4. 💾 Backup Directory")
    backup_dir = "backups"
    if os.path.exists(backup_dir):
        print(f"   ✅ Backup directory exists: {backup_dir}")
    else:
        print(f"   ⚠️  Backup directory missing: {backup_dir}")
        warnings.append("Backup directory will be created automatically")
    
    # Test 5: Test imports
    print("\n5. 📦 Package Imports")
    
    # Add src to Python path
    src_path = os.path.join(os.getcwd(), "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    try:
        from keepass_mcp_server.config import get_config
        print("   ✅ Config module")
    except ImportError as e:
        print(f"   ❌ Config module: {e}")
        errors.append("Cannot import config module")
    
    try:
        from mcp.server.fastmcp import FastMCP
        print("   ✅ FastMCP library")
    except ImportError as e:
        print(f"   ❌ FastMCP library: {e}")
        errors.append("FastMCP not installed - run: pip install fastmcp")
    
    try:
        from keepass_mcp_server.fastmcp_server import KeePassFastMCPServer
        print("   ✅ FastMCP server class")
    except ImportError as e:
        print(f"   ❌ FastMCP server class: {e}")
        errors.append("Cannot import FastMCP server")
    
    # Test 6: Check configuration files
    print("\n6. ⚙️ Configuration Files")
    config_files = [
        "claude_desktop_config_fastmcp.json",
        "claude_desktop_config_minimal.json"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"   ✅ {config_file} (valid JSON)")
            except json.JSONDecodeError as e:
                print(f"   ❌ {config_file} (invalid JSON): {e}")
                errors.append(f"Invalid JSON in {config_file}")
        else:
            print(f"   ❌ {config_file} (missing)")
            errors.append(f"Missing config file: {config_file}")
    
    # Test 7: Check executable scripts
    print("\n7. 🔧 Executable Scripts")
    scripts = [
        "setup_fastmcp_claude.sh",
        "complete_cleanup.sh",
        "make-executable.sh"
    ]
    
    for script in scripts:
        if os.path.exists(script):
            if os.access(script, os.X_OK):
                print(f"   ✅ {script} (executable)")
            else:
                print(f"   ⚠️  {script} (not executable)")
                warnings.append(f"Run: chmod +x {script}")
        else:
            print(f"   ❌ {script} (missing)")
            errors.append(f"Missing script: {script}")
    
    # Summary
    print("\n" + "="*50)
    if errors:
        print("❌ SETUP ISSUES FOUND:")
        for error in errors:
            print(f"   • {error}")
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Run: pip install -e .")
        print("   2. Run: pip install fastmcp")
        print("   3. Run: chmod +x *.sh")
        print("   4. Ensure KeePass database is in project root")
        return False
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   • {warning}")
    
    print("\n🎉 FASTMCP SETUP LOOKS GOOD!")
    print("\n🚀 NEXT STEPS:")
    print("   1. Run: ./setup_fastmcp_claude.sh")
    print("   2. Restart Claude Desktop")
    print("   3. Test authentication with your KeePass password")
    
    return True

if __name__ == "__main__":
    success = test_fastmcp_setup()
    sys.exit(0 if success else 1)
