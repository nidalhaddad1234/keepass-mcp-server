#!/usr/bin/env python3
"""
Simple test to verify the fixed MCP server outputs only JSON to stdout
"""

import sys
import os
import subprocess
import signal

def test_server_output():
    """Test if the server outputs clean JSON to stdout"""
    
    # Set environment variables
    env = os.environ.copy()
    env['PYTHONPATH'] = '/home/nidal/claude_projects/keepass-mcp-server/src'
    env['KEEPASS_DB_PATH'] = '/home/nidal/claude_projects/keepass-mcp-server/keepass-nidal.kdbx'
    env['KEEPASS_ACCESS_MODE'] = 'readwrite'
    env['USE_KEYCHAIN'] = 'false'
    env['LOG_LEVEL'] = 'ERROR'  # Minimize logs
    
    # Change to project directory
    os.chdir('/home/nidal/claude_projects/keepass-mcp-server')
    
    try:
        print("Testing fixed server output...", file=sys.stderr)
        
        # Start the server
        proc = subprocess.Popen(
            ['/home/nidal/claude_projects/keepass-mcp-server/venv/bin/python', 
             '-m', 'keepass_mcp_server.fastmcp_server_fixed'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True
        )
        
        # Give it a moment to start
        import time
        time.sleep(2)
        
        # Terminate the process
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=5)
        
        print(f"Server stderr (logs): {stderr[:200]}...", file=sys.stderr)
        print(f"Server stdout (should be empty or JSON): '{stdout[:100]}'", file=sys.stderr)
        
        # Check if stdout starts with non-JSON text
        if stdout.strip() and not stdout.strip().startswith('{'):
            print("❌ PROBLEM: Server outputs non-JSON to stdout!", file=sys.stderr)
            print(f"Bad output: {stdout[:100]}", file=sys.stderr)
            return False
        else:
            print("✅ GOOD: Server outputs clean to stdout", file=sys.stderr)
            return True
            
    except Exception as e:
        print(f"❌ Test error: {e}", file=sys.stderr)
        return False

def check_current_claude_config():
    """Check what's currently in the Claude config"""
    try:
        config_path = '/home/nidal/.config/claude-desktop/claude_desktop_config.json'
        with open(config_path, 'r') as f:
            content = f.read()
            
        if 'fastmcp_server_fixed' in content:
            print("✅ Claude config uses fixed server", file=sys.stderr)
            return True
        else:
            print("❌ Claude config still uses old server", file=sys.stderr)
            print("You need to update your Claude config!", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Cannot check Claude config: {e}", file=sys.stderr)
        return False

def main():
    print("=== Quick MCP Server Fix Verification ===", file=sys.stderr)
    
    # Test 1: Server output
    server_ok = test_server_output()
    
    # Test 2: Claude config
    config_ok = check_current_claude_config()
    
    print("", file=sys.stderr)
    if server_ok and config_ok:
        print("✅ Everything looks good! Restart Claude Desktop.", file=sys.stderr)
    else:
        print("❌ Issues found. Follow the fix steps.", file=sys.stderr)

if __name__ == "__main__":
    main()
