"""
Test entry operations for KeePass MCP Server.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from keepass_mcp_server.entry_manager import EntryManager
from keepass_mcp_server.exceptions import (
    EntryNotFoundError,
    ValidationError,
    ReadOnlyModeError,
    DuplicateEntryError
)


class TestEntryManager:
    """Test cases for EntryManager."""
    
    @pytest.fixture
    def mock_keepass_handler(self):
        """Mock KeePass handler for testing."""
        handler = Mock()
        handler.get_entry_by_id.return_value = None
        handler.get_all_entries.return_value = []
        handler.get_root_group.return_value = Mock()
        return handler
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.is_read_only.return_value = False
        return config
    
    @pytest.fixture
    def entry_manager(self, mock_keepass_handler, mock_config):
        """Create EntryManager instance for testing."""
        return EntryManager(mock_keepass_handler, mock_config)
    
    def test_create_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry creation."""
        # Setup mock
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        mock_entry.username = "testuser"
        mock_entry.password = "testpass"
        mock_entry.url = "https://test.com"
        mock_entry.notes = "Test notes"
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        mock_entry.group = Mock()
        mock_entry.group.name = "Test Group"
        mock_entry.group.uuid = "group-uuid"
        
        mock_keepass_handler.create_entry.return_value = mock_entry
        mock_keepass_handler.get_root_group.return_value = mock_entry.group
        
        # Test entry creation
        result = entry_manager.create_entry(
            title="Test Entry",
            username="testuser",
            password="testpass",
            url="https://test.com",
            notes="Test notes"
        )
        
        # Assertions
        assert result['title'] == "Test Entry"
        assert result['username'] == "testuser"
        assert result['url'] == "https://test.com"
        mock_keepass_handler.create_entry.assert_called_once()
    
    def test_create_entry_readonly_mode(self, entry_manager, mock_config):
        """Test entry creation in read-only mode."""
        mock_config.is_read_only.return_value = True
        
        with pytest.raises(ReadOnlyModeError):
            entry_manager.create_entry(title="Test Entry")
    
    def test_create_entry_invalid_title(self, entry_manager):
        """Test entry creation with invalid title."""
        with pytest.raises(ValidationError):
            entry_manager.create_entry(title="")
    
    def test_create_entry_with_password_generation(self, entry_manager, mock_keepass_handler):
        """Test entry creation with password generation."""
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        mock_entry.password = "GeneratedPassword123!"
        mock_entry.group = Mock()
        mock_entry.group.name = "Test Group"
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        
        mock_keepass_handler.create_entry.return_value = mock_entry
        mock_keepass_handler.get_root_group.return_value = mock_entry.group
        
        result = entry_manager.create_entry(
            title="Test Entry",
            generate_password=True,
            password_options={'length': 16}
        )
        
        assert len(result['password']) >= 16  # Password was generated
        mock_keepass_handler.create_entry.assert_called_once()
    
    def test_get_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry retrieval."""
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        mock_entry.username = "testuser"
        mock_entry.password = "testpass"
        mock_entry.url = "https://test.com"
        mock_entry.notes = "Test notes"
        mock_entry.group = Mock()
        mock_entry.group.name = "Test Group"
        mock_entry.group.uuid = "group-uuid"
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        
        mock_keepass_handler.get_entry_by_id.return_value = mock_entry
        
        result = entry_manager.get_entry("test-uuid", include_password=True)
        
        assert result['id'] == "test-uuid"
        assert result['title'] == "Test Entry"
        assert 'password' in result
        mock_keepass_handler.get_entry_by_id.assert_called_with("test-uuid")
    
    def test_get_entry_not_found(self, entry_manager, mock_keepass_handler):
        """Test entry retrieval when entry doesn't exist."""
        mock_keepass_handler.get_entry_by_id.return_value = None
        
        with pytest.raises(EntryNotFoundError):
            entry_manager.get_entry("nonexistent-uuid")
    
    def test_update_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry update."""
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Updated Entry"
        mock_entry.username = "updateduser"
        mock_entry.group = Mock()
        mock_entry.group.name = "Test Group"
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        
        mock_keepass_handler.get_entry_by_id.return_value = mock_entry
        mock_keepass_handler.update_entry.return_value = mock_entry
        
        result = entry_manager.update_entry(
            "test-uuid",
            title="Updated Entry",
            username="updateduser"
        )
        
        assert result['title'] == "Updated Entry"
        assert result['username'] == "updateduser"
        mock_keepass_handler.update_entry.assert_called_once()
    
    def test_update_entry_readonly_mode(self, entry_manager, mock_config):
        """Test entry update in read-only mode."""
        mock_config.is_read_only.return_value = True
        
        with pytest.raises(ReadOnlyModeError):
            entry_manager.update_entry("test-uuid", title="New Title")
    
    def test_delete_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry deletion."""
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        
        mock_keepass_handler.get_entry_by_id.return_value = mock_entry
        
        result = entry_manager.delete_entry("test-uuid", permanent=False)
        
        assert result['success'] is True
        assert result['permanent'] is False
        mock_keepass_handler.delete_entry.assert_called_with(mock_entry, False)
    
    def test_delete_entry_readonly_mode(self, entry_manager, mock_config):
        """Test entry deletion in read-only mode."""
        mock_config.is_read_only.return_value = True
        
        with pytest.raises(ReadOnlyModeError):
            entry_manager.delete_entry("test-uuid")
    
    def test_move_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry move."""
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        mock_entry.group = Mock()
        mock_entry.group.name = "Old Group"
        
        mock_target_group = Mock()
        mock_target_group.name = "New Group"
        
        mock_keepass_handler.get_entry_by_id.return_value = mock_entry
        mock_keepass_handler.get_group_by_name.return_value = mock_target_group
        
        result = entry_manager.move_entry("test-uuid", target_group_name="New Group")
        
        assert result['success'] is True
        assert result['old_group'] == "Old Group"
        assert result['new_group'] == "New Group"
        mock_keepass_handler.move_entry.assert_called_with(mock_entry, mock_target_group)
    
    def test_duplicate_entry_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry duplication."""
        mock_source_entry = Mock()
        mock_source_entry.uuid = "source-uuid"
        mock_source_entry.title = "Original Entry"
        mock_source_entry.username = "testuser"
        mock_source_entry.password = "testpass"
        mock_source_entry.url = "https://test.com"
        mock_source_entry.notes = "Test notes"
        mock_source_entry.group = Mock()
        mock_source_entry.tags = []
        
        mock_duplicate_entry = Mock()
        mock_duplicate_entry.uuid = "duplicate-uuid"
        mock_duplicate_entry.title = "Copy of Original Entry"
        mock_duplicate_entry.username = "testuser"
        mock_duplicate_entry.password = "testpass"
        mock_duplicate_entry.url = "https://test.com"
        mock_duplicate_entry.notes = "Test notes"
        mock_duplicate_entry.group = mock_source_entry.group
        mock_duplicate_entry.ctime = datetime.now()
        mock_duplicate_entry.mtime = datetime.now()
        mock_duplicate_entry.atime = datetime.now()
        
        mock_keepass_handler.get_entry_by_id.return_value = mock_source_entry
        mock_keepass_handler.create_entry.return_value = mock_duplicate_entry
        
        result = entry_manager.duplicate_entry("source-uuid")
        
        assert result['title'] == "Copy of Original Entry"
        mock_keepass_handler.create_entry.assert_called_once()
    
    def test_list_entries_success(self, entry_manager, mock_keepass_handler):
        """Test successful entry listing."""
        mock_entries = [
            Mock(uuid="uuid1", title="Entry 1", username="user1", url="url1", 
                 notes="notes1", group=Mock(name="Group1", uuid="group1"),
                 ctime=datetime.now(), mtime=datetime.now(), atime=datetime.now()),
            Mock(uuid="uuid2", title="Entry 2", username="user2", url="url2", 
                 notes="notes2", group=Mock(name="Group2", uuid="group2"),
                 ctime=datetime.now(), mtime=datetime.now(), atime=datetime.now())
        ]
        
        mock_keepass_handler.get_all_entries.return_value = mock_entries
        
        results = entry_manager.list_entries()
        
        assert len(results) == 2
        assert results[0]['title'] == "Entry 1"
        assert results[1]['title'] == "Entry 2"
    
    def test_validate_entries(self, entry_manager, mock_keepass_handler):
        """Test entry validation."""
        mock_entries = [
            Mock(uuid="uuid1", title="Good Entry", password="StrongPassword123!", 
                 url="https://example.com", notes="Notes",
                 group=Mock(name="Group1")),
            Mock(uuid="uuid2", title="Weak Entry", password="weak", 
                 url="", notes="",
                 group=Mock(name="Group2"))
        ]
        
        mock_keepass_handler.get_all_entries.return_value = mock_entries
        
        results = entry_manager.validate_entries()
        
        assert results['total_entries'] == 2
        assert len(results['weak_passwords']) > 0
        assert len(results['missing_urls']) > 0
        assert 'summary' in results


