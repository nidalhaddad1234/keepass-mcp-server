#!/usr/bin/env python3
"""
KeePass MCP Server using FastMCP - Fixed version.
"""

import json
import sys
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

try:
    from mcp.server.fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

from .config import get_config, KeePassMCPConfig
from .keepass_handler import KeePassHandler
from .entry_manager import EntryManager
from .group_manager import GroupManager
from .search_engine import SearchEngine
from .password_generator import PasswordGenerator
from .backup_manager import BackupManager
from .security import SecurityManager
from .exceptions import (
    KeePassMCPError,
    DatabaseError,
    AuthenticationError,
    ValidationError,
    SecurityError,
    ReadOnlyModeError,
    DatabaseLockedError,
    SessionExpiredError
)


# Global server instance
mcp = FastMCP("keepass-mcp-server")

# Global components (will be initialized in main)
config = None
security_manager = None
keepass_handler = None
entry_manager = None
group_manager = None
search_engine = None
password_generator = None
backup_manager = None

# Session management
current_session = None
last_activity = datetime.now()


def _validate_session():
    """Validate current session."""
    global current_session
    
    if not current_session:
        raise AuthenticationError("No active session. Please authenticate first.")
    
    try:
        if not security_manager.validate_session(current_session):
            current_session = None
            raise SessionExpiredError("Session has expired. Please authenticate again.")
    except SessionExpiredError:
        current_session = None
        raise
    
    # Update last activity
    global last_activity
    last_activity = datetime.now()


def _check_write_permission():
    """Check if write operations are allowed."""
    if config.is_read_only():
        raise ReadOnlyModeError("Server is in read-only mode")


def _handle_error(error: Exception) -> str:
    """Handle and format errors for MCP response."""
    if isinstance(error, KeePassMCPError):
        error_response = {
            'success': False,
            'error': {
                'type': error.__class__.__name__,
                'code': error.error_code,
                'message': error.message
            }
        }
    else:
        # Log to stderr only (not stdout)
        print(f"Unexpected error: {error}", file=sys.stderr)
        error_response = {
            'success': False,
            'error': {
                'type': 'UnexpectedError',
                'code': 'INTERNAL_ERROR',
                'message': str(error)
            }
        }
    
    return json.dumps(error_response, indent=2)


