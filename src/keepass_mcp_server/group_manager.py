"""
Group management for KeePass database operations.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from .exceptions import (
    GroupNotFoundError,
    ValidationError,
    ReadOnlyModeError,
    ConcurrentAccessError
)
from .validators import Validators


class GroupManager:
    """Manages KeePass database groups with full CRUD operations."""
    
    def __init__(self, keepass_handler, config):
        self.keepass_handler = keepass_handler
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def create_group(
        self,
        name: str,
        parent_group_id: str = None,
        parent_group_name: str = None,
        notes: str = "",
        icon: int = 48,  # Default folder icon
        expires: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a new group in the KeePass database.
        
        Args:
            name: Name of the new group
            parent_group_id: ID of the parent group
            parent_group_name: Name of the parent group (alternative to ID)
            notes: Notes for the group
            icon: Icon number for the group
            expires: Expiration date for the group
            
        Returns:
            Dictionary containing the created group information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            ValidationError: If validation fails
            GroupNotFoundError: If parent group doesn't exist
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("create_group")
            
            # Validate inputs
            name = Validators.validate_group_name(name)
            notes = Validators.validate_notes(notes)
            
            # Check if group already exists in parent
            parent_group = self._resolve_parent_group(parent_group_id, parent_group_name)
            
            if self._group_exists_in_parent(name, parent_group):
                raise ValidationError(f"Group '{name}' already exists in parent group")
            
            # Create group data
            group_data = {
                'name': name,
                'notes': notes,
                'icon': icon,
                'expires': expires
            }
            
            # Create group in KeePass database
            created_group = self.keepass_handler.create_group(parent_group, group_data)
            
            # Log the operation
            parent_name = parent_group.name if parent_group else "Root"
            self.logger.info(f"Group created: {name} in {parent_name}")
            
            return self._format_group_response(created_group)
            
        except Exception as e:
            self.logger.error(f"Failed to create group '{name}': {e}")
            raise
    
    def get_group(
        self,
        group_id: str = None,
        group_name: str = None,
        include_entries: bool = False,
        include_subgroups: bool = True,
        include_statistics: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve a specific group by ID or name.
        
        Args:
            group_id: UUID of the group
            group_name: Name of the group (alternative to ID)
            include_entries: Whether to include group entries
            include_subgroups: Whether to include subgroups
            include_statistics: Whether to include group statistics
            
        Returns:
            Dictionary containing group information
            
        Raises:
            GroupNotFoundError: If group not found
            ValidationError: If parameters are invalid
        """
        try:
            group = self._resolve_group(group_id, group_name)
            
            response = self._format_group_response(
                group,
                include_entries=include_entries,
                include_subgroups=include_subgroups,
                include_statistics=include_statistics
            )
            
            return response
            
        except Exception as e:
            identifier = group_id or group_name or "unknown"
            if not isinstance(e, (GroupNotFoundError, ValidationError)):
                self.logger.error(f"Failed to get group {identifier}: {e}")
            raise
    
    def update_group(
        self,
        group_id: str = None,
        group_name: str = None,
        new_name: str = None,
        notes: str = None,
        icon: int = None,
        expires: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Update an existing group.
        
        Args:
            group_id: UUID of the group to update
            group_name: Name of the group to update (alternative to ID)
            new_name: New name for the group (optional)
            notes: New notes (optional)
            icon: New icon number (optional)
            expires: New expiration date (optional)
            
        Returns:
            Dictionary containing updated group information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            GroupNotFoundError: If group not found
            ValidationError: If validation fails
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("update_group")
            
            group = self._resolve_group(group_id, group_name)
            
            # Prepare update data
            update_data = {}
            
            if new_name is not None:
                new_name = Validators.validate_group_name(new_name)
                # Check if new name conflicts with siblings
                if self._group_exists_in_parent(new_name, group.parent, exclude_group=group):
                    raise ValidationError(f"Group '{new_name}' already exists in parent group")
                update_data['name'] = new_name
            
            if notes is not None:
                update_data['notes'] = Validators.validate_notes(notes)
            
            if icon is not None:
                update_data['icon'] = icon
            
            if expires is not None:
                update_data['expires'] = expires
            
            # Update group in database
            updated_group = self.keepass_handler.update_group(group, update_data)
            
            # Log the operation
            group_name_for_log = update_data.get('name', group.name)
            self.logger.info(f"Group updated: {group_name_for_log}")
            
            return self._format_group_response(updated_group)
            
        except Exception as e:
            identifier = group_id or group_name or "unknown"
            self.logger.error(f"Failed to update group {identifier}: {e}")
            raise
    
    def delete_group(
        self,
        group_id: str = None,
        group_name: str = None,
        force: bool = False,
        move_entries_to: str = None
    ) -> Dict[str, Any]:
        """
        Delete a group from the database.
        
        Args:
            group_id: UUID of the group to delete
            group_name: Name of the group to delete (alternative to ID)
            force: Whether to force deletion even if group has entries/subgroups
            move_entries_to: Group ID to move entries to before deletion
            
        Returns:
            Dictionary with deletion information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            GroupNotFoundError: If group not found
            ValidationError: If group has content and force=False
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("delete_group")
            
            group = self._resolve_group(group_id, group_name)
            
            # Check if group is root group
            if group == self.keepass_handler.get_root_group():
                raise ValidationError("Cannot delete root group")
            
            group_name_for_log = group.name
            
            # Check if group has content
            entries_count = len(self.keepass_handler.get_entries_in_group(group, include_subgroups=False))
            subgroups_count = len(group.subgroups) if hasattr(group, 'subgroups') else 0
            
            if (entries_count > 0 or subgroups_count > 0) and not force:
                if not move_entries_to:
                    raise ValidationError(
                        f"Group contains {entries_count} entries and {subgroups_count} subgroups. "
                        "Use force=True or specify move_entries_to parameter."
                    )
            
            # Move entries if specified
            moved_entries = 0
            if move_entries_to and entries_count > 0:
                target_group = self._resolve_group(move_entries_to)
                entries = self.keepass_handler.get_entries_in_group(group, include_subgroups=False)
                
                for entry in entries:
                    self.keepass_handler.move_entry(entry, target_group)
                    moved_entries += 1
            
            # Delete group
            self.keepass_handler.delete_group(group, force)
            
            # Log the operation
            self.logger.info(f"Group deleted: {group_name_for_log} (moved {moved_entries} entries)")
            
            return {
                'group_id': str(group.uuid) if hasattr(group, 'uuid') else None,
                'name': group_name_for_log,
                'deleted_at': datetime.now().isoformat(),
                'entries_moved': moved_entries,
                'target_group': move_entries_to,
                'forced': force,
                'success': True
            }
            
        except Exception as e:
            identifier = group_id or group_name or "unknown"
            self.logger.error(f"Failed to delete group {identifier}: {e}")
            raise
    
    def move_group(
        self,
        group_id: str = None,
        group_name: str = None,
        target_parent_id: str = None,
        target_parent_name: str = None
    ) -> Dict[str, Any]:
        """
        Move a group to a different parent group.
        
        Args:
            group_id: UUID of the group to move
            group_name: Name of the group to move (alternative to ID)
            target_parent_id: ID of the target parent group
            target_parent_name: Name of the target parent group (alternative to ID)
            
        Returns:
            Dictionary with move operation information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            GroupNotFoundError: If group or target parent not found
            ValidationError: If move would create a circular reference
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("move_group")
            
            group = self._resolve_group(group_id, group_name)
            target_parent = self._resolve_parent_group(target_parent_id, target_parent_name)
            
            # Check if group is root group
            if group == self.keepass_handler.get_root_group():
                raise ValidationError("Cannot move root group")
            
            # Check for circular reference
            if self._would_create_circular_reference(group, target_parent):
                raise ValidationError("Move would create circular reference")
            
            # Check if name conflicts in target parent
            if self._group_exists_in_parent(group.name, target_parent, exclude_group=group):
                raise ValidationError(f"Group '{group.name}' already exists in target parent")
            
            old_parent_name = group.parent.name if group.parent else "Root"
            new_parent_name = target_parent.name if target_parent else "Root"
            
            # Move group
            self.keepass_handler.move_group(group, target_parent)
            
            # Log the operation
            self.logger.info(f"Group moved: {group.name} from {old_parent_name} to {new_parent_name}")
            
            return {
                'group_id': str(group.uuid) if hasattr(group, 'uuid') else None,
                'name': group.name,
                'old_parent': old_parent_name,
                'new_parent': new_parent_name,
                'moved_at': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            identifier = group_id or group_name or "unknown"
            self.logger.error(f"Failed to move group {identifier}: {e}")
            raise
    
    def list_groups(
        self,
        parent_group_id: str = None,
        parent_group_name: str = None,
        include_root: bool = True,
        include_statistics: bool = False,
        recursive: bool = False,
        sort_by: str = "name"
    ) -> List[Dict[str, Any]]:
        """
        List groups in the database or under a specific parent.
        
        Args:
            parent_group_id: ID of parent group to list (optional)
            parent_group_name: Name of parent group to list (optional)
            include_root: Whether to include root group in results
            include_statistics: Whether to include group statistics
            recursive: Whether to include all descendant groups
            sort_by: Sort method (name, created, modified, entries_count)
            
        Returns:
            List of group dictionaries
        """
        try:
            # Get groups from specified parent or entire database
            if parent_group_id or parent_group_name:
                parent_group = self._resolve_group(parent_group_id, parent_group_name)
                groups = self.keepass_handler.get_subgroups(parent_group, recursive)
            else:
                groups = self.keepass_handler.get_all_groups()
                
                # Exclude root group if requested
                if not include_root:
                    root_group = self.keepass_handler.get_root_group()
                    groups = [g for g in groups if g != root_group]
            
            # Format groups
            formatted_groups = [
                self._format_group_response(group, include_statistics=include_statistics)
                for group in groups
            ]
            
            # Sort groups
            formatted_groups = self._sort_groups(formatted_groups, sort_by)
            
            return formatted_groups
            
        except Exception as e:
            self.logger.error(f"Failed to list groups: {e}")
            raise
    
    def get_group_hierarchy(
        self,
        group_id: str = None,
        group_name: str = None,
        max_depth: int = None
    ) -> Dict[str, Any]:
        """
        Get hierarchical structure of groups starting from specified group.
        
        Args:
            group_id: ID of starting group (defaults to root)
            group_name: Name of starting group (alternative to ID)
            max_depth: Maximum depth to traverse
            
        Returns:
            Hierarchical dictionary of groups
        """
        try:
            if group_id or group_name:
                start_group = self._resolve_group(group_id, group_name)
            else:
                start_group = self.keepass_handler.get_root_group()
            
            hierarchy = self._build_group_hierarchy(start_group, max_depth, 0)
            
            return hierarchy
            
        except Exception as e:
            identifier = group_id or group_name or "root"
            self.logger.error(f"Failed to get group hierarchy from {identifier}: {e}")
            raise
    
    def get_group_statistics(
        self,
        group_id: str = None,
        group_name: str = None,
        include_subgroups: bool = True
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a group.
        
        Args:
            group_id: ID of the group
            group_name: Name of the group (alternative to ID)
            include_subgroups: Whether to include statistics from subgroups
            
        Returns:
            Dictionary with group statistics
        """
        try:
            group = self._resolve_group(group_id, group_name)
            
            entries = self.keepass_handler.get_entries_in_group(group, include_subgroups)
            subgroups = self.keepass_handler.get_subgroups(group, include_subgroups)
            
            # Calculate statistics
            total_entries = len(entries)
            entries_with_passwords = sum(1 for entry in entries if entry.password)
            entries_with_urls = sum(1 for entry in entries if entry.url)
            entries_with_notes = sum(1 for entry in entries if entry.notes)
            
            # Password strength analysis
            weak_passwords = 0
            strong_passwords = 0
            
            for entry in entries:
                if entry.password:
                    # Simple strength check (could be enhanced)
                    if len(entry.password) >= 12 and any(c.isupper() for c in entry.password) and any(c.islower() for c in entry.password) and any(c.isdigit() for c in entry.password):
                        strong_passwords += 1
                    else:
                        weak_passwords += 1
            
            # Date analysis
            now = datetime.now()
            entries_created_last_30_days = sum(
                1 for entry in entries 
                if entry.ctime and (now - entry.ctime).days <= 30
            )
            entries_modified_last_30_days = sum(
                1 for entry in entries 
                if entry.mtime and (now - entry.mtime).days <= 30
            )
            
            statistics = {
                'group_id': str(group.uuid) if hasattr(group, 'uuid') else None,
                'group_name': group.name,
                'total_entries': total_entries,
                'total_subgroups': len(subgroups),
                'entries_with_passwords': entries_with_passwords,
                'entries_without_passwords': total_entries - entries_with_passwords,
                'entries_with_urls': entries_with_urls,
                'entries_with_notes': entries_with_notes,
                'password_strength': {
                    'weak_passwords': weak_passwords,
                    'strong_passwords': strong_passwords
                },
                'recent_activity': {
                    'created_last_30_days': entries_created_last_30_days,
                    'modified_last_30_days': entries_modified_last_30_days
                },
                'include_subgroups': include_subgroups,
                'calculated_at': datetime.now().isoformat()
            }
            
            return statistics
            
        except Exception as e:
            identifier = group_id or group_name or "unknown"
            self.logger.error(f"Failed to get group statistics for {identifier}: {e}")
            raise
    
    def _resolve_group(self, group_id: str = None, group_name: str = None):
        """Resolve group from ID or name."""
        if group_id:
            group_id = Validators.validate_uuid(group_id)
            group = self.keepass_handler.get_group_by_id(group_id)
            if not group:
                raise GroupNotFoundError(group_id)
            return group
        
        elif group_name:
            group_name = Validators.validate_group_name(group_name)
            group = self.keepass_handler.get_group_by_name(group_name)
            if not group:
                raise GroupNotFoundError(group_name)
            return group
        
        else:
            raise ValidationError("Either group_id or group_name must be provided")
    
    def _resolve_parent_group(self, parent_group_id: str = None, parent_group_name: str = None):
        """Resolve parent group from ID or name, defaults to root."""
        if parent_group_id or parent_group_name:
            return self._resolve_group(parent_group_id, parent_group_name)
        else:
            return self.keepass_handler.get_root_group()
    
    def _group_exists_in_parent(self, name: str, parent_group, exclude_group=None) -> bool:
        """Check if a group with the given name exists in the parent group."""
        try:
            subgroups = self.keepass_handler.get_subgroups(parent_group, recursive=False)
            
            for group in subgroups:
                if group == exclude_group:
                    continue
                if group.name.lower() == name.lower():
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _would_create_circular_reference(self, group, target_parent) -> bool:
        """Check if moving group to target_parent would create circular reference."""
        # Check if target_parent is a descendant of group
        current = target_parent
        while current:
            if current == group:
                return True
            current = current.parent if hasattr(current, 'parent') else None
        
        return False
    
    def _format_group_response(
        self,
        group,
        include_entries: bool = False,
        include_subgroups: bool = False,
        include_statistics: bool = False
    ) -> Dict[str, Any]:
        """Format group object for API response."""
        response = {
            'id': str(group.uuid) if hasattr(group, 'uuid') else None,
            'name': group.name,
            'notes': group.notes if hasattr(group, 'notes') else "",
            'icon': group.icon if hasattr(group, 'icon') else 48,
            'parent_id': str(group.parent.uuid) if hasattr(group, 'parent') and group.parent else None,
            'parent_name': group.parent.name if hasattr(group, 'parent') and group.parent else None,
            'created': group.ctime.isoformat() if hasattr(group, 'ctime') and group.ctime else None,
            'modified': group.mtime.isoformat() if hasattr(group, 'mtime') and group.mtime else None,
            'expires': group.expires.isoformat() if hasattr(group, 'expires') and group.expires else None,
            'path': self._get_group_path(group)
        }
        
        if include_entries:
            entries = self.keepass_handler.get_entries_in_group(group, include_subgroups=False)
            response['entries'] = [
                {
                    'id': str(entry.uuid),
                    'title': entry.title,
                    'username': entry.username,
                    'url': entry.url
                }
                for entry in entries
            ]
            response['entries_count'] = len(entries)
        
        if include_subgroups:
            subgroups = self.keepass_handler.get_subgroups(group, recursive=False)
            response['subgroups'] = [
                {
                    'id': str(subgroup.uuid) if hasattr(subgroup, 'uuid') else None,
                    'name': subgroup.name
                }
                for subgroup in subgroups
            ]
            response['subgroups_count'] = len(subgroups)
        
        if include_statistics:
            try:
                stats = self.get_group_statistics(str(group.uuid) if hasattr(group, 'uuid') else None, group.name)
                response['statistics'] = stats
            except:
                response['statistics'] = None
        
        return response
    
    def _get_group_path(self, group) -> str:
        """Get full path of group from root."""
        path_parts = []
        current = group
        
        while current:
            if current.name:  # Skip if root group has no name
                path_parts.append(current.name)
            current = current.parent if hasattr(current, 'parent') else None
        
        path_parts.reverse()
        return '/' + '/'.join(path_parts) if path_parts else '/'
    
    def _build_group_hierarchy(self, group, max_depth: int = None, current_depth: int = 0) -> Dict[str, Any]:
        """Build hierarchical structure of groups recursively."""
        hierarchy = self._format_group_response(group)
        
        # Add children if within depth limit
        if max_depth is None or current_depth < max_depth:
            subgroups = self.keepass_handler.get_subgroups(group, recursive=False)
            hierarchy['children'] = [
                self._build_group_hierarchy(subgroup, max_depth, current_depth + 1)
                for subgroup in subgroups
            ]
        else:
            hierarchy['children'] = []
        
        return hierarchy
    
    def _sort_groups(self, groups: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort groups by specified criteria."""
        if sort_by == "name":
            return sorted(groups, key=lambda x: x.get('name', '').lower())
        elif sort_by == "created":
            return sorted(groups, key=lambda x: x.get('created', ''), reverse=True)
        elif sort_by == "modified":
            return sorted(groups, key=lambda x: x.get('modified', ''), reverse=True)
        elif sort_by == "entries_count":
            return sorted(groups, key=lambda x: x.get('entries_count', 0), reverse=True)
        else:
            return groups
