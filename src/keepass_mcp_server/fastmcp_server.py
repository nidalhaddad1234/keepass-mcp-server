"""
KeePass MCP Server using FastMCP - Simplified and more reliable tool registration.
"""

import asyncio
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


class KeePassFastMCPServer:
    """KeePass MCP Server using FastMCP for better tool registration."""
    
    def __init__(self, config: KeePassMCPConfig):
        if not FASTMCP_AVAILABLE:
            raise ImportError("FastMCP library is required but not installed")
        
        self.config = config
        self.mcp = FastMCP("keepass-mcp-server")
        
        # Initialize components
        self.security_manager = SecurityManager(config)
        self.keepass_handler = KeePassHandler(config, self.security_manager)
        self.entry_manager = EntryManager(self.keepass_handler, config)
        self.group_manager = GroupManager(self.keepass_handler, config)
        self.search_engine = SearchEngine()
        self.password_generator = PasswordGenerator()
        self.backup_manager = BackupManager(config)
        
        # Session management
        self.current_session = None
        self.last_activity = datetime.now()
        
        # Setup logging
        config.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Register all tools
        self._register_tools()
        self._register_resources()
        
        self.logger.info("KeePass FastMCP Server initialized")
    
    def _register_tools(self):
        """Register all MCP tools using FastMCP decorators."""
        
        # Authentication tools
        @self.mcp.tool()
        async def authenticate(password: str, key_file: str = None) -> str:
            """Authenticate user and unlock KeePass database."""
            try:
                if not password:
                    raise ValidationError("Password is required")
                
                # Unlock database
                unlock_info = self.keepass_handler.unlock_database(password, key_file)
                
                # Create session
                session_token = self.security_manager.authenticate_user("default", password)
                self.current_session = session_token
                
                response = {
                    'success': True,
                    'session_token': session_token,
                    'unlock_info': unlock_info,
                    'message': 'Database unlocked successfully'
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def logout() -> str:
            """Logout user and lock database."""
            try:
                if self.current_session:
                    self.security_manager.logout_user(self.current_session)
                    self.current_session = None
                
                lock_info = self.keepass_handler.lock_database()
                
                response = {
                    'success': True,
                    'lock_info': lock_info,
                    'message': 'Database locked successfully'
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        # Search tools
        @self.mcp.tool()
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
                self._validate_session()
                
                if search_fields is None:
                    search_fields = ['title', 'username', 'url', 'notes', 'tags']
                if tags is None:
                    tags = []
                
                # Get all entries
                all_entries = self.entry_manager.list_entries(include_passwords=False)
                
                # Search entries
                results = self.search_engine.search_entries(
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
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def search_by_url(url: str, fuzzy_match: bool = True) -> str:
            """Search for credentials by URL."""
            try:
                self._validate_session()
                
                if not url:
                    raise ValidationError("URL is required")
                
                # Get all entries
                all_entries = self.entry_manager.list_entries(include_passwords=False)
                
                # Search by URL
                results = self.search_engine.search_by_url(all_entries, url, fuzzy_match)
                
                response = {
                    'success': True,
                    'url': url,
                    'fuzzy_match': fuzzy_match,
                    'results_count': len(results),
                    'results': results
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_credential(
            entry_id: str,
            include_password: bool = True,
            include_history: bool = False
        ) -> str:
            """Retrieve specific credential by entry ID."""
            try:
                self._validate_session()
                
                if not entry_id:
                    raise ValidationError("Entry ID is required")
                
                entry = self.entry_manager.get_entry(
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
                return self._handle_error(e)
        
        @self.mcp.tool()
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
                self._validate_session()
                
                entries = self.entry_manager.list_entries(
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
                return self._handle_error(e)
        
        # Entry management tools
        @self.mcp.tool()
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
                self._validate_session()
                self._check_write_permission()
                
                if not title:
                    raise ValidationError("Title is required")
                
                if tags is None:
                    tags = []
                if custom_fields is None:
                    custom_fields = {}
                if password_options is None:
                    password_options = {}
                
                entry = self.entry_manager.create_entry(
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
                return self._handle_error(e)
        
        @self.mcp.tool()
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
                self._validate_session()
                self._check_write_permission()
                
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
                
                entry = self.entry_manager.update_entry(entry_id, **update_fields)
                
                response = {
                    'success': True,
                    'entry': entry,
                    'message': 'Entry updated successfully'
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def delete_entry(entry_id: str, permanent: bool = False) -> str:
            """Delete an entry."""
            try:
                self._validate_session()
                self._check_write_permission()
                
                if not entry_id:
                    raise ValidationError("Entry ID is required")
                
                result = self.entry_manager.delete_entry(entry_id, permanent)
                
                response = {
                    'success': True,
                    'result': result,
                    'message': 'Entry deleted successfully'
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        # Group management tools
        @self.mcp.tool()
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
                self._validate_session()
                
                groups = self.group_manager.list_groups(
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
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def create_group(
            name: str,
            parent_group_id: str = None,
            parent_group_name: str = None,
            notes: str = "",
            icon: int = 48
        ) -> str:
            """Create a new group."""
            try:
                self._validate_session()
                self._check_write_permission()
                
                if not name:
                    raise ValidationError("Group name is required")
                
                group = self.group_manager.create_group(
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
                return self._handle_error(e)
        
        # Password generation
        @self.mcp.tool()
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
                self._validate_session()
                
                password = self.password_generator.generate_password(
                    length=length,
                    include_uppercase=include_uppercase,
                    include_lowercase=include_lowercase,
                    include_numbers=include_numbers,
                    include_symbols=include_symbols,
                    exclude_ambiguous=exclude_ambiguous
                )
                
                # Check password strength
                strength = self.password_generator.check_password_strength(password)
                
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
                return self._handle_error(e)
        
        # Database operations
        @self.mcp.tool()
        async def save_database(reason: str = "manual") -> str:
            """Manually save the database."""
            try:
                self._validate_session()
                self._check_write_permission()
                
                save_info = self.keepass_handler.save_database(reason)
                
                response = {
                    'success': True,
                    'save_info': save_info,
                    'message': 'Database saved successfully'
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def get_database_info() -> str:
            """Get database information and statistics."""
            try:
                self._validate_session()
                
                db_info = self.keepass_handler.get_database_info()
                
                response = {
                    'success': True,
                    'database_info': db_info
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        @self.mcp.tool()
        async def health_check() -> str:
            """Perform system health check."""
            try:
                health = self.keepass_handler.health_check()
                
                response = {
                    'success': True,
                    'health_check': health
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                return self._handle_error(e)
        
        # Security analysis tools
        @self.mcp.tool()
        async def search_weak_passwords(
            min_length: int = 8,
            require_complexity: bool = True
        ) -> str:
            """Find entries with weak passwords."""
            try:
                self._validate_session()
                
                all_entries = self.entry_manager.list_entries(include_passwords=True)
                weak_entries = self.search_engine.search_weak_passwords(
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
                return self._handle_error(e)
    
    def _register_resources(self):
        """Register MCP resources using FastMCP."""
        
        @self.mcp.resource("keepass://database/info")
        async def database_info():
            """Current database information and statistics"""
            try:
                if self.current_session:
                    info = self.keepass_handler.get_database_info()
                    return json.dumps(info, indent=2)
                else:
                    return json.dumps({"error": "Not authenticated"})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.resource("keepass://groups/hierarchy")
        async def group_hierarchy():
            """Complete group hierarchy structure"""
            try:
                if self.current_session:
                    hierarchy = self.group_manager.get_group_hierarchy()
                    return json.dumps(hierarchy, indent=2)
                else:
                    return json.dumps({"error": "Not authenticated"})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @self.mcp.resource("keepass://backup/list")
        async def backup_list():
            """List of available database backups"""
            try:
                backups = self.backup_manager.list_backups()
                return json.dumps(backups, indent=2, default=str)
            except Exception as e:
                return json.dumps({"error": str(e)})
    
    def _validate_session(self):
        """Validate current session."""
        if not self.current_session:
            raise AuthenticationError("No active session. Please authenticate first.")
        
        try:
            if not self.security_manager.validate_session(self.current_session):
                self.current_session = None
                raise SessionExpiredError("Session has expired. Please authenticate again.")
        except SessionExpiredError:
            self.current_session = None
            raise
        
        # Update last activity
        self.last_activity = datetime.now()
    
    def _check_write_permission(self):
        """Check if write operations are allowed."""
        if self.config.is_read_only():
            raise ReadOnlyModeError("Server is in read-only mode")
    
    def _handle_error(self, error: Exception) -> str:
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
            self.logger.error(f"Unexpected error: {error}")
            error_response = {
                'success': False,
                'error': {
                    'type': 'UnexpectedError',
                    'code': 'INTERNAL_ERROR',
                    'message': str(error)
                }
            }
        
        return json.dumps(error_response, indent=2)
    
    async def run(self):
        """Run the FastMCP server."""
        try:
            self.logger.info("Starting KeePass FastMCP Server...")
            await self.mcp.run()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if self.current_session:
                self.security_manager.logout_user(self.current_session)
            
            self.keepass_handler.cleanup()
            self.security_manager.cleanup()
            
            self.logger.info("KeePass FastMCP Server cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


def main():
    """Main entry point for FastMCP server."""
    parser = argparse.ArgumentParser(description="KeePass FastMCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = get_config()
        
        if args.log_level:
            config.log_level = args.log_level.upper()
        
        # Create and run server
        server = KeePassFastMCPServer(config)
        asyncio.run(server.run())
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
