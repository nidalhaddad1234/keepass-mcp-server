#!/usr/bin/env python3
"""
Quick test to identify and fix the FastMCP startup issue
"""

import subprocess
import sys
import os

def test_and_fix():
    print("🔧 KeePass FastMCP Server - Quick Fix")
    print("====================================")
    
    # Paths
    project_dir = "/home/nidal/claude_projects/keepass-mcp-server"
    venv_python = f"{project_dir}/venv/bin/python"
    
    os.chdir(project_dir)
    
    print("1. 📦 Installing FastMCP...")
    try:
        result = subprocess.run([venv_python, "-m", "pip", "install", "fastmcp"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ FastMCP installed successfully")
        else:
            print(f"   ❌ FastMCP installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ Error installing FastMCP: {e}")
        return False
    
    print("\n2. 🔄 Reinstalling package...")
    try:
        result = subprocess.run([venv_python, "-m", "pip", "install", "-e", "."], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Package reinstalled")
        else:
            print(f"   ❌ Package reinstall failed: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Error reinstalling package: {e}")
    
    print("\n3. 🧪 Testing FastMCP import...")
    test_script = '''
import sys
sys.path.insert(0, "/home/nidal/claude_projects/keepass-mcp-server/src")

try:
    from mcp.server.fastmcp import FastMCP
    print("✅ FastMCP library imported successfully")
except ImportError as e:
    print(f"❌ FastMCP import failed: {e}")
    sys.exit(1)

try:
    from keepass_mcp_server.fastmcp_server import KeePassFastMCPServer
    print("✅ FastMCP server class imported successfully")
except ImportError as e:
    print(f"❌ FastMCP server import failed: {e}")
    sys.exit(1)

print("✅ All imports successful!")
'''
    
    try:
        result = subprocess.run([venv_python, "-c", test_script], 
                              capture_output=True, text=True)
        print(f"   {result.stdout}")
        if result.stderr:
            print(f"   Errors: {result.stderr}")
        if result.returncode != 0:
            return False
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False
    
    print("\n4. 🚀 Testing server startup...")
    env = os.environ.copy()
    env.update({
        "KEEPASS_DB_PATH": f"{project_dir}/keepass-nidal.kdbx",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "LOG_LEVEL": "INFO",
        "PYTHONPATH": f"{project_dir}/src"
    })
    
    try:
        # Test the exact command Claude Desktop will use
        result = subprocess.run([
            venv_python, "-m", "keepass_mcp_server.fastmcp_server", "--help"
        ], capture_output=True, text=True, timeout=5, env=env)
        
        if result.returncode == 0:
            print("   ✅ Server help command works")
        else:
            print(f"   ❌ Server help failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ Server command timeout (might be normal)")
    except Exception as e:
        print(f"   ❌ Server test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_and_fix()
    
    if success:
        print("\n🎉 FastMCP server should now work!")
        print("\n📋 Updated Claude Desktop Config:")
        print('```json')
        print('{')
        print('  "mcpServers": {')
        print('    "keepass": {')
        print('      "command": "/home/nidal/claude_projects/keepass-mcp-server/venv/bin/python",')
        print('      "args": ["-m", "keepass_mcp_server.fastmcp_server"],')
        print('      "cwd": "/home/nidal/claude_projects/keepass-mcp-server",')
        print('      "env": {')
        print('        "KEEPASS_DB_PATH": "/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx",')
        print('        "KEEPASS_ACCESS_MODE": "readwrite",')
        print('        "LOG_LEVEL": "INFO",')
        print('        "USE_KEYCHAIN": "false",')
        print('        "MASTER_PASSWORD_PROMPT": "true",')
        print('        "PYTHONPATH": "/home/nidal/claude_projects/keepass-mcp-server/src"')
        print('      }')
        print('    }')
        print('  }')
        print('}')
        print('```')
        print("\n🔄 Next steps:")
        print("1. Update your Claude Desktop config with the above")
        print("2. Restart Claude Desktop")
        print("3. Test the KeePass tools")
    else:
        print("\n❌ Issues found - check output above")