# Authentication tools
@mcp.tool()
async def authenticate(password: str, key_file: str = None) -> str:
    """Authenticate user and unlock KeePass database."""
    try:
        if not password:
            raise ValidationError("Password is required")
        
        # Unlock database
        unlock_info = keepass_handler.unlock_database(password, key_file)
        
        # Create session
        session_token = security_manager.authenticate_user("default", password)
        global current_session
        current_session = session_token
        
        response = {
            'success': True,
            'session_token': session_token,
            'unlock_info': unlock_info,
            'message': 'Database unlocked successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def logout() -> str:
    """Logout user and lock database."""
    try:
        global current_session
        if current_session:
            security_manager.logout_user(current_session)
            current_session = None
        
        lock_info = keepass_handler.lock_database()
        
        response = {
            'success': True,
            'lock_info': lock_info,
            'message': 'Database locked successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Search tools
@mcp.tool()
async def search_credentials(
    query: str = "",
    search_fields: List[str] = None,
    case_sensitive: bool = False,
    exact_match: bool = False,
    tags: List[str] = None,
    group_filter: str = None,
    limit: int = 50,
    sort_by: str = "relevance"
) -> str:
    """Search for credentials by various criteria."""
    try:
        _validate_session()
        
        if search_fields is None:
            search_fields = ['title', 'username', 'url', 'notes', 'tags']
        if tags is None:
            tags = []
        
        # Get all entries
        all_entries = entry_manager.list_entries(include_passwords=False)
        
        # Search entries
        results = search_engine.search_entries(
            entries=all_entries,
            query=query,
            search_fields=search_fields,
            case_sensitive=case_sensitive,
            exact_match=exact_match,
            tags=tags,
            group_filter=group_filter,
            sort_by=sort_by,
            limit=limit
        )
        
        response = {
            'success': True,
            'query': query,
            'results_count': len(results),
            'results': results
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def search_by_url(url: str, fuzzy_match: bool = True) -> str:
    """Search for credentials by URL."""
    try:
        _validate_session()
        
        if not url:
            raise ValidationError("URL is required")
        
        # Get all entries
        all_entries = entry_manager.list_entries(include_passwords=False)
        
        # Search by URL
        results = search_engine.search_by_url(all_entries, url, fuzzy_match)
        
        response = {
            'success': True,
            'url': url,
            'fuzzy_match': fuzzy_match,
            'results_count': len(results),
            'results': results
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def get_credential(
    entry_id: str,
    include_password: bool = True,
    include_history: bool = False
) -> str:
    """Retrieve specific credential by entry ID."""
    try:
        _validate_session()
        
        if not entry_id:
            raise ValidationError("Entry ID is required")
        
        entry = entry_manager.get_entry(
            entry_id,
            include_password=include_password,
            include_history=include_history
        )
        
        response = {
            'success': True,
            'entry': entry
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def list_entries(
    group_id: str = None,
    group_name: str = None,
    include_passwords: bool = False,
    include_subgroups: bool = True,
    sort_by: str = "title",
    limit: int = None
) -> str:
    """List entries in database or specific group."""
    try:
        _validate_session()
        
        entries = entry_manager.list_entries(
            group_id=group_id,
            group_name=group_name,
            include_passwords=include_passwords,
            include_subgroups=include_subgroups,
            sort_by=sort_by,
            limit=limit
        )
        
        response = {
            'success': True,
            'group_id': group_id,
            'group_name': group_name,
            'entries_count': len(entries),
            'entries': entries
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Entry management tools
@mcp.tool()
async def create_entry(
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
    password_options: Dict[str, Any] = None
) -> str:
    """Create a new password entry."""
    try:
        _validate_session()
        _check_write_permission()
        
        if not title:
            raise ValidationError("Title is required")
        
        if tags is None:
            tags = []
        if custom_fields is None:
            custom_fields = {}
        if password_options is None:
            password_options = {}
        
        entry = entry_manager.create_entry(
            title=title,
            username=username,
            password=password,
            url=url,
            notes=notes,
            group_id=group_id,
            group_name=group_name,
            tags=tags,
            custom_fields=custom_fields,
            generate_password=generate_password,
            password_options=password_options
        )
        
        response = {
            'success': True,
            'entry': entry,
            'message': f'Entry "{title}" created successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def update_entry(
    entry_id: str,
    title: str = None,
    username: str = None,
    password: str = None,
    url: str = None,
    notes: str = None,
    tags: List[str] = None,
    custom_fields: Dict[str, str] = None,
    generate_password: bool = False,
    password_options: Dict[str, Any] = None
) -> str:
    """Update an existing entry."""
    try:
        _validate_session()
        _check_write_permission()
        
        if not entry_id:
            raise ValidationError("Entry ID is required")
        
        # Build update fields
        update_fields = {}
        for field, value in [
            ('title', title), ('username', username), ('password', password),
            ('url', url), ('notes', notes), ('tags', tags), 
            ('custom_fields', custom_fields)
        ]:
            if value is not None:
                update_fields[field] = value
        
        if generate_password:
            update_fields['generate_password'] = True
            update_fields['password_options'] = password_options or {}
        
        entry = entry_manager.update_entry(entry_id, **update_fields)
        
        response = {
            'success': True,
            'entry': entry,
            'message': 'Entry updated successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def delete_entry(entry_id: str, permanent: bool = False) -> str:
    """Delete an entry."""
    try:
        _validate_session()
        _check_write_permission()
        
        if not entry_id:
            raise ValidationError("Entry ID is required")
        
        result = entry_manager.delete_entry(entry_id, permanent)
        
        response = {
            'success': True,
            'result': result,
            'message': 'Entry deleted successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Group management tools
@mcp.tool()
async def list_groups(
    parent_group_id: str = None,
    parent_group_name: str = None,
    include_root: bool = True,
    include_statistics: bool = False,
    recursive: bool = False,
    sort_by: str = "name"
) -> str:
    """List groups in the database."""
    try:
        _validate_session()
        
        groups = group_manager.list_groups(
            parent_group_id=parent_group_id,
            parent_group_name=parent_group_name,
            include_root=include_root,
            include_statistics=include_statistics,
            recursive=recursive,
            sort_by=sort_by
        )
        
        response = {
            'success': True,
            'parent_group_id': parent_group_id,
            'parent_group_name': parent_group_name,
            'groups_count': len(groups),
            'groups': groups
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def create_group(
    name: str,
    parent_group_id: str = None,
    parent_group_name: str = None,
    notes: str = "",
    icon: int = 48
) -> str:
    """Create a new group."""
    try:
        _validate_session()
        _check_write_permission()
        
        if not name:
            raise ValidationError("Group name is required")
        
        group = group_manager.create_group(
            name=name,
            parent_group_id=parent_group_id,
            parent_group_name=parent_group_name,
            notes=notes,
            icon=icon
        )
        
        response = {
            'success': True,
            'group': group,
            'message': f'Group "{name}" created successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Password generation
@mcp.tool()
async def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_numbers: bool = True,
    include_symbols: bool = True,
    exclude_ambiguous: bool = False
) -> str:
    """Generate a secure password."""
    try:
        _validate_session()
        
        password = password_generator.generate_password(
            length=length,
            include_uppercase=include_uppercase,
            include_lowercase=include_lowercase,
            include_numbers=include_numbers,
            include_symbols=include_symbols,
            exclude_ambiguous=exclude_ambiguous
        )
        
        # Check password strength
        strength = password_generator.check_password_strength(password)
        
        response = {
            'success': True,
            'password': password,
            'strength_analysis': strength,
            'options_used': {
                'length': length,
                'include_uppercase': include_uppercase,
                'include_lowercase': include_lowercase,
                'include_numbers': include_numbers,
                'include_symbols': include_symbols,
                'exclude_ambiguous': exclude_ambiguous
            }
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Database operations
@mcp.tool()
async def save_database(reason: str = "manual") -> str:
    """Manually save the database."""
    try:
        _validate_session()
        _check_write_permission()
        
        save_info = keepass_handler.save_database(reason)
        
        response = {
            'success': True,
            'save_info': save_info,
            'message': 'Database saved successfully'
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def get_database_info() -> str:
    """Get database information and statistics."""
    try:
        _validate_session()
        
        db_info = keepass_handler.get_database_info()
        
        response = {
            'success': True,
            'database_info': db_info
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


@mcp.tool()
async def health_check() -> str:
    """Perform system health check."""
    try:
        health = keepass_handler.health_check()
        
        response = {
            'success': True,
            'health_check': health
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Security analysis tools
@mcp.tool()
async def search_weak_passwords(
    min_length: int = 8,
    require_complexity: bool = True
) -> str:
    """Find entries with weak passwords."""
    try:
        _validate_session()
        
        all_entries = entry_manager.list_entries(include_passwords=True)
        weak_entries = search_engine.search_weak_passwords(
            all_entries,
            min_length=min_length,
            require_complexity=require_complexity
        )
        
        response = {
            'success': True,
            'criteria': {
                'min_length': min_length,
                'require_complexity': require_complexity
            },
            'weak_entries_count': len(weak_entries),
            'weak_entries': weak_entries
        }
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        return _handle_error(e)


# Resources
@mcp.resource("keepass://database/info")
async def database_info():
    """Current database information and statistics"""
    try:
        if current_session:
            info = keepass_handler.get_database_info()
            return json.dumps(info, indent=2)
        else:
            return json.dumps({"error": "Not authenticated"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("keepass://groups/hierarchy")
async def group_hierarchy():
    """Complete group hierarchy structure"""
    try:
        if current_session:
            hierarchy = group_manager.get_group_hierarchy()
            return json.dumps(hierarchy, indent=2)
        else:
            return json.dumps({"error": "Not authenticated"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("keepass://backup/list")
async def backup_list():
    """List of available database backups"""
    try:
        backups = backup_manager.list_backups()
        return json.dumps(backups, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


def cleanup():
    """Cleanup resources."""
    try:
        global current_session
        if current_session:
            security_manager.logout_user(current_session)
        
        if keepass_handler:
            keepass_handler.cleanup()
        if security_manager:
            security_manager.cleanup()
        
        # Log to stderr only
        print("Cleared all sensitive data from memory", file=sys.stderr)
        print("Security manager cleanup completed", file=sys.stderr)
        print("KeePass FastMCP Server cleanup completed", file=sys.stderr)
        
    except Exception as e:
        print(f"Cleanup error: {e}", file=sys.stderr)


def main():
    """Main entry point for FastMCP server."""
    global config, security_manager, keepass_handler, entry_manager
    global group_manager, search_engine, password_generator, backup_manager
    
    if not FASTMCP_AVAILABLE:
        print("Fatal error: FastMCP library is required but not installed", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Load configuration
        config = get_config()
        
        # Initialize components
        security_manager = SecurityManager(config)
        keepass_handler = KeePassHandler(config, security_manager)
        entry_manager = EntryManager(keepass_handler, config)
        group_manager = GroupManager(keepass_handler, config)
        search_engine = SearchEngine()
        password_generator = PasswordGenerator()
        backup_manager = BackupManager(config)
        
        # Setup logging to stderr only
        config.setup_logging()
        
        # Log initialization to stderr
        print("KeePass FastMCP Server initialized", file=sys.stderr)
        print("Starting KeePass FastMCP Server...", file=sys.stderr)
        
        # Run the FastMCP server - this will handle the event loop
        mcp.run()
        
    except KeyboardInterrupt:
        print("Shutdown requested by user", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