class TestEntryManagerIntegration:
    """Integration tests for EntryManager with real-like scenarios."""
    
    @pytest.fixture
    def realistic_entry_manager(self):
        """Create a more realistic entry manager setup."""
        mock_handler = Mock()
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        
        return EntryManager(mock_handler, mock_config)
    
    def test_create_entry_workflow(self, realistic_entry_manager):
        """Test complete entry creation workflow."""
        handler = realistic_entry_manager.keepass_handler
        
        # Mock successful creation
        mock_entry = Mock()
        mock_entry.uuid = "new-uuid"
        mock_entry.title = "GitHub"
        mock_entry.username = "developer"
        mock_entry.password = "GeneratedPassword123!"
        mock_entry.url = "https://github.com"
        mock_entry.notes = "Development account"
        mock_entry.group = Mock(name="Development", uuid="dev-group")
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        
        handler.create_entry.return_value = mock_entry
        handler.get_group_by_name.return_value = mock_entry.group
        
        # Test the workflow
        result = realistic_entry_manager.create_entry(
            title="GitHub",
            username="developer",
            url="https://github.com",
            notes="Development account",
            group_name="Development",
            generate_password=True,
            password_options={'length': 20, 'include_symbols': True}
        )
        
        # Verify result
        assert result['title'] == "GitHub"
        assert result['username'] == "developer"
        assert result['url'] == "https://github.com"
        assert result['group'] == "Development"
        assert len(result['password']) >= 20
        
        # Verify handler was called correctly
        handler.create_entry.assert_called_once()
        call_args = handler.create_entry.call_args[1]
        assert call_args['title'] == "GitHub"
        assert call_args['username'] == "developer"
        assert call_args['url'] == "https://github.com"


