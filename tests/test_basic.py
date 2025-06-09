"""
Minimal test to ensure CI/CD works.
"""
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_import_main_module():
    """Test that main module can be imported."""
    try:
        import keepass_mcp_server
        assert keepass_mcp_server is not None
    except ImportError as e:
        pytest.fail(f"Failed to import main module: {e}")

def test_import_config():
    """Test that config module can be imported."""
    try:
        from keepass_mcp_server.config import get_config
        assert get_config is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config module: {e}")

def test_import_exceptions():
    """Test that exceptions module can be imported."""
    try:
        from keepass_mcp_server.exceptions import KeePassMCPError
        assert KeePassMCPError is not None
    except ImportError as e:
        pytest.fail(f"Failed to import exceptions module: {e}")

def test_basic_functionality():
    """Test basic functionality without requiring KeePass database."""
    from keepass_mcp_server.password_generator import PasswordGenerator
    from keepass_mcp_server.validators import Validators
    
    # Test password generator
    generator = PasswordGenerator()
    password = generator.generate_password(length=12)
    assert len(password) == 12
    assert isinstance(password, str)
    
    # Test validators
    result = Validators.validate_search_query("test")
    assert result == "test"

def test_fastmcp_import():
    """Test that FastMCP can be imported when available."""
    try:
        from mcp.server.fastmcp import FastMCP
        assert FastMCP is not None
    except ImportError:
        # This is OK - FastMCP might not be available in all environments
        pass

if __name__ == "__main__":
    pytest.main([__file__])
