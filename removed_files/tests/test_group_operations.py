"""
Test group operations for KeePass MCP Server.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from keepass_mcp_server.group_manager import GroupManager
from keepass_mcp_server.exceptions import (
    GroupNotFoundError,
    ValidationError,
    ReadOnlyModeError
)


class TestGroupManager:
    """Test cases for GroupManager."""
    
    @pytest.fixture
    def mock_keepass_handler(self):
        """Mock KeePass handler for testing."""
        handler = Mock()
        handler.get_group_by_id.return_value = None
        handler.get_group_by_name.return_value = None
        handler.get_all_groups.return_value = []
        handler.get_root_group.return_value = Mock(name="Root")
        return handler
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.is_read_only.return_value = False
        return config
    
    @pytest.fixture
    def group_manager(self, mock_keepass_handler, mock_config):
        """Create GroupManager instance for testing."""
        return GroupManager(mock_keepass_handler, mock_config)
    
    def test_create_group_success(self, group_manager, mock_keepass_handler):
        """Test successful group creation."""
        # Setup mocks
        mock_parent_group = Mock()
        mock_parent_group.name = "Parent Group"
        
        mock_new_group = Mock()
        mock_new_group.uuid = "new-group-uuid"
        mock_new_group.name = "New Group"
        mock_new_group.notes = "Test notes"
        mock_new_group.icon = 48
        mock_new_group.parent = mock_parent_group
        mock_new_group.ctime = datetime.now()
        mock_new_group.mtime = datetime.now()
        
        mock_keepass_handler.get_root_group.return_value = mock_parent_group
        mock_keepass_handler.create_group.return_value = mock_new_group
        mock_keepass_handler.get_subgroups.return_value = []
        
        # Test group creation
        result = group_manager.create_group(
            name="New Group",
            notes="Test notes",
            icon=48
        )
        
        # Assertions
        assert result['name'] == "New Group"
        assert result['notes'] == "Test notes"
        assert result['icon'] == 48
        mock_keepass_handler.create_group.assert_called_once()
    
    def test_create_group_readonly_mode(self, group_manager, mock_config):
        """Test group creation in read-only mode."""
        mock_config.is_read_only.return_value = True
        
        with pytest.raises(ReadOnlyModeError):
            group_manager.create_group(name="Test Group")
    
    def test_create_group_invalid_name(self, group_manager):
        """Test group creation with invalid name."""
        with pytest.raises(ValidationError):
            group_manager.create_group(name="")
    
    def test_create_group_duplicate_name(self, group_manager, mock_keepass_handler):
        """Test group creation with duplicate name in parent."""
        # Setup existing group
        mock_existing_group = Mock()
        mock_existing_group.name = "Existing Group"
        
        mock_parent_group = Mock()
        mock_parent_group.name = "Parent"
        
        mock_keepass_handler.get_root_group.return_value = mock_parent_group
        mock_keepass_handler.get_subgroups.return_value = [mock_existing_group]
        
        with pytest.raises(ValidationError, match="already exists"):
            group_manager.create_group(name="Existing Group")
    
    def test_get_group_by_id_success(self, group_manager, mock_keepass_handler):
        """Test successful group retrieval by ID."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        mock_group.notes = "Test notes"
        mock_group.icon = 48
        mock_group.parent = None
        mock_group.ctime = datetime.now()
        mock_group.mtime = datetime.now()
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        
        result = group_manager.get_group(group_id="test-group-uuid")
        
        assert result['id'] == "test-group-uuid"
        assert result['name'] == "Test Group"
        mock_keepass_handler.get_group_by_id.assert_called_with("test-group-uuid")
    
    def test_get_group_by_name_success(self, group_manager, mock_keepass_handler):
        """Test successful group retrieval by name."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        mock_group.notes = "Test notes"
        mock_group.icon = 48
        mock_group.parent = None
        mock_group.ctime = datetime.now()
        mock_group.mtime = datetime.now()
        
        mock_keepass_handler.get_group_by_name.return_value = mock_group
        
        result = group_manager.get_group(group_name="Test Group")
        
        assert result['name'] == "Test Group"
        mock_keepass_handler.get_group_by_name.assert_called_with("Test Group")
    
    def test_get_group_not_found(self, group_manager, mock_keepass_handler):
        """Test group retrieval when group doesn't exist."""
        mock_keepass_handler.get_group_by_id.return_value = None
        
        with pytest.raises(GroupNotFoundError):
            group_manager.get_group(group_id="nonexistent-uuid")
    
    def test_get_group_no_identifier(self, group_manager):
        """Test group retrieval without ID or name."""
        with pytest.raises(ValidationError):
            group_manager.get_group()
    
    def test_update_group_success(self, group_manager, mock_keepass_handler):
        """Test successful group update."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Updated Group"
        mock_group.notes = "Updated notes"
        mock_group.icon = 50
        mock_group.parent = Mock()
        mock_group.ctime = datetime.now()
        mock_group.mtime = datetime.now()
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        mock_keepass_handler.update_group.return_value = mock_group
        mock_keepass_handler.get_subgroups.return_value = []
        
        result = group_manager.update_group(
            group_id="test-group-uuid",
            new_name="Updated Group",
            notes="Updated notes",
            icon=50
        )
        
        assert result['name'] == "Updated Group"
        assert result['notes'] == "Updated notes"
        assert result['icon'] == 50
        mock_keepass_handler.update_group.assert_called_once()
    
    def test_update_group_readonly_mode(self, group_manager, mock_config):
        """Test group update in read-only mode."""
        mock_config.is_read_only.return_value = True
        
        with pytest.raises(ReadOnlyModeError):
            group_manager.update_group(group_id="test-uuid", new_name="New Name")
    
    def test_delete_group_success(self, group_manager, mock_keepass_handler):
        """Test successful group deletion."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        
        mock_root_group = Mock()
        mock_root_group.name = "Root"
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        mock_keepass_handler.get_entries_in_group.return_value = []
        
        # Mock subgroups attribute
        mock_group.subgroups = []
        
        result = group_manager.delete_group(group_id="test-group-uuid", force=True)
        
        assert result['success'] is True
        assert result['name'] == "Test Group"
        mock_keepass_handler.delete_group.assert_called_with(mock_group, True)
    
    def test_delete_root_group_forbidden(self, group_manager, mock_keepass_handler):
        """Test that deleting root group is forbidden."""
        mock_root_group = Mock()
        mock_root_group.name = "Root"
        
        mock_keepass_handler.get_group_by_id.return_value = mock_root_group
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        
        with pytest.raises(ValidationError, match="Cannot delete root group"):
            group_manager.delete_group(group_id="root-uuid")
    
    def test_delete_group_with_content_no_force(self, group_manager, mock_keepass_handler):
        """Test group deletion with content but no force flag."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        mock_group.subgroups = []
        
        mock_root_group = Mock()
        mock_root_group.name = "Root"
        
        mock_entries = [Mock(), Mock()]  # 2 entries
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        mock_keepass_handler.get_entries_in_group.return_value = mock_entries
        
        with pytest.raises(ValidationError, match="contains 2 entries"):
            group_manager.delete_group(group_id="test-group-uuid", force=False)
    
    def test_move_group_success(self, group_manager, mock_keepass_handler):
        """Test successful group move."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        mock_group.parent = Mock(name="Old Parent")
        
        mock_target_parent = Mock()
        mock_target_parent.name = "New Parent"
        
        mock_root_group = Mock()
        mock_root_group.name = "Root"
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        mock_keepass_handler.get_group_by_name.return_value = mock_target_parent
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        mock_keepass_handler.get_subgroups.return_value = []  # No name conflicts
        
        result = group_manager.move_group(
            group_id="test-group-uuid",
            target_parent_name="New Parent"
        )
        
        assert result['success'] is True
        assert result['old_parent'] == "Old Parent"
        assert result['new_parent'] == "New Parent"
        mock_keepass_handler.move_group.assert_called_with(mock_group, mock_target_parent)
    
    def test_move_root_group_forbidden(self, group_manager, mock_keepass_handler):
        """Test that moving root group is forbidden."""
        mock_root_group = Mock()
        mock_root_group.name = "Root"
        
        mock_keepass_handler.get_group_by_id.return_value = mock_root_group
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        
        with pytest.raises(ValidationError, match="Cannot move root group"):
            group_manager.move_group(group_id="root-uuid", target_parent_name="Target")
    
    def test_list_groups_success(self, group_manager, mock_keepass_handler):
        """Test successful group listing."""
        mock_groups = [
            Mock(uuid="uuid1", name="Group 1", notes="Notes 1", icon=48,
                 parent=None, ctime=datetime.now(), mtime=datetime.now()),
            Mock(uuid="uuid2", name="Group 2", notes="Notes 2", icon=49,
                 parent=None, ctime=datetime.now(), mtime=datetime.now())
        ]
        
        mock_keepass_handler.get_all_groups.return_value = mock_groups
        mock_keepass_handler.get_root_group.return_value = mock_groups[0]
        
        results = group_manager.list_groups(include_root=True)
        
        assert len(results) == 2
        assert results[0]['name'] == "Group 1"
        assert results[1]['name'] == "Group 2"
    
    def test_list_groups_exclude_root(self, group_manager, mock_keepass_handler):
        """Test group listing excluding root group."""
        mock_root_group = Mock(uuid="root-uuid", name="Root")
        mock_other_group = Mock(uuid="other-uuid", name="Other Group", 
                               parent=None, ctime=datetime.now(), mtime=datetime.now(),
                               notes="", icon=48)
        
        mock_keepass_handler.get_all_groups.return_value = [mock_root_group, mock_other_group]
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        
        results = group_manager.list_groups(include_root=False)
        
        assert len(results) == 1
        assert results[0]['name'] == "Other Group"
    
    def test_get_group_hierarchy(self, group_manager, mock_keepass_handler):
        """Test group hierarchy retrieval."""
        # Setup hierarchy: Root -> Parent -> Child
        mock_child_group = Mock()
        mock_child_group.uuid = "child-uuid"
        mock_child_group.name = "Child Group"
        mock_child_group.notes = ""
        mock_child_group.icon = 48
        mock_child_group.parent = None  # Will be set below
        mock_child_group.ctime = datetime.now()
        mock_child_group.mtime = datetime.now()
        
        mock_parent_group = Mock()
        mock_parent_group.uuid = "parent-uuid"
        mock_parent_group.name = "Parent Group"
        mock_parent_group.notes = ""
        mock_parent_group.icon = 48
        mock_parent_group.parent = None  # Will be set below
        mock_parent_group.ctime = datetime.now()
        mock_parent_group.mtime = datetime.now()
        
        mock_root_group = Mock()
        mock_root_group.uuid = "root-uuid"
        mock_root_group.name = "Root"
        mock_root_group.notes = ""
        mock_root_group.icon = 48
        mock_root_group.parent = None
        mock_root_group.ctime = datetime.now()
        mock_root_group.mtime = datetime.now()
        
        # Set up parent relationships
        mock_child_group.parent = mock_parent_group
        mock_parent_group.parent = mock_root_group
        
        # Setup subgroups
        mock_keepass_handler.get_root_group.return_value = mock_root_group
        mock_keepass_handler.get_subgroups.side_effect = [
            [mock_parent_group],  # Root has Parent
            [mock_child_group],   # Parent has Child
            []                    # Child has no subgroups
        ]
        
        result = group_manager.get_group_hierarchy()
        
        assert result['name'] == "Root"
        assert 'children' in result
    
    def test_get_group_statistics(self, group_manager, mock_keepass_handler):
        """Test group statistics calculation."""
        mock_group = Mock()
        mock_group.uuid = "test-group-uuid"
        mock_group.name = "Test Group"
        
        # Mock entries with different characteristics
        mock_entries = [
            Mock(password="StrongPass123!", url="https://example.com", notes="Notes",
                 ctime=datetime.now(), mtime=datetime.now()),
            Mock(password="weak", url="", notes="",
                 ctime=datetime.now(), mtime=datetime.now()),
            Mock(password="", url="https://test.com", notes="More notes",
                 ctime=datetime.now(), mtime=datetime.now())
        ]
        
        mock_subgroups = [Mock(), Mock()]  # 2 subgroups
        
        mock_keepass_handler.get_group_by_id.return_value = mock_group
        mock_keepass_handler.get_entries_in_group.return_value = mock_entries
        mock_keepass_handler.get_subgroups.return_value = mock_subgroups
        
        result = group_manager.get_group_statistics(group_id="test-group-uuid")
        
        assert result['group_name'] == "Test Group"
        assert result['total_entries'] == 3
        assert result['total_subgroups'] == 2
        assert result['entries_with_passwords'] == 2  # Only 2 have passwords
        assert result['entries_without_passwords'] == 1
        assert result['entries_with_urls'] == 2
        assert 'password_strength' in result
        assert 'recent_activity' in result
    
    def test_group_path_calculation(self, group_manager):
        """Test group path calculation."""
        # Create hierarchy: Root -> Work -> Projects
        mock_projects_group = Mock()
        mock_projects_group.name = "Projects"
        
        mock_work_group = Mock()
        mock_work_group.name = "Work"
        
        mock_root_group = Mock()
        mock_root_group.name = ""  # Root often has empty name
        
        # Set up parent relationships
        mock_projects_group.parent = mock_work_group
        mock_work_group.parent = mock_root_group
        mock_root_group.parent = None
        
        path = group_manager._get_group_path(mock_projects_group)
        assert path == "/Work/Projects"
    
    def test_circular_reference_detection(self, group_manager):
        """Test circular reference detection."""
        # Create potential circular reference
        mock_group_a = Mock()
        mock_group_a.name = "Group A"
        
        mock_group_b = Mock()
        mock_group_b.name = "Group B"
        mock_group_b.parent = mock_group_a
        
        mock_group_c = Mock()
        mock_group_c.name = "Group C"
        mock_group_c.parent = mock_group_b
        
        # Test moving Group A under Group C (would create circular reference)
        circular = group_manager._would_create_circular_reference(mock_group_a, mock_group_c)
        assert circular is True
        
        # Test valid move
        mock_group_d = Mock()
        mock_group_d.name = "Group D"
        mock_group_d.parent = None
        
        not_circular = group_manager._would_create_circular_reference(mock_group_a, mock_group_d)
        assert not_circular is False


