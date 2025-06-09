"""
Core KeePass database handler with pykeepass integration.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from pykeepass import PyKeePass
    from pykeepass.exceptions import (
        CredentialsError,
        HeaderChecksumError,
        PayloadChecksumError,
        UnableToSendToRecycleBin,
    )

    PYKEEPASS_AVAILABLE = True
except ImportError:
    PYKEEPASS_AVAILABLE = False

from .backup_manager import BackupManager
from .exceptions import (
    AuthenticationError,
    BackupError,
    ConcurrentAccessError,
    DatabaseCorruptedError,
    DatabaseError,
    DatabaseLockedError,
    EntryNotFoundError,
    GroupNotFoundError,
)
from .security import SecurityManager


class KeePassHandler:
    """Core handler for KeePass database operations using pykeepass."""

    def __init__(self, config, security_manager: SecurityManager):
        if not PYKEEPASS_AVAILABLE:
            raise ImportError("pykeepass library is required but not installed")

        self.config = config
        self.security_manager = security_manager
        self.backup_manager = BackupManager(config)
        self.logger = logging.getLogger(__name__)

        # Database state
        self.database: Optional[PyKeePass] = None
        self.is_locked = True
        self.last_save_time = None
        self.lock = threading.RLock()

        # Auto-save settings
        self.auto_save_enabled = config.auto_save
        self.save_interval = 60  # seconds

        # Database path
        self.db_path = Path(config.keepass_db_path)
        self.key_file_path = (
            Path(config.keepass_key_file) if config.keepass_key_file else None
        )

    def unlock_database(self, password: str, key_file: str = None) -> Dict[str, Any]:
        """
        Unlock the KeePass database.

        Args:
            password: Master password for the database
            key_file: Path to key file (optional)

        Returns:
            Dictionary with unlock information

        Raises:
            AuthenticationError: If authentication fails
            DatabaseError: If database cannot be opened
            DatabaseCorruptedError: If database is corrupted
        """
        with self.lock:
            try:
                if not self.db_path.exists():
                    raise DatabaseError(f"Database file not found: {self.db_path}")

                # Use provided key file or configured one
                key_file_to_use = key_file or (
                    str(self.key_file_path) if self.key_file_path else None
                )

                # Attempt to open database
                self.database = PyKeePass(
                    filename=str(self.db_path),
                    password=password,
                    keyfile=key_file_to_use,
                )

                self.is_locked = False
                self.last_save_time = time.time()

                # Store credentials securely
                if self.config.use_keychain:
                    self.security_manager.password_manager.store_password(
                        "database", password
                    )

                unlock_info = {
                    "unlocked_at": datetime.now().isoformat(),
                    "database_path": str(self.db_path),
                    "has_key_file": key_file_to_use is not None,
                    "entry_count": len(list(self.database.entries)),
                    "group_count": len(list(self.database.groups)),
                    "database_version": (
                        str(self.database.version)
                        if hasattr(self.database, "version")
                        else "unknown"
                    ),
                }

                self.logger.info(f"Database unlocked: {self.db_path.name}")
                return unlock_info

            except CredentialsError as e:
                self.logger.warning(f"Authentication failed for database: {e}")
                raise AuthenticationError("Invalid password or key file")

            except (HeaderChecksumError, PayloadChecksumError) as e:
                self.logger.error(f"Database corruption detected: {e}")
                raise DatabaseCorruptedError(f"Database file is corrupted: {e}")

            except Exception as e:
                self.logger.error(f"Failed to unlock database: {e}")
                raise DatabaseError(f"Failed to unlock database: {e}")

    def lock_database(self) -> Dict[str, Any]:
        """
        Lock the database and clear memory.

        Returns:
            Dictionary with lock information
        """
        with self.lock:
            try:
                # Save database if changes were made
                if self.database and not self.is_locked:
                    self.save_database("lock_operation")

                # Clear database from memory
                self.database = None
                self.is_locked = True

                # Clear stored credentials
                if self.config.use_keychain:
                    self.security_manager.password_manager.delete_password("database")

                lock_info = {"locked_at": datetime.now().isoformat(), "success": True}

                self.logger.info("Database locked")
                return lock_info

            except Exception as e:
                self.logger.error(f"Failed to lock database: {e}")
                raise DatabaseError(f"Failed to lock database: {e}")

    def save_database(self, reason: str = "manual") -> Dict[str, Any]:
        """
        Save the database to disk.

        Args:
            reason: Reason for saving (manual, auto, pre_operation, etc.)

        Returns:
            Dictionary with save information

        Raises:
            DatabaseLockedError: If database is locked
            DatabaseError: If save fails
        """
        with self.lock:
            try:
                if self.is_locked or not self.database:
                    raise DatabaseLockedError("Database is locked")

                # Create backup before saving if this is a significant operation
                backup_info = None
                if reason in ["pre_operation", "manual"]:
                    try:
                        backup_info = self.backup_manager.create_backup(
                            reason=f"pre_save_{reason}", compress=True, verify=True
                        )
                    except Exception as e:
                        self.logger.warning(f"Backup creation failed before save: {e}")

                # Save database
                self.database.save()
                self.last_save_time = time.time()

                save_info = {
                    "saved_at": datetime.now().isoformat(),
                    "reason": reason,
                    "backup_created": backup_info is not None,
                    "backup_info": backup_info,
                    "success": True,
                }

                self.logger.info(f"Database saved (reason: {reason})")
                return save_info

            except Exception as e:
                self.logger.error(f"Failed to save database: {e}")
                raise DatabaseError(f"Failed to save database: {e}")

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get information about the database.

        Returns:
            Dictionary with database information

        Raises:
            DatabaseLockedError: If database is locked
        """
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                entries = list(self.database.entries)
                groups = list(self.database.groups)

                # Calculate some statistics
                entries_with_passwords = sum(1 for entry in entries if entry.password)
                entries_with_urls = sum(1 for entry in entries if entry.url)

                # Get root group info
                root_group = self.database.root_group

                info = {
                    "database_path": str(self.db_path),
                    "is_locked": self.is_locked,
                    "last_saved": (
                        datetime.fromtimestamp(self.last_save_time).isoformat()
                        if self.last_save_time
                        else None
                    ),
                    "version": (
                        str(self.database.version)
                        if hasattr(self.database, "version")
                        else "unknown"
                    ),
                    "encryption": (
                        "AES-256"
                        if hasattr(self.database, "encryption_algorithm")
                        else "unknown"
                    ),
                    "total_entries": len(entries),
                    "total_groups": len(groups),
                    "entries_with_passwords": entries_with_passwords,
                    "entries_with_urls": entries_with_urls,
                    "root_group_name": root_group.name if root_group else "Unknown",
                    "database_size_bytes": self.db_path.stat().st_size,
                    "has_recycle_bin": hasattr(self.database, "recyclebin_group")
                    and self.database.recyclebin_group is not None,
                    "auto_save_enabled": self.auto_save_enabled,
                }

                return info

            except Exception as e:
                self.logger.error(f"Failed to get database info: {e}")
                raise DatabaseError(f"Failed to get database info: {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database.

        Returns:
            Dictionary with health check results
        """
        health = {
            "timestamp": datetime.now().isoformat(),
            "database_exists": False,
            "database_accessible": False,
            "database_locked": self.is_locked,
            "backup_directory_exists": False,
            "recent_backup_available": False,
            "issues": [],
        }

        try:
            # Check if database file exists
            health["database_exists"] = self.db_path.exists()
            if not health["database_exists"]:
                health["issues"].append("Database file does not exist")

            # Check if database is accessible
            if not self.is_locked and self.database:
                try:
                    # Try to access basic info
                    _ = list(self.database.entries)
                    health["database_accessible"] = True
                except Exception as e:
                    health["issues"].append(f"Database not accessible: {e}")

            # Check backup directory
            backup_dir = self.backup_manager.backup_dir
            health["backup_directory_exists"] = backup_dir.exists()
            if not health["backup_directory_exists"]:
                health["issues"].append("Backup directory does not exist")
            else:
                # Check for recent backups
                try:
                    backups = self.backup_manager.list_backups(limit=1)
                    if backups:
                        latest_backup = backups[0]
                        backup_age = datetime.now() - latest_backup["created_at"]
                        health["recent_backup_available"] = backup_age.days < 7
                        health["latest_backup_age_days"] = backup_age.days
                    else:
                        health["issues"].append("No backups found")
                except Exception as e:
                    health["issues"].append(f"Could not check backups: {e}")

            # Overall health status
            health["status"] = "healthy" if not health["issues"] else "issues_detected"

        except Exception as e:
            health["issues"].append(f"Health check failed: {e}")
            health["status"] = "error"

        return health

    # Entry operations
    def create_entry(self, group, entry_data: Dict[str, Any]):
        """Create a new entry in the specified group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                entry = self.database.add_entry(
                    destination_group=group,
                    title=entry_data.get("title", ""),
                    username=entry_data.get("username", ""),
                    password=entry_data.get("password", ""),
                    url=entry_data.get("url", ""),
                    notes=entry_data.get("notes", ""),
                    icon=entry_data.get("icon", 0),
                    tags=entry_data.get("tags", []),
                )

                # Set custom fields
                custom_fields = entry_data.get("custom_fields", {})
                for key, value in custom_fields.items():
                    entry.set_custom_property(key, value)

                # Set expiration if provided
                if entry_data.get("expires"):
                    entry.expires = entry_data["expires"]

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_create")

                return entry

            except Exception as e:
                self.logger.error(f"Failed to create entry: {e}")
                raise DatabaseError(f"Failed to create entry: {e}")

    def get_entry_by_id(self, entry_id: str):
        """Get entry by UUID."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                for entry in self.database.entries:
                    if str(entry.uuid) == entry_id:
                        return entry
                return None

            except Exception as e:
                self.logger.error(f"Failed to get entry by ID: {e}")
                raise DatabaseError(f"Failed to get entry by ID: {e}")

    def update_entry(self, entry, update_data: Dict[str, Any]):
        """Update an existing entry."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                # Update basic fields
                if "title" in update_data:
                    entry.title = update_data["title"]
                if "username" in update_data:
                    entry.username = update_data["username"]
                if "password" in update_data:
                    entry.password = update_data["password"]
                if "url" in update_data:
                    entry.url = update_data["url"]
                if "notes" in update_data:
                    entry.notes = update_data["notes"]
                if "icon" in update_data:
                    entry.icon = update_data["icon"]

                # Update tags
                if "tags" in update_data:
                    # Clear existing tags and set new ones
                    entry.tags = update_data["tags"]

                # Update custom fields
                if "custom_fields" in update_data:
                    for key, value in update_data["custom_fields"].items():
                        entry.set_custom_property(key, value)

                # Update expiration
                if "expires" in update_data:
                    entry.expires = update_data["expires"]

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_update")

                return entry

            except Exception as e:
                self.logger.error(f"Failed to update entry: {e}")
                raise DatabaseError(f"Failed to update entry: {e}")

    def delete_entry(self, entry, permanent: bool = False):
        """Delete an entry."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                if permanent:
                    self.database.delete_entry(entry)
                else:
                    # Move to recycle bin
                    self.database.move_entry(entry, self.database.recyclebin_group)

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_delete")

            except Exception as e:
                self.logger.error(f"Failed to delete entry: {e}")
                raise DatabaseError(f"Failed to delete entry: {e}")

    def move_entry(self, entry, target_group):
        """Move entry to a different group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                self.database.move_entry(entry, target_group)

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_move")

            except Exception as e:
                self.logger.error(f"Failed to move entry: {e}")
                raise DatabaseError(f"Failed to move entry: {e}")

    def get_all_entries(self) -> List:
        """Get all entries in the database."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                return list(self.database.entries)

            except Exception as e:
                self.logger.error(f"Failed to get all entries: {e}")
                raise DatabaseError(f"Failed to get all entries: {e}")

    def get_entries_in_group(self, group, include_subgroups: bool = True) -> List:
        """Get entries in a specific group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                entries = []

                # Get entries directly in the group
                for entry in group.entries:
                    entries.append(entry)

                # Get entries from subgroups if requested
                if include_subgroups:
                    for subgroup in group.subgroups:
                        entries.extend(self.get_entries_in_group(subgroup, True))

                return entries

            except Exception as e:
                self.logger.error(f"Failed to get entries in group: {e}")
                raise DatabaseError(f"Failed to get entries in group: {e}")

    def get_entry_history(self, entry) -> List:
        """Get history of an entry."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                return entry.history if hasattr(entry, "history") else []

            except Exception as e:
                self.logger.error(f"Failed to get entry history: {e}")
                raise DatabaseError(f"Failed to get entry history: {e}")

    # Group operations
    def create_group(self, parent_group, group_data: Dict[str, Any]):
        """Create a new group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                group = self.database.add_group(
                    destination_group=parent_group,
                    group_name=group_data.get("name", ""),
                    icon=group_data.get("icon", 48),
                    notes=group_data.get("notes", ""),
                )

                # Set expiration if provided
                if group_data.get("expires"):
                    group.expires = group_data["expires"]

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_group_create")

                return group

            except Exception as e:
                self.logger.error(f"Failed to create group: {e}")
                raise DatabaseError(f"Failed to create group: {e}")

    def get_group_by_id(self, group_id: str):
        """Get group by UUID."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                for group in self.database.groups:
                    if str(group.uuid) == group_id:
                        return group
                return None

            except Exception as e:
                self.logger.error(f"Failed to get group by ID: {e}")
                raise DatabaseError(f"Failed to get group by ID: {e}")

    def get_group_by_name(self, group_name: str):
        """Get group by name (first match)."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                for group in self.database.groups:
                    if group.name == group_name:
                        return group
                return None

            except Exception as e:
                self.logger.error(f"Failed to get group by name: {e}")
                raise DatabaseError(f"Failed to get group by name: {e}")

    def update_group(self, group, update_data: Dict[str, Any]):
        """Update an existing group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                if "name" in update_data:
                    group.name = update_data["name"]
                if "notes" in update_data:
                    group.notes = update_data["notes"]
                if "icon" in update_data:
                    group.icon = update_data["icon"]
                if "expires" in update_data:
                    group.expires = update_data["expires"]

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_group_update")

                return group

            except Exception as e:
                self.logger.error(f"Failed to update group: {e}")
                raise DatabaseError(f"Failed to update group: {e}")

    def delete_group(self, group, force: bool = False):
        """Delete a group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                self.database.delete_group(group)

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_group_delete")

            except Exception as e:
                self.logger.error(f"Failed to delete group: {e}")
                raise DatabaseError(f"Failed to delete group: {e}")

    def move_group(self, group, target_parent):
        """Move group to a different parent."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                self.database.move_group(group, target_parent)

                if self.auto_save_enabled:
                    self.save_database("auto_save_after_group_move")

            except Exception as e:
                self.logger.error(f"Failed to move group: {e}")
                raise DatabaseError(f"Failed to move group: {e}")

    def get_root_group(self):
        """Get the root group of the database."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                return self.database.root_group

            except Exception as e:
                self.logger.error(f"Failed to get root group: {e}")
                raise DatabaseError(f"Failed to get root group: {e}")

    def get_all_groups(self) -> List:
        """Get all groups in the database."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                return list(self.database.groups)

            except Exception as e:
                self.logger.error(f"Failed to get all groups: {e}")
                raise DatabaseError(f"Failed to get all groups: {e}")

    def get_subgroups(self, group, recursive: bool = False) -> List:
        """Get subgroups of a group."""
        with self.lock:
            if self.is_locked or not self.database:
                raise DatabaseLockedError("Database is locked")

            try:
                subgroups = list(group.subgroups)

                if recursive:
                    all_subgroups = subgroups.copy()
                    for subgroup in subgroups:
                        all_subgroups.extend(self.get_subgroups(subgroup, True))
                    return all_subgroups

                return subgroups

            except Exception as e:
                self.logger.error(f"Failed to get subgroups: {e}")
                raise DatabaseError(f"Failed to get subgroups: {e}")

    def cleanup(self):
        """Cleanup resources and lock database."""
        try:
            if not self.is_locked:
                self.lock_database()
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
