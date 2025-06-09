#!/usr/bin/env python3
"""
Debug FastMCP KeePass Server startup issues
"""

import sys
import os
import subprocess
import json
from pathlib import Path

def debug_fastmcp_startup():
    """Debug FastMCP server startup issues."""
    print("🐛 KeePass FastMCP Server - Startup Debugging")
    print("============================================")
    print()

    # Set up paths
    project_dir = "/home/nidal/claude_projects/keepass-mcp-server"
    venv_python = f"{project_dir}/venv/bin/python"
    src_dir = f"{project_dir}/src"
    
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Python executable: {venv_python}")
    print(f"📂 Source directory: {src_dir}")
    print()

    # Check if we're in the right directory
    current_dir = os.getcwd()
    if current_dir != project_dir:
        print(f"⚠️  Current directory: {current_dir}")
        print(f"   Expected: {project_dir}")
        print("   Changing to project directory...")
        os.chdir(project_dir)
    
    # Test 1: Check virtual environment
    print("1. 🔍 Checking Virtual Environment...")
    if not os.path.exists(venv_python):
        print(f"❌ Virtual environment not found: {venv_python}")
        return False
    
    try:
        result = subprocess.run([venv_python, "--version"], capture_output=True, text=True)
        print(f"   ✅ Python version: {result.stdout.strip()}")
    except Exception as e:
        print(f"   ❌ Cannot run Python: {e}")
        return False

    # Test 2: Check if FastMCP is installed
    print("\n2. 📦 Checking FastMCP Installation...")
    try:
        result = subprocess.run([
            venv_python, "-c", "from mcp.server.fastmcp import FastMCP; print('FastMCP available')"
        ], capture_output=True, text=True, cwd=project_dir)
        
        if result.returncode == 0:
            print("   ✅ FastMCP is installed")
        else:
            print(f"   ❌ FastMCP not available: {result.stderr}")
            print("   🔧 Fix: pip install fastmcp")
            return False
    except Exception as e:
        print(f"   ❌ Error checking FastMCP: {e}")
        return False

    # Test 3: Check database file
    print("\n3. 🗄️ Checking Database File...")
    db_path = f"{project_dir}/keepass-nidal.kdbx"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        print(f"   ✅ Database found: {db_path} ({size} bytes)")
    else:
        print(f"   ❌ Database not found: {db_path}")
        # Check alternative locations
        alt_paths = [
            "/home/nidal/Downloads/keepass-nidal.kdbx",
            f"{project_dir}/database.kdbx",
            f"{project_dir}/*.kdbx"
        ]
        print("   🔍 Checking alternative locations...")
        for alt_path in alt_paths:
            if "*" in alt_path:
                import glob
                matches = glob.glob(alt_path)
                if matches:
                    print(f"   📍 Found: {matches[0]}")
            elif os.path.exists(alt_path):
                print(f"   📍 Found: {alt_path}")

    # Test 4: Test basic import
    print("\n4. 🧪 Testing Basic Imports...")
    
    test_script = f'''
import sys
sys.path.insert(0, "{src_dir}")

try:
    from keepass_mcp_server.config import get_config
    print("✅ Config import successful")
except Exception as e:
    print(f"❌ Config import failed: {{e}}")
    sys.exit(1)

try:
    from keepass_mcp_server.fastmcp_server import KeePassFastMCPServer
    print("✅ FastMCP server import successful")
except Exception as e:
    print(f"❌ FastMCP server import failed: {{e}}")
    sys.exit(1)
'''
    
    try:
        result = subprocess.run([venv_python, "-c", test_script], 
                              capture_output=True, text=True, cwd=project_dir)
        
        if result.returncode == 0:
            print(f"   {result.stdout.strip()}")
        else:
            print(f"   ❌ Import test failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot run import test: {e}")
        return False

    # Test 5: Test FastMCP server startup (with proper error capture)
    print("\n5. 🚀 Testing FastMCP Server Startup...")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        "KEEPASS_DB_PATH": db_path,
        "KEEPASS_ACCESS_MODE": "readwrite",
        "LOG_LEVEL": "DEBUG",
        "PYTHONPATH": src_dir
    })
    
    startup_script = f'''
import sys
sys.path.insert(0, "{src_dir}")

try:
    from keepass_mcp_server.fastmcp_server import main
    print("🔧 Starting FastMCP server test...")
    main()
except KeyboardInterrupt:
    print("✅ Server startup successful (interrupted by user)")
    sys.exit(0)
except Exception as e:
    print(f"❌ Server startup failed: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    print("   Starting server with 5-second timeout...")
    try:
        result = subprocess.run([venv_python, "-c", startup_script],
                              capture_output=True, text=True, timeout=5,
                              cwd=project_dir, env=env)
        
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   Stdout: {result.stdout}")
        if result.stderr:
            print(f"   Stderr: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        print("   ✅ Server appears to start (timeout reached)")
    except Exception as e:
        print(f"   ❌ Server test failed: {e}")

    # Test 6: Test command line that Claude Desktop uses
    print("\n6. 📋 Testing Claude Desktop Command...")
    
    claude_command = [
        venv_python, "-m", "keepass_mcp_server.fastmcp_server"
    ]
    
    print(f"   Command: {' '.join(claude_command)}")
    print("   Environment variables:")
    for key in ["KEEPASS_DB_PATH", "KEEPASS_ACCESS_MODE", "LOG_LEVEL", "PYTHONPATH"]:
        print(f"     {key}={env.get(key, 'Not set')}")
    
    try:
        result = subprocess.run(claude_command, capture_output=True, text=True,
                              timeout=3, cwd=project_dir, env=env)
        
        print(f"   Return code: {result.returncode}")
        if result.stdout:
            print(f"   Stdout: {result.stdout[:200]}...")  # First 200 chars
        if result.stderr:
            print(f"   Stderr: {result.stderr[:200]}...")  # First 200 chars
            
        # Check if output starts with "Fatal error"
        if result.stdout.startswith("Fatal"):
            print("   🎯 FOUND THE ISSUE: Server outputting 'Fatal error' to stdout")
            print("   This is what Claude Desktop is trying to parse as JSON!")
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Command timed out (normal for MCP servers)")
    except Exception as e:
        print(f"   ❌ Command test failed: {e}")

    return True

def suggest_fixes():
    """Suggest potential fixes based on common issues."""
    print("\n" + "="*50)
    print("🔧 POTENTIAL FIXES:")
    print("=" * 50)
    
    print("\n1. 📦 Install/Reinstall Dependencies:")
    print("   cd /home/nidal/claude_projects/keepass-mcp-server")
    print("   source venv/bin/activate")
    print("   pip install --upgrade fastmcp")
    print("   pip install -e .")
    
    print("\n2. 🗄️ Database Path Issues:")
    print("   # Make sure database exists and is readable")
    print("   ls -la /home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx")
    print("   # Or update path in Claude Desktop config")
    
    print("\n3. 🔧 Test Server Manually:")
    print("   cd /home/nidal/claude_projects/keepass-mcp-server")
    print("   source venv/bin/activate")
    print("   export KEEPASS_DB_PATH=/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx")
    print("   python -m keepass_mcp_server.fastmcp_server")
    
    print("\n4. 📝 Check Claude Desktop Config:")
    print("   # Make sure args point to: keepass_mcp_server.fastmcp_server")
    print("   # Not just: keepass_mcp_server")
    
    print("\n5. 🧹 Clean Installation:")
    print("   ./complete_cleanup.sh  # Clean old files")
    print("   pip install -e .       # Reinstall package")

if __name__ == "__main__":
    success = debug_fastmcp_startup()
    suggest_fixes()
    
    if not success:
        print("\n❌ Debug completed with issues found")
        sys.exit(1)
    else:
        print("\n✅ Debug completed - check output above for specific issues")
        sys.exit(0)