class TestGroupManagerIntegration:
    """Integration tests for GroupManager."""
    
    def test_complete_group_lifecycle(self):
        """Test complete group lifecycle: create, update, move, delete."""
        mock_handler = Mock()
        mock_config = Mock()
        mock_config.is_read_only.return_value = False
        
        group_manager = GroupManager(mock_handler, mock_config)
        
        # Create group
        mock_new_group = Mock()
        mock_new_group.uuid = "new-uuid"
        mock_new_group.name = "New Group"
        mock_new_group.notes = "Initial notes"
        mock_new_group.icon = 48
        mock_new_group.parent = Mock(name="Root")
        mock_new_group.ctime = datetime.now()
        mock_new_group.mtime = datetime.now()
        
        mock_handler.get_root_group.return_value = mock_new_group.parent
        mock_handler.create_group.return_value = mock_new_group
        mock_handler.get_subgroups.return_value = []
        
        # Step 1: Create
        create_result = group_manager.create_group(
            name="New Group",
            notes="Initial notes"
        )
        assert create_result['name'] == "New Group"
        
        # Step 2: Update
        mock_new_group.name = "Updated Group"
        mock_new_group.notes = "Updated notes"
        mock_handler.get_group_by_id.return_value = mock_new_group
        mock_handler.update_group.return_value = mock_new_group
        
        update_result = group_manager.update_group(
            group_id="new-uuid",
            new_name="Updated Group",
            notes="Updated notes"
        )
        assert update_result['name'] == "Updated Group"
        
        # Step 3: Delete
        mock_handler.get_entries_in_group.return_value = []
        mock_new_group.subgroups = []
        
        delete_result = group_manager.delete_group(
            group_id="new-uuid",
            force=True
        )
        assert delete_result['success'] is True


if __name__ == "__main__":
    pytest.main([__file__])