@pytest.mark.asyncio
class TestEntryManagerAsync:
    """Async tests for EntryManager operations."""
    
    async def test_concurrent_operations(self):
        """Test that concurrent operations are handled safely."""
        mock_handler = Mock()
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        
        entry_manager = EntryManager(mock_handler, mock_config)
        
        # Mock successful operations
        mock_entry = Mock()
        mock_entry.uuid = "test-uuid"
        mock_entry.title = "Test Entry"
        mock_entry.group = Mock(name="Test Group")
        mock_entry.ctime = datetime.now()
        mock_entry.mtime = datetime.now()
        mock_entry.atime = datetime.now()
        
        mock_handler.get_entry_by_id.return_value = mock_entry
        mock_handler.update_entry.return_value = mock_entry
        
        # Simulate concurrent updates
        async def update_entry(field_name, field_value):
            return entry_manager.update_entry("test-uuid", **{field_name: field_value})
        
        # Run concurrent operations
        tasks = [
            asyncio.create_task(asyncio.to_thread(update_entry, "title", "New Title")),
            asyncio.create_task(asyncio.to_thread(update_entry, "username", "newuser")),
            asyncio.create_task(asyncio.to_thread(update_entry, "notes", "New notes"))
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)


if __name__ == "__main__":
    pytest.main([__file__])
