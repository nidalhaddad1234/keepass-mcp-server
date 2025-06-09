"""
Entry management for KeePass database operations.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
import logging

from .exceptions import (
    EntryNotFoundError,
    DuplicateEntryError,
    ValidationError,
    ReadOnlyModeError,
    GroupNotFoundError
)
from .validators import Validators
from .password_generator import PasswordGenerator


class EntryManager:
    """Manages KeePass database entries with full CRUD operations."""
    
    def __init__(self, keepass_handler, config):
        self.keepass_handler = keepass_handler
        self.config = config
        self.password_generator = PasswordGenerator()
        self.logger = logging.getLogger(__name__)
    
    def create_entry(
        self,
        title: str,
        username: str = "",
        password: str = "",
        url: str = "",
        notes: str = "",
        group_id: str = None,
        group_name: str = None,
        tags: List[str] = None,
        custom_fields: Dict[str, str] = None,
        generate_password: bool = False,
        password_options: Dict[str, Any] = None,
        expires: Optional[datetime] = None,
        icon: int = 0
    ) -> Dict[str, Any]:
        """
        Create a new entry in the KeePass database.
        
        Args:
            title: Entry title
            username: Username for the entry
            password: Password for the entry
            url: URL associated with the entry
            notes: Notes for the entry
            group_id: ID of the group to create entry in
            group_name: Name of the group (alternative to group_id)
            tags: List of tags for the entry
            custom_fields: Dictionary of custom fields
            generate_password: Whether to generate a password automatically
            password_options: Options for password generation
            expires: Expiration date for the entry
            icon: Icon number for the entry
            
        Returns:
            Dictionary containing the created entry information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            ValidationError: If validation fails
            DuplicateEntryError: If entry already exists
            GroupNotFoundError: If specified group doesn't exist
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("create_entry")
            
            # Validate inputs
            title = Validators.validate_entry_title(title)
            username = Validators.validate_username(username)
            url = Validators.validate_url(url) if url else ""
            notes = Validators.validate_notes(notes)
            tags = Validators.validate_tags(tags or [])
            custom_fields = Validators.validate_custom_fields(custom_fields or {})
            
            # Generate password if requested
            if generate_password:
                password_opts = password_options or {}
                password = self.password_generator.generate_password(**password_opts)
            else:
                password = Validators.validate_password(password)
            
            # Check for duplicates
            if self._check_duplicate_entry(title, username, url):
                raise DuplicateEntryError(title)
            
            # Find target group
            target_group = self._resolve_target_group(group_id, group_name)
            
            # Create entry in KeePass database
            entry_data = {
                'title': title,
                'username': username,
                'password': password,
                'url': url,
                'notes': notes,
                'tags': tags,
                'custom_fields': custom_fields,
                'expires': expires,
                'icon': icon
            }
            
            created_entry = self.keepass_handler.create_entry(target_group, entry_data)
            
            # Log the operation (without sensitive data)
            self.logger.info(f"Entry created: {title} in group {target_group.name}")
            
            return self._format_entry_response(created_entry)
            
        except Exception as e:
            self.logger.error(f"Failed to create entry '{title}': {e}")
            raise
    
    def get_entry(
        self,
        entry_id: str,
        include_password: bool = False,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve a specific entry by ID.
        
        Args:
            entry_id: UUID of the entry
            include_password: Whether to include password in response
            include_history: Whether to include entry history
            
        Returns:
            Dictionary containing entry information
            
        Raises:
            EntryNotFoundError: If entry not found
            ValidationError: If entry ID is invalid
        """
        try:
            entry_id = Validators.validate_uuid(entry_id)
            
            entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not entry:
                raise EntryNotFoundError(entry_id)
            
            return self._format_entry_response(entry, include_password, include_history)
            
        except Exception as e:
            if not isinstance(e, (EntryNotFoundError, ValidationError)):
                self.logger.error(f"Failed to get entry {entry_id}: {e}")
            raise
    
    def update_entry(
        self,
        entry_id: str,
        title: str = None,
        username: str = None,
        password: str = None,
        url: str = None,
        notes: str = None,
        tags: List[str] = None,
        custom_fields: Dict[str, str] = None,
        expires: Optional[datetime] = None,
        icon: int = None,
        generate_password: bool = False,
        password_options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Update an existing entry.
        
        Args:
            entry_id: UUID of the entry to update
            title: New title (optional)
            username: New username (optional)
            password: New password (optional)
            url: New URL (optional)
            notes: New notes (optional)
            tags: New tags (optional)
            custom_fields: New custom fields (optional)
            expires: New expiration date (optional)
            icon: New icon number (optional)
            generate_password: Whether to generate a new password
            password_options: Options for password generation
            
        Returns:
            Dictionary containing updated entry information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            EntryNotFoundError: If entry not found
            ValidationError: If validation fails
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("update_entry")
            
            entry_id = Validators.validate_uuid(entry_id)
            
            # Get existing entry
            entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not entry:
                raise EntryNotFoundError(entry_id)
            
            # Prepare update data
            update_data = {}
            
            if title is not None:
                update_data['title'] = Validators.validate_entry_title(title)
            
            if username is not None:
                update_data['username'] = Validators.validate_username(username)
            
            if generate_password:
                password_opts = password_options or {}
                update_data['password'] = self.password_generator.generate_password(**password_opts)
            elif password is not None:
                update_data['password'] = Validators.validate_password(password)
            
            if url is not None:
                update_data['url'] = Validators.validate_url(url) if url else ""
            
            if notes is not None:
                update_data['notes'] = Validators.validate_notes(notes)
            
            if tags is not None:
                update_data['tags'] = Validators.validate_tags(tags)
            
            if custom_fields is not None:
                update_data['custom_fields'] = Validators.validate_custom_fields(custom_fields)
            
            if expires is not None:
                update_data['expires'] = expires
            
            if icon is not None:
                update_data['icon'] = icon
            
            # Update entry in database
            updated_entry = self.keepass_handler.update_entry(entry, update_data)
            
            # Log the operation
            entry_title = update_data.get('title', entry.title)
            self.logger.info(f"Entry updated: {entry_title}")
            
            return self._format_entry_response(updated_entry)
            
        except Exception as e:
            self.logger.error(f"Failed to update entry {entry_id}: {e}")
            raise
    
    def delete_entry(self, entry_id: str, permanent: bool = False) -> Dict[str, Any]:
        """
        Delete an entry from the database.
        
        Args:
            entry_id: UUID of the entry to delete
            permanent: Whether to permanently delete (vs move to recycle bin)
            
        Returns:
            Dictionary with deletion information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            EntryNotFoundError: If entry not found
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("delete_entry")
            
            entry_id = Validators.validate_uuid(entry_id)
            
            # Get entry before deletion
            entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not entry:
                raise EntryNotFoundError(entry_id)
            
            entry_title = entry.title
            
            # Delete entry
            self.keepass_handler.delete_entry(entry, permanent)
            
            # Log the operation
            delete_type = "permanently deleted" if permanent else "moved to recycle bin"
            self.logger.info(f"Entry {delete_type}: {entry_title}")
            
            return {
                'entry_id': entry_id,
                'title': entry_title,
                'deleted_at': datetime.now().isoformat(),
                'permanent': permanent,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete entry {entry_id}: {e}")
            raise
    
    def move_entry(
        self,
        entry_id: str,
        target_group_id: str = None,
        target_group_name: str = None
    ) -> Dict[str, Any]:
        """
        Move an entry to a different group.
        
        Args:
            entry_id: UUID of the entry to move
            target_group_id: ID of the target group
            target_group_name: Name of the target group (alternative to ID)
            
        Returns:
            Dictionary with move operation information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            EntryNotFoundError: If entry not found
            GroupNotFoundError: If target group not found
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("move_entry")
            
            entry_id = Validators.validate_uuid(entry_id)
            
            # Get entry
            entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not entry:
                raise EntryNotFoundError(entry_id)
            
            # Find target group
            target_group = self._resolve_target_group(target_group_id, target_group_name)
            
            old_group_name = entry.group.name if entry.group else "Unknown"
            
            # Move entry
            self.keepass_handler.move_entry(entry, target_group)
            
            # Log the operation
            self.logger.info(f"Entry moved: {entry.title} from {old_group_name} to {target_group.name}")
            
            return {
                'entry_id': entry_id,
                'title': entry.title,
                'old_group': old_group_name,
                'new_group': target_group.name,
                'moved_at': datetime.now().isoformat(),
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to move entry {entry_id}: {e}")
            raise
    
    def duplicate_entry(
        self,
        entry_id: str,
        new_title: str = None,
        target_group_id: str = None,
        target_group_name: str = None
    ) -> Dict[str, Any]:
        """
        Create a duplicate of an existing entry.
        
        Args:
            entry_id: UUID of the entry to duplicate
            new_title: Title for the new entry (defaults to "Copy of <original>")
            target_group_id: ID of the target group for duplicate
            target_group_name: Name of the target group (alternative to ID)
            
        Returns:
            Dictionary containing the duplicated entry information
            
        Raises:
            ReadOnlyModeError: If in read-only mode
            EntryNotFoundError: If source entry not found
        """
        try:
            if self.config.is_read_only():
                raise ReadOnlyModeError("duplicate_entry")
            
            entry_id = Validators.validate_uuid(entry_id)
            
            # Get source entry
            source_entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not source_entry:
                raise EntryNotFoundError(entry_id)
            
            # Determine new title
            if not new_title:
                new_title = f"Copy of {source_entry.title}"
            else:
                new_title = Validators.validate_entry_title(new_title)
            
            # Find target group (default to source entry's group)
            if target_group_id or target_group_name:
                target_group = self._resolve_target_group(target_group_id, target_group_name)
            else:
                target_group = source_entry.group
            
            # Create duplicate entry
            duplicate_data = {
                'title': new_title,
                'username': source_entry.username,
                'password': source_entry.password,
                'url': source_entry.url,
                'notes': source_entry.notes,
                'tags': list(source_entry.tags) if hasattr(source_entry, 'tags') else [],
                'custom_fields': dict(source_entry.custom_properties) if hasattr(source_entry, 'custom_properties') else {},
                'icon': source_entry.icon if hasattr(source_entry, 'icon') else 0
            }
            
            duplicated_entry = self.keepass_handler.create_entry(target_group, duplicate_data)
            
            # Log the operation
            self.logger.info(f"Entry duplicated: {source_entry.title} -> {new_title}")
            
            return self._format_entry_response(duplicated_entry)
            
        except Exception as e:
            self.logger.error(f"Failed to duplicate entry {entry_id}: {e}")
            raise
    
    def list_entries(
        self,
        group_id: str = None,
        group_name: str = None,
        include_passwords: bool = False,
        include_subgroups: bool = True,
        sort_by: str = "title",
        limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        List entries in a group or entire database.
        
        Args:
            group_id: ID of specific group to list (optional)
            group_name: Name of specific group to list (optional)
            include_passwords: Whether to include passwords in response
            include_subgroups: Whether to include entries from subgroups
            sort_by: Sort method (title, username, date_created, date_modified)
            limit: Maximum number of entries to return
            
        Returns:
            List of entry dictionaries
        """
        try:
            # Get entries from specified group or entire database
            if group_id or group_name:
                target_group = self._resolve_target_group(group_id, group_name)
                entries = self.keepass_handler.get_entries_in_group(target_group, include_subgroups)
            else:
                entries = self.keepass_handler.get_all_entries()
            
            # Format entries
            formatted_entries = [
                self._format_entry_response(entry, include_passwords)
                for entry in entries
            ]
            
            # Sort entries
            formatted_entries = self._sort_entries(formatted_entries, sort_by)
            
            # Apply limit
            if limit and limit > 0:
                formatted_entries = formatted_entries[:limit]
            
            return formatted_entries
            
        except Exception as e:
            self.logger.error(f"Failed to list entries: {e}")
            raise
    
    def get_entry_history(self, entry_id: str) -> List[Dict[str, Any]]:
        """
        Get history of changes for an entry.
        
        Args:
            entry_id: UUID of the entry
            
        Returns:
            List of historical entry versions
            
        Raises:
            EntryNotFoundError: If entry not found
        """
        try:
            entry_id = Validators.validate_uuid(entry_id)
            
            entry = self.keepass_handler.get_entry_by_id(entry_id)
            if not entry:
                raise EntryNotFoundError(entry_id)
            
            history = self.keepass_handler.get_entry_history(entry)
            
            return [
                {
                    'version': i + 1,
                    'title': version.title,
                    'username': version.username,
                    'url': version.url,
                    'modified_at': version.mtime.isoformat() if version.mtime else None,
                    'notes_length': len(version.notes) if version.notes else 0
                }
                for i, version in enumerate(history)
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get entry history {entry_id}: {e}")
            raise
    
    def validate_entries(self) -> Dict[str, Any]:
        """
        Validate all entries and find issues.
        
        Returns:
            Dictionary with validation results
        """
        try:
            all_entries = self.keepass_handler.get_all_entries()
            
            issues = {
                'weak_passwords': [],
                'duplicate_titles': [],
                'missing_urls': [],
                'expired_entries': [],
                'empty_passwords': [],
                'total_entries': len(all_entries)
            }
            
            # Track titles for duplicate detection
            title_count = {}
            
            for entry in all_entries:
                entry_info = {
                    'id': str(entry.uuid),
                    'title': entry.title,
                    'group': entry.group.name if entry.group else 'Unknown'
                }
                
                # Check for weak passwords
                if entry.password:
                    strength = self.password_generator.check_password_strength(entry.password)
                    if strength['score'] < 60:  # Weak threshold
                        entry_info['weakness_reasons'] = strength['feedback']
                        issues['weak_passwords'].append(entry_info)
                else:
                    issues['empty_passwords'].append(entry_info)
                
                # Track title duplicates
                title_lower = entry.title.lower()
                if title_lower in title_count:
                    title_count[title_lower].append(entry_info)
                else:
                    title_count[title_lower] = [entry_info]
                
                # Check for missing URLs
                if not entry.url:
                    issues['missing_urls'].append(entry_info)
                
                # Check for expired entries
                if hasattr(entry, 'expires') and entry.expires and entry.expires < datetime.now():
                    entry_info['expired_at'] = entry.expires.isoformat()
                    issues['expired_entries'].append(entry_info)
            
            # Add duplicate titles
            for title, entries in title_count.items():
                if len(entries) > 1:
                    issues['duplicate_titles'].extend(entries)
            
            # Summary
            issues['summary'] = {
                'total_issues': (
                    len(issues['weak_passwords']) +
                    len(issues['duplicate_titles']) +
                    len(issues['missing_urls']) +
                    len(issues['expired_entries']) +
                    len(issues['empty_passwords'])
                ),
                'validation_date': datetime.now().isoformat()
            }
            
            self.logger.info(f"Entry validation completed: {issues['summary']['total_issues']} issues found")
            return issues
            
        except Exception as e:
            self.logger.error(f"Entry validation failed: {e}")
            raise
    
    def _check_duplicate_entry(self, title: str, username: str, url: str) -> bool:
        """Check if an entry with similar properties already exists."""
        try:
            all_entries = self.keepass_handler.get_all_entries()
            
            for entry in all_entries:
                if (entry.title.lower() == title.lower() and
                    entry.username.lower() == username.lower() and
                    entry.url.lower() == url.lower()):
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _resolve_target_group(self, group_id: str = None, group_name: str = None):
        """Resolve target group from ID or name."""
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
            # Default to root group
            return self.keepass_handler.get_root_group()
    
    def _format_entry_response(
        self,
        entry,
        include_password: bool = False,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """Format entry object for API response."""
        response = {
            'id': str(entry.uuid),
            'title': entry.title,
            'username': entry.username,
            'url': entry.url,
            'notes': entry.notes,
            'group': entry.group.name if entry.group else 'Unknown',
            'group_id': str(entry.group.uuid) if entry.group else None,
            'created': entry.ctime.isoformat() if entry.ctime else None,
            'modified': entry.mtime.isoformat() if entry.mtime else None,
            'accessed': entry.atime.isoformat() if entry.atime else None,
            'expires': entry.expires.isoformat() if hasattr(entry, 'expires') and entry.expires else None,
            'icon': entry.icon if hasattr(entry, 'icon') else 0,
            'tags': list(entry.tags) if hasattr(entry, 'tags') else [],
            'custom_fields': dict(entry.custom_properties) if hasattr(entry, 'custom_properties') else {}
        }
        
        if include_password:
            response['password'] = entry.password
        
        if include_history:
            try:
                response['history'] = self.get_entry_history(str(entry.uuid))
            except:
                response['history'] = []
        
        return response
    
    def _sort_entries(self, entries: List[Dict[str, Any]], sort_by: str) -> List[Dict[str, Any]]:
        """Sort entries by specified criteria."""
        if sort_by == "title":
            return sorted(entries, key=lambda x: x.get('title', '').lower())
        elif sort_by == "username":
            return sorted(entries, key=lambda x: x.get('username', '').lower())
        elif sort_by == "date_created":
            return sorted(entries, key=lambda x: x.get('created', ''), reverse=True)
        elif sort_by == "date_modified":
            return sorted(entries, key=lambda x: x.get('modified', ''), reverse=True)
        elif sort_by == "url":
            return sorted(entries, key=lambda x: x.get('url', '').lower())
        else:
            return entries
