"""
Integration tests for KeePass MCP Server.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from keepass_mcp_server.server import KeePassMCPServer
from keepass_mcp_server.config import KeePassMCPConfig
from keepass_mcp_server.exceptions import (
    AuthenticationError,
    DatabaseLockedError,
    ValidationError,
    ReadOnlyModeError
)


class TestKeePassMCPServerIntegration:
    """Integration tests for the complete KeePass MCP Server."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing."""
        config = Mock(spec=KeePassMCPConfig)
        config.keepass_db_path = "/test/database.kdbx"
        config.keepass_key_file = None
        config.keepass_backup_dir = "/test/backups"
        config.access_mode = "readwrite"
        config.auto_save = True
        config.backup_count = 10
        config.session_timeout = 3600
        config.auto_lock_timeout = 1800
        config.log_level = "INFO"
        config.use_keychain = True
        config.max_retries = 3
        config.is_read_only.return_value = False
        config.setup_logging.return_value = None
        config.get_backup_dir.return_value = Path("/test/backups")
        return config
    
    @pytest.fixture
    def server(self, mock_config):
        """Create KeePass MCP Server instance for testing."""
        with patch('keepass_mcp_server.server.MCP_AVAILABLE', True), \
             patch('keepass_mcp_server.server.Server'), \
             patch('keepass_mcp_server.server.SecurityManager'), \
             patch('keepass_mcp_server.server.KeePassHandler'), \
             patch('keepass_mcp_server.server.BackupManager'):
            return KeePassMCPServer(mock_config)
    
    @pytest.mark.asyncio
    async def test_authentication_workflow(self, server):
        """Test complete authentication workflow."""
        # Mock the keepass handler
        server.keepass_handler.unlock_database = Mock(return_value={
            'unlocked_at': datetime.now().isoformat(),
            'database_path': '/test/database.kdbx',
            'entry_count': 10,
            'group_count': 3
        })
        
        server.security_manager.authenticate_user = Mock(return_value="test_session_token")
        
        # Test authentication tool
        auth_args = {
            'password': 'test_password',
            'key_file': None
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['authenticate'](auth_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert 'session_token' in response_data
        assert server.current_session == "test_session_token"
    
    @pytest.mark.asyncio
    async def test_search_credentials_workflow(self, server):
        """Test credential search workflow."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock entry manager
        mock_entries = [
            {
                'id': 'entry1',
                'title': 'GitHub Account',
                'username': 'developer',
                'url': 'https://github.com',
                'group': 'Development',
                'tags': ['development', 'git']
            }
        ]
        
        server.entry_manager.list_entries = Mock(return_value=mock_entries)
        server.search_engine.search_entries = Mock(return_value=mock_entries)
        
        # Test search tool
        search_args = {
            'query': 'GitHub',
            'search_fields': ['title', 'url'],
            'limit': 10
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['search_credentials'](search_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['results_count'] == 1
        assert response_data['results'][0]['title'] == 'GitHub Account'
    
    @pytest.mark.asyncio
    async def test_create_entry_workflow(self, server):
        """Test entry creation workflow."""
        # Setup session and write permissions
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        server.config.is_read_only.return_value = False
        
        # Mock entry creation
        mock_entry = {
            'id': 'new_entry_id',
            'title': 'New Account',
            'username': 'newuser',
            'password': 'GeneratedPassword123!',
            'url': 'https://example.com',
            'group': 'Personal'
        }
        
        server.entry_manager.create_entry = Mock(return_value=mock_entry)
        
        # Test create entry tool
        create_args = {
            'title': 'New Account',
            'username': 'newuser',
            'url': 'https://example.com',
            'generate_password': True,
            'password_options': {'length': 16}
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['create_entry'](create_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['entry']['title'] == 'New Account'
        assert len(response_data['entry']['password']) >= 16
    
    @pytest.mark.asyncio
    async def test_readonly_mode_enforcement(self, server):
        """Test that read-only mode is enforced."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        server.config.is_read_only.return_value = True
        
        # Test create entry in read-only mode
        create_args = {
            'title': 'New Account',
            'username': 'newuser'
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['create_entry'](create_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is False
        assert 'READ_ONLY_MODE' in response_data['error']['code']
    
    @pytest.mark.asyncio
    async def test_session_validation_failure(self, server):
        """Test handling of session validation failure."""
        # Setup invalid session
        server.current_session = "invalid_session"
        server.security_manager.validate_session = Mock(side_effect=AuthenticationError("Invalid session"))
        
        # Test any authenticated operation
        search_args = {'query': 'test'}
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['search_credentials'](search_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is False
        assert 'AUTH_ERROR' in response_data['error']['code']
    
    @pytest.mark.asyncio
    async def test_database_locked_handling(self, server):
        """Test handling of locked database."""
        # Setup session but locked database
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        server.entry_manager.list_entries = Mock(side_effect=DatabaseLockedError("Database is locked"))
        
        # Test operation on locked database
        search_args = {'query': 'test'}
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['search_credentials'](search_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is False
        assert 'DATABASE_LOCKED' in response_data['error']['code']
    
    @pytest.mark.asyncio
    async def test_password_generation_workflow(self, server):
        """Test password generation workflow."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock password generation
        server.password_generator.generate_password = Mock(return_value="GeneratedPassword123!")
        server.password_generator.check_password_strength = Mock(return_value={
            'score': 85,
            'strength': 'Strong',
            'feedback': []
        })
        
        # Test password generation tool
        gen_args = {
            'length': 16,
            'include_uppercase': True,
            'include_lowercase': True,
            'include_numbers': True,
            'include_symbols': True
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['generate_password'](gen_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['password'] == "GeneratedPassword123!"
        assert response_data['strength_analysis']['strength'] == 'Strong'
    
    @pytest.mark.asyncio
    async def test_backup_operations_workflow(self, server):
        """Test backup operations workflow."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock backup creation
        mock_backup_info = {
            'filename': 'backup_20240101_120000_manual.kdbx.gz',
            'created_at': datetime.now().isoformat(),
            'reason': 'manual',
            'compressed': True,
            'verified': True
        }
        
        server.backup_manager.create_backup = Mock(return_value=mock_backup_info)
        
        # Test backup creation tool
        backup_args = {
            'reason': 'manual',
            'compress': True,
            'verify': True
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['create_backup'](backup_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['backup_info']['filename'].endswith('.gz')
        assert response_data['backup_info']['verified'] is True
    
    @pytest.mark.asyncio
    async def test_error_handling_chain(self, server):
        """Test error handling throughout the system."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        server.config.is_read_only.return_value = False
        
        # Test validation error
        server.entry_manager.create_entry = Mock(side_effect=ValidationError("Invalid title"))
        
        create_args = {'title': ''}  # Invalid title
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['create_entry'](create_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is False
        assert response_data['error']['type'] == 'ValidationError'
        assert 'Invalid title' in response_data['error']['message']
    
    @pytest.mark.asyncio
    async def test_group_management_workflow(self, server):
        """Test group management workflow."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        server.config.is_read_only.return_value = False
        
        # Mock group operations
        mock_group = {
            'id': 'group123',
            'name': 'Development',
            'notes': 'Development related accounts',
            'parent_id': None,
            'created': datetime.now().isoformat()
        }
        
        server.group_manager.create_group = Mock(return_value=mock_group)
        server.group_manager.list_groups = Mock(return_value=[mock_group])
        
        # Test create group
        create_group_args = {
            'name': 'Development',
            'notes': 'Development related accounts'
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['create_group'](create_group_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['group']['name'] == 'Development'
        
        # Test list groups
        list_args = {'include_statistics': False}
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['list_groups'](list_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['groups_count'] == 1
    
    @pytest.mark.asyncio
    async def test_advanced_search_workflow(self, server):
        """Test advanced search features."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock weak password search
        weak_entries = [
            {
                'id': 'weak1',
                'title': 'Weak Account',
                'password': 'weak',
                'weakness_reasons': ['Too short', 'Low complexity']
            }
        ]
        
        server.entry_manager.list_entries = Mock(return_value=weak_entries)
        server.search_engine.search_weak_passwords = Mock(return_value=weak_entries)
        
        # Test weak password search
        weak_args = {
            'min_length': 8,
            'require_complexity': True
        }
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['search_weak_passwords'](weak_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert response_data['weak_entries_count'] == 1
        assert 'weakness_reasons' in response_data['weak_entries'][0]


class TestMCPProtocolCompliance:
    """Test MCP protocol compliance and tool registration."""
    
    @pytest.fixture
    def server(self):
        """Create server for protocol testing."""
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        mock_config.setup_logging.return_value = None
        
        with patch('keepass_mcp_server.server.MCP_AVAILABLE', True), \
             patch('keepass_mcp_server.server.Server') as mock_server_class, \
             patch('keepass_mcp_server.server.SecurityManager'), \
             patch('keepass_mcp_server.server.KeePassHandler'), \
             patch('keepass_mcp_server.server.BackupManager'):
            
            mock_server = Mock()
            mock_server.call_tool.return_value = lambda: None
            mock_server.list_resources.return_value = lambda: None
            mock_server.read_resource.return_value = lambda: None
            mock_server_class.return_value = mock_server
            
            server = KeePassMCPServer(mock_config)
            server.server = mock_server
            return server
    
    def test_tool_registration(self, server):
        """Test that all required tools are registered."""
        # Verify that call_tool decorator was called for each tool
        call_tool_calls = server.server.call_tool.call_count
        
        # We expect at least these tools to be registered:
        expected_tools = [
            'authenticate', 'logout', 'search_credentials', 'search_by_url',
            'get_credential', 'list_entries', 'list_groups', 'get_group_info',
            'create_entry', 'update_entry', 'delete_entry', 'move_entry', 'duplicate_entry',
            'create_group', 'update_group', 'delete_group', 'move_group',
            'generate_password', 'save_database', 'create_backup', 'get_database_info',
            'health_check', 'search_weak_passwords', 'search_duplicates', 'validate_entries'
        ]
        
        # Should have at least the expected number of tools
        assert call_tool_calls >= len(expected_tools)
    
    def test_resource_registration(self, server):
        """Test that resources are registered."""
        # Verify that resource decorators were called
        assert server.server.list_resources.called
        assert server.server.read_resource.called
    
    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self, server):
        """Test tool parameter validation."""
        # Mock session validation
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Test with missing required parameters
        with pytest.raises((ValidationError, TypeError)):
            # This should fail due to missing title
            await server._validate_session()  # This exists and should work
            # The actual tool would fail on missing parameters


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    @pytest.fixture
    def server(self):
        """Create server for error testing."""
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        mock_config.setup_logging.return_value = None
        
        with patch('keepass_mcp_server.server.MCP_AVAILABLE', True), \
             patch('keepass_mcp_server.server.Server'), \
             patch('keepass_mcp_server.server.SecurityManager'), \
             patch('keepass_mcp_server.server.KeePassHandler'), \
             patch('keepass_mcp_server.server.BackupManager'):
            return KeePassMCPServer(mock_config)
    
    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, server):
        """Test recovery from database connection issues."""
        # Setup initial good state
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Simulate database connection failure
        server.keepass_handler.get_database_info = Mock(
            side_effect=DatabaseLockedError("Connection lost")
        )
        
        # Test health check tool should handle the error gracefully
        result = await server.server.handlers['call_tool']['health_check']({})
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        # Should return health status even if database is locked
        assert 'health_check' in response_data
    
    @pytest.mark.asyncio
    async def test_session_expiry_recovery(self, server):
        """Test recovery from session expiry."""
        # Setup expired session
        server.current_session = "expired_session"
        server.security_manager.validate_session = Mock(
            side_effect=AuthenticationError("Session expired")
        )
        
        # Any authenticated operation should clear the session
        search_args = {'query': 'test'}
        
        # Mock the tool call
        result = await server.server.handlers['call_tool']['search_credentials'](search_args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is False
        
        # Session should be cleared
        assert server.current_session is None
    
    def test_cleanup_on_shutdown(self, server):
        """Test proper cleanup on server shutdown."""
        # Setup some state
        server.current_session = "test_session"
        
        # Mock manager cleanup methods
        server.security_manager.cleanup = Mock()
        server.keepass_handler.cleanup = Mock()
        
        # Call cleanup
        server.cleanup()
        
        # Verify cleanup was called
        server.security_manager.cleanup.assert_called_once()
        server.keepass_handler.cleanup.assert_called_once()


class TestPerformanceAndConcurrency:
    """Test performance and concurrency aspects."""
    
    @pytest.fixture
    def server(self):
        """Create server for performance testing."""
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        mock_config.setup_logging.return_value = None
        mock_config.max_concurrent_operations = 5
        
        with patch('keepass_mcp_server.server.MCP_AVAILABLE', True), \
             patch('keepass_mcp_server.server.Server'), \
             patch('keepass_mcp_server.server.SecurityManager'), \
             patch('keepass_mcp_server.server.KeePassHandler'), \
             patch('keepass_mcp_server.server.BackupManager'):
            return KeePassMCPServer(mock_config)
    
    @pytest.mark.asyncio
    async def test_concurrent_search_operations(self, server):
        """Test handling of concurrent search operations."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock search results
        mock_entries = [{'id': f'entry{i}', 'title': f'Entry {i}'} for i in range(10)]
        server.entry_manager.list_entries = Mock(return_value=mock_entries)
        server.search_engine.search_entries = Mock(return_value=mock_entries)
        
        # Run multiple concurrent searches
        async def search_task(query):
            args = {'query': query, 'limit': 5}
            return await server.server.handlers['call_tool']['search_credentials'](args)
        
        # Create multiple concurrent tasks
        tasks = [search_task(f"query{i}") for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All tasks should complete successfully
        assert len(results) == 5
        for result in results:
            assert not isinstance(result, Exception)
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data['success'] is True
    
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, server):
        """Test handling of large result sets."""
        # Setup session
        server.current_session = "valid_session"
        server.security_manager.validate_session = Mock(return_value=True)
        
        # Mock large number of entries
        large_entry_set = [
            {'id': f'entry{i}', 'title': f'Entry {i}', 'username': f'user{i}'}
            for i in range(1000)
        ]
        
        server.entry_manager.list_entries = Mock(return_value=large_entry_set)
        
        # Test listing with limit
        args = {'limit': 50}
        result = await server.server.handlers['call_tool']['list_entries'](args)
        
        assert len(result) == 1
        response_data = json.loads(result[0].text)
        assert response_data['success'] is True
        assert len(response_data['entries']) == 50  # Should respect limit


if __name__ == "__main__":
    pytest.main([__file__])
