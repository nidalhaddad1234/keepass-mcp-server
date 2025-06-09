"""
KeePass MCP Server - Main server implementation with all MCP tools.
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        EmbeddedResource,
        ImageContent,
        Resource,
        TextContent,
        Tool,
    )

    # Try to import newer MCP types if available
    try:
        from mcp.types import ExperimentalCapabilities, NotificationOptions
    except ImportError:
        NotificationOptions = None
        ExperimentalCapabilities = None

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    NotificationOptions = None
    ExperimentalCapabilities = None

from .backup_manager import BackupManager
from .config import KeePassMCPConfig, get_config
from .entry_manager import EntryManager
from .exceptions import (
    AuthenticationError,
    DatabaseError,
    DatabaseLockedError,
    EntryNotFoundError,
    GroupNotFoundError,
    KeePassMCPError,
    ReadOnlyModeError,
    SecurityError,
    SessionExpiredError,
    ValidationError,
)
from .group_manager import GroupManager
from .keepass_handler import KeePassHandler
from .password_generator import PasswordGenerator
from .search_engine import SearchEngine
from .security import SecurityManager
from .validators import Validators


class KeePassMCPServer:
    """Main KeePass MCP Server class implementing all functionality."""

    def __init__(self, config: KeePassMCPConfig):
        if not MCP_AVAILABLE:
            raise ImportError("MCP library is required but not installed")

        # Check MCP version for debugging
        try:
            import mcp

            self.logger = logging.getLogger(__name__)
            self.logger.info(
                f"Using MCP version: {getattr(mcp, '__version__', 'unknown')}"
            )

            # Also check what get_capabilities expects
            import inspect

            sig = inspect.signature(Server.get_capabilities)
            self.logger.info(f"get_capabilities signature: {sig}")

        except (ImportError, AttributeError) as e:
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Could not determine MCP version: {e}")

        self.config = config
        self.server = Server("keepass-mcp-server")

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

        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()

        self.logger.info("KeePass MCP Server initialized")

    def _register_tools(self):
        """Register all MCP tools."""

        # Authentication and session management
        @self.server.call_tool()
        async def authenticate(arguments: dict) -> List[TextContent]:
            """Authenticate user and unlock database."""
            try:
                password = arguments.get("password", "")
                key_file = arguments.get("key_file")

                if not password:
                    raise ValidationError("Password is required")

                # Unlock database
                unlock_info = self.keepass_handler.unlock_database(password, key_file)

                # Create session
                session_token = self.security_manager.authenticate_user(
                    "default", password
                )
                self.current_session = session_token

                response = {
                    "success": True,
                    "session_token": session_token,
                    "unlock_info": unlock_info,
                    "message": "Database unlocked successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def logout(arguments: dict) -> List[TextContent]:
            """Logout user and lock database."""
            try:
                if self.current_session:
                    self.security_manager.logout_user(self.current_session)
                    self.current_session = None

                lock_info = self.keepass_handler.lock_database()

                response = {
                    "success": True,
                    "lock_info": lock_info,
                    "message": "Database locked successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Search and retrieval tools
        @self.server.call_tool()
        async def search_credentials(arguments: dict) -> List[TextContent]:
            """Search for credentials by various criteria."""
            try:
                self._validate_session()

                query = arguments.get("query", "")
                search_fields = arguments.get(
                    "search_fields", ["title", "username", "url", "notes", "tags"]
                )
                case_sensitive = arguments.get("case_sensitive", False)
                exact_match = arguments.get("exact_match", False)
                tags = arguments.get("tags", [])
                group_filter = arguments.get("group_filter")
                limit = arguments.get("limit", 50)
                sort_by = arguments.get("sort_by", "relevance")

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
                    limit=limit,
                )

                response = {
                    "success": True,
                    "query": query,
                    "results_count": len(results),
                    "results": results,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def search_by_url(arguments: dict) -> List[TextContent]:
            """Search for credentials by URL."""
            try:
                self._validate_session()

                url = arguments.get("url", "")
                fuzzy_match = arguments.get("fuzzy_match", True)

                if not url:
                    raise ValidationError("URL is required")

                # Get all entries
                all_entries = self.entry_manager.list_entries(include_passwords=False)

                # Search by URL
                results = self.search_engine.search_by_url(
                    all_entries, url, fuzzy_match
                )

                response = {
                    "success": True,
                    "url": url,
                    "fuzzy_match": fuzzy_match,
                    "results_count": len(results),
                    "results": results,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def get_credential(arguments: dict) -> List[TextContent]:
            """Retrieve specific credential by entry ID."""
            try:
                self._validate_session()

                entry_id = arguments.get("entry_id", "")
                include_password = arguments.get("include_password", True)
                include_history = arguments.get("include_history", False)

                if not entry_id:
                    raise ValidationError("Entry ID is required")

                entry = self.entry_manager.get_entry(
                    entry_id,
                    include_password=include_password,
                    include_history=include_history,
                )

                response = {"success": True, "entry": entry}

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def list_entries(arguments: dict) -> List[TextContent]:
            """List entries in database or specific group."""
            try:
                self._validate_session()

                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")
                include_passwords = arguments.get("include_passwords", False)
                include_subgroups = arguments.get("include_subgroups", True)
                sort_by = arguments.get("sort_by", "title")
                limit = arguments.get("limit")

                entries = self.entry_manager.list_entries(
                    group_id=group_id,
                    group_name=group_name,
                    include_passwords=include_passwords,
                    include_subgroups=include_subgroups,
                    sort_by=sort_by,
                    limit=limit,
                )

                response = {
                    "success": True,
                    "group_id": group_id,
                    "group_name": group_name,
                    "entries_count": len(entries),
                    "entries": entries,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def list_groups(arguments: dict) -> List[TextContent]:
            """List groups in the database."""
            try:
                self._validate_session()

                parent_group_id = arguments.get("parent_group_id")
                parent_group_name = arguments.get("parent_group_name")
                include_root = arguments.get("include_root", True)
                include_statistics = arguments.get("include_statistics", False)
                recursive = arguments.get("recursive", False)
                sort_by = arguments.get("sort_by", "name")

                groups = self.group_manager.list_groups(
                    parent_group_id=parent_group_id,
                    parent_group_name=parent_group_name,
                    include_root=include_root,
                    include_statistics=include_statistics,
                    recursive=recursive,
                    sort_by=sort_by,
                )

                response = {
                    "success": True,
                    "parent_group_id": parent_group_id,
                    "parent_group_name": parent_group_name,
                    "groups_count": len(groups),
                    "groups": groups,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def get_group_info(arguments: dict) -> List[TextContent]:
            """Get detailed information about a group."""
            try:
                self._validate_session()

                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")
                include_entries = arguments.get("include_entries", False)
                include_subgroups = arguments.get("include_subgroups", True)
                include_statistics = arguments.get("include_statistics", True)

                if not group_id and not group_name:
                    raise ValidationError("Either group_id or group_name is required")

                group_info = self.group_manager.get_group(
                    group_id=group_id,
                    group_name=group_name,
                    include_entries=include_entries,
                    include_subgroups=include_subgroups,
                    include_statistics=include_statistics,
                )

                response = {"success": True, "group": group_info}

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Entry management tools
        @self.server.call_tool()
        async def create_entry(arguments: dict) -> List[TextContent]:
            """Create a new password entry."""
            try:
                self._validate_session()
                self._check_write_permission()

                title = arguments.get("title", "")
                username = arguments.get("username", "")
                password = arguments.get("password", "")
                url = arguments.get("url", "")
                notes = arguments.get("notes", "")
                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")
                tags = arguments.get("tags", [])
                custom_fields = arguments.get("custom_fields", {})
                generate_password = arguments.get("generate_password", False)
                password_options = arguments.get("password_options", {})

                if not title:
                    raise ValidationError("Title is required")

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
                    password_options=password_options,
                )

                response = {
                    "success": True,
                    "entry": entry,
                    "message": f'Entry "{title}" created successfully',
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def update_entry(arguments: dict) -> List[TextContent]:
            """Update an existing entry."""
            try:
                self._validate_session()
                self._check_write_permission()

                entry_id = arguments.get("entry_id", "")
                if not entry_id:
                    raise ValidationError("Entry ID is required")

                # Extract update fields
                update_fields = {}
                for field in [
                    "title",
                    "username",
                    "password",
                    "url",
                    "notes",
                    "tags",
                    "custom_fields",
                ]:
                    if field in arguments:
                        update_fields[field] = arguments[field]

                generate_password = arguments.get("generate_password", False)
                password_options = arguments.get("password_options", {})

                if generate_password:
                    update_fields["generate_password"] = True
                    update_fields["password_options"] = password_options

                entry = self.entry_manager.update_entry(entry_id, **update_fields)

                response = {
                    "success": True,
                    "entry": entry,
                    "message": f"Entry updated successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def delete_entry(arguments: dict) -> List[TextContent]:
            """Delete an entry."""
            try:
                self._validate_session()
                self._check_write_permission()

                entry_id = arguments.get("entry_id", "")
                permanent = arguments.get("permanent", False)

                if not entry_id:
                    raise ValidationError("Entry ID is required")

                result = self.entry_manager.delete_entry(entry_id, permanent)

                response = {
                    "success": True,
                    "result": result,
                    "message": f"Entry deleted successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def move_entry(arguments: dict) -> List[TextContent]:
            """Move an entry to a different group."""
            try:
                self._validate_session()
                self._check_write_permission()

                entry_id = arguments.get("entry_id", "")
                target_group_id = arguments.get("target_group_id")
                target_group_name = arguments.get("target_group_name")

                if not entry_id:
                    raise ValidationError("Entry ID is required")

                if not target_group_id and not target_group_name:
                    raise ValidationError("Target group ID or name is required")

                result = self.entry_manager.move_entry(
                    entry_id,
                    target_group_id=target_group_id,
                    target_group_name=target_group_name,
                )

                response = {
                    "success": True,
                    "result": result,
                    "message": "Entry moved successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def duplicate_entry(arguments: dict) -> List[TextContent]:
            """Create a duplicate of an existing entry."""
            try:
                self._validate_session()
                self._check_write_permission()

                entry_id = arguments.get("entry_id", "")
                new_title = arguments.get("new_title")
                target_group_id = arguments.get("target_group_id")
                target_group_name = arguments.get("target_group_name")

                if not entry_id:
                    raise ValidationError("Entry ID is required")

                entry = self.entry_manager.duplicate_entry(
                    entry_id,
                    new_title=new_title,
                    target_group_id=target_group_id,
                    target_group_name=target_group_name,
                )

                response = {
                    "success": True,
                    "entry": entry,
                    "message": "Entry duplicated successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Group management tools
        @self.server.call_tool()
        async def create_group(arguments: dict) -> List[TextContent]:
            """Create a new group."""
            try:
                self._validate_session()
                self._check_write_permission()

                name = arguments.get("name", "")
                parent_group_id = arguments.get("parent_group_id")
                parent_group_name = arguments.get("parent_group_name")
                notes = arguments.get("notes", "")
                icon = arguments.get("icon", 48)

                if not name:
                    raise ValidationError("Group name is required")

                group = self.group_manager.create_group(
                    name=name,
                    parent_group_id=parent_group_id,
                    parent_group_name=parent_group_name,
                    notes=notes,
                    icon=icon,
                )

                response = {
                    "success": True,
                    "group": group,
                    "message": f'Group "{name}" created successfully',
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def update_group(arguments: dict) -> List[TextContent]:
            """Update an existing group."""
            try:
                self._validate_session()
                self._check_write_permission()

                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")

                if not group_id and not group_name:
                    raise ValidationError("Either group_id or group_name is required")

                update_fields = {}
                for field in ["new_name", "notes", "icon"]:
                    if field in arguments:
                        update_fields[field] = arguments[field]

                group = self.group_manager.update_group(
                    group_id=group_id, group_name=group_name, **update_fields
                )

                response = {
                    "success": True,
                    "group": group,
                    "message": "Group updated successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def delete_group(arguments: dict) -> List[TextContent]:
            """Delete a group."""
            try:
                self._validate_session()
                self._check_write_permission()

                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")
                force = arguments.get("force", False)
                move_entries_to = arguments.get("move_entries_to")

                if not group_id and not group_name:
                    raise ValidationError("Either group_id or group_name is required")

                result = self.group_manager.delete_group(
                    group_id=group_id,
                    group_name=group_name,
                    force=force,
                    move_entries_to=move_entries_to,
                )

                response = {
                    "success": True,
                    "result": result,
                    "message": "Group deleted successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def move_group(arguments: dict) -> List[TextContent]:
            """Move a group to a different parent."""
            try:
                self._validate_session()
                self._check_write_permission()

                group_id = arguments.get("group_id")
                group_name = arguments.get("group_name")
                target_parent_id = arguments.get("target_parent_id")
                target_parent_name = arguments.get("target_parent_name")

                if not group_id and not group_name:
                    raise ValidationError("Either group_id or group_name is required")

                result = self.group_manager.move_group(
                    group_id=group_id,
                    group_name=group_name,
                    target_parent_id=target_parent_id,
                    target_parent_name=target_parent_name,
                )

                response = {
                    "success": True,
                    "result": result,
                    "message": "Group moved successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Password generation tool
        @self.server.call_tool()
        async def generate_password(arguments: dict) -> List[TextContent]:
            """Generate a secure password."""
            try:
                self._validate_session()

                length = arguments.get("length", 16)
                include_uppercase = arguments.get("include_uppercase", True)
                include_lowercase = arguments.get("include_lowercase", True)
                include_numbers = arguments.get("include_numbers", True)
                include_symbols = arguments.get("include_symbols", True)
                exclude_ambiguous = arguments.get("exclude_ambiguous", False)

                password = self.password_generator.generate_password(
                    length=length,
                    include_uppercase=include_uppercase,
                    include_lowercase=include_lowercase,
                    include_numbers=include_numbers,
                    include_symbols=include_symbols,
                    exclude_ambiguous=exclude_ambiguous,
                )

                # Check password strength
                strength = self.password_generator.check_password_strength(password)

                response = {
                    "success": True,
                    "password": password,
                    "strength_analysis": strength,
                    "options_used": {
                        "length": length,
                        "include_uppercase": include_uppercase,
                        "include_lowercase": include_lowercase,
                        "include_numbers": include_numbers,
                        "include_symbols": include_symbols,
                        "exclude_ambiguous": exclude_ambiguous,
                    },
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Database operations
        @self.server.call_tool()
        async def save_database(arguments: dict) -> List[TextContent]:
            """Manually save the database."""
            try:
                self._validate_session()
                self._check_write_permission()

                reason = arguments.get("reason", "manual")

                save_info = self.keepass_handler.save_database(reason)

                response = {
                    "success": True,
                    "save_info": save_info,
                    "message": "Database saved successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def create_backup(arguments: dict) -> List[TextContent]:
            """Create a database backup."""
            try:
                self._validate_session()

                reason = arguments.get("reason", "manual")
                compress = arguments.get("compress", True)
                verify = arguments.get("verify", True)

                backup_info = self.backup_manager.create_backup(
                    reason=reason, compress=compress, verify=verify
                )

                response = {
                    "success": True,
                    "backup_info": backup_info,
                    "message": "Backup created successfully",
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def get_database_info(arguments: dict) -> List[TextContent]:
            """Get database information and statistics."""
            try:
                self._validate_session()

                db_info = self.keepass_handler.get_database_info()

                response = {"success": True, "database_info": db_info}

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def health_check(arguments: dict) -> List[TextContent]:
            """Perform system health check."""
            try:
                health = self.keepass_handler.health_check()

                response = {"success": True, "health_check": health}

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        # Advanced search and analysis tools
        @self.server.call_tool()
        async def search_weak_passwords(arguments: dict) -> List[TextContent]:
            """Find entries with weak passwords."""
            try:
                self._validate_session()

                min_length = arguments.get("min_length", 8)
                require_complexity = arguments.get("require_complexity", True)

                all_entries = self.entry_manager.list_entries(include_passwords=True)
                weak_entries = self.search_engine.search_weak_passwords(
                    all_entries,
                    min_length=min_length,
                    require_complexity=require_complexity,
                )

                response = {
                    "success": True,
                    "criteria": {
                        "min_length": min_length,
                        "require_complexity": require_complexity,
                    },
                    "weak_entries_count": len(weak_entries),
                    "weak_entries": weak_entries,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def search_duplicates(arguments: dict) -> List[TextContent]:
            """Find duplicate entries."""
            try:
                self._validate_session()

                check_fields = arguments.get(
                    "check_fields", ["title", "username", "url"]
                )

                all_entries = self.entry_manager.list_entries(include_passwords=False)
                duplicate_groups = self.search_engine.search_duplicates(
                    all_entries, check_fields=check_fields
                )

                response = {
                    "success": True,
                    "check_fields": check_fields,
                    "duplicate_groups_count": len(duplicate_groups),
                    "duplicate_groups": duplicate_groups,
                }

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

        @self.server.call_tool()
        async def validate_entries(arguments: dict) -> List[TextContent]:
            """Validate all entries and find issues."""
            try:
                self._validate_session()

                validation_results = self.entry_manager.validate_entries()

                response = {"success": True, "validation_results": validation_results}

                return [TextContent(type="text", text=json.dumps(response, indent=2))]

            except Exception as e:
                return self._handle_error(e)

    def _register_resources(self):
        """Register MCP resources."""

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources."""
            return [
                Resource(
                    uri="keepass://database/info",
                    name="Database Information",
                    description="Current database information and statistics",
                    mimeType="application/json",
                ),
                Resource(
                    uri="keepass://groups/hierarchy",
                    name="Group Hierarchy",
                    description="Complete group hierarchy structure",
                    mimeType="application/json",
                ),
                Resource(
                    uri="keepass://backup/list",
                    name="Backup List",
                    description="List of available database backups",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a specific resource."""
            try:
                if uri == "keepass://database/info":
                    if self.current_session:
                        info = self.keepass_handler.get_database_info()
                        return json.dumps(info, indent=2)
                    else:
                        return json.dumps({"error": "Not authenticated"})

                elif uri == "keepass://groups/hierarchy":
                    if self.current_session:
                        hierarchy = self.group_manager.get_group_hierarchy()
                        return json.dumps(hierarchy, indent=2)
                    else:
                        return json.dumps({"error": "Not authenticated"})

                elif uri == "keepass://backup/list":
                    backups = self.backup_manager.list_backups()
                    return json.dumps(backups, indent=2, default=str)

                else:
                    return json.dumps({"error": "Resource not found"})

            except Exception as e:
                return json.dumps({"error": str(e)})

    def _validate_session(self):
        """Validate current session."""
        if not self.current_session:
            raise AuthenticationError("No active session. Please authenticate first.")

        try:
            if not self.security_manager.validate_session(self.current_session):
                self.current_session = None
                raise SessionExpiredError(
                    "Session has expired. Please authenticate again."
                )
        except SessionExpiredError:
            self.current_session = None
            raise

        # Update last activity
        self.last_activity = datetime.now()

    def _check_write_permission(self):
        """Check if write operations are allowed."""
        if self.config.is_read_only():
            raise ReadOnlyModeError("Server is in read-only mode")

    def _handle_error(self, error: Exception) -> List[TextContent]:
        """Handle and format errors for MCP response."""
        if isinstance(error, KeePassMCPError):
            error_response = {
                "success": False,
                "error": {
                    "type": error.__class__.__name__,
                    "code": error.error_code,
                    "message": error.message,
                },
            }
        else:
            self.logger.error(f"Unexpected error: {error}")
            error_response = {
                "success": False,
                "error": {
                    "type": "UnexpectedError",
                    "code": "INTERNAL_ERROR",
                    "message": str(error),
                },
            }

        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

    async def run(self):
        """Run the MCP server with improved error handling."""
        try:
            self.logger.info("Starting KeePass MCP Server...")

            # Setup signal handlers for graceful shutdown
            def signal_handler(signum, frame):
                self.logger.info("Received shutdown signal, cleaning up...")
                self.cleanup()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Run stdio server with better error handling
            try:
                async with stdio_server() as (read_stream, write_stream):
                    self.logger.info("MCP stdio server started, running server...")

                    # Initialize server options for MCP 1.9.3
                    # MCP 1.9.3 uses Pydantic models that expect specific dictionary structures
                    capabilities = None

                    try:
                        # Try to use the ServerCapabilities model with correct dictionary structure
                        from mcp.server.models import ServerCapabilities

                        # Create the capabilities with proper dictionary structures
                        capabilities = ServerCapabilities(
                            resources={"subscribe": False, "listChanged": False},
                            tools={},
                            prompts={"listChanged": False},
                            experimental={},  # This must be a dict, not an object!
                        )
                        self.logger.debug(
                            "✅ MCP 1.9.3 API works with ServerCapabilities model"
                        )

                    except Exception as e1:
                        self.logger.debug(f"ServerCapabilities model failed: {e1}")

                        # Fallback: Try the get_capabilities method directly with no arguments
                        try:
                            capabilities = self.server.get_capabilities()
                            self.logger.debug(
                                "✅ MCP 1.9.3 API works with no arguments"
                            )

                        except Exception as e2:
                            self.logger.debug(f"No arguments approach failed: {e2}")

                            # Final fallback: Create minimal capabilities dictionary
                            capabilities = {
                                "resources": {"subscribe": False, "listChanged": False},
                                "tools": {},
                                "prompts": {"listChanged": False},
                                "experimental": {},
                            }
                            self.logger.debug("Using fallback capabilities dictionary")

                    init_options = InitializationOptions(
                        server_name="keepass-mcp-server",
                        server_version="1.0.0",
                        capabilities=capabilities,
                    )

                    # Run the server
                    await self.server.run(read_stream, write_stream, init_options)

            except Exception as eg:
                # Handle exception groups (TaskGroup errors) - compatible with older Python
                self.logger.error("MCP server exception:")
                self.logger.error(f"Exception type: {type(eg).__name__}")
                self.logger.error(f"Exception message: {eg}")

                # Check if it's an ExceptionGroup (Python 3.11+)
                if hasattr(eg, "exceptions"):
                    self.logger.error("Sub-exceptions in group:")
                    for i, exc in enumerate(eg.exceptions):
                        self.logger.error(f"  {i+1}. {type(exc).__name__}: {exc}")
                        traceback.print_exception(type(exc), exc, exc.__traceback__)
                else:
                    self.logger.debug("Full traceback:", exc_info=True)

                raise

        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self.logger.debug("Full traceback:", exc_info=True)

            # Print more detailed error information
            self.logger.error(f"Error type: {type(e)}")
            self.logger.error(f"Error args: {e.args}")

            if hasattr(e, "exceptions"):
                self.logger.error("Sub-exceptions:")
                for i, sub_exc in enumerate(e.exceptions):
                    self.logger.error(f"  {i+1}. {type(sub_exc).__name__}: {sub_exc}")

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

            self.logger.info("KeePass MCP Server cleanup completed")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="KeePass MCP Server")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    args = parser.parse_args()

    try:
        # Load configuration
        config = get_config()

        if args.log_level:
            config.log_level = args.log_level.upper()

        # Create and run server
        server = KeePassMCPServer(config)
        asyncio.run(server.run())

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
