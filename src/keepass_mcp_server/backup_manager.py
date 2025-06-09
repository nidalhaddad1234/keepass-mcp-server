"""
Backup management for KeePass databases.
"""

import gzip
import hashlib
import json
import logging
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import KeePassMCPConfig
from .exceptions import BackupError, ValidationError


class BackupManager:
    """Manages database backups with automatic cleanup and verification."""

    def __init__(self, config: KeePassMCPConfig):
        self.config = config
        self.backup_dir = config.get_backup_dir()
        self.db_path = Path(config.keepass_db_path)
        self.max_backups = config.backup_count
        self.logger = logging.getLogger(__name__)

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self, reason: str = "manual", compress: bool = True, verify: bool = True
    ) -> Dict[str, Any]:
        """
        Create a backup of the KeePass database.

        Args:
            reason: Reason for backup (manual, pre_operation, scheduled)
            compress: Whether to compress the backup
            verify: Whether to verify backup integrity

        Returns:
            Dictionary with backup information

        Raises:
            BackupError: If backup creation fails
        """
        try:
            if not self.db_path.exists():
                raise BackupError(f"Database file not found: {self.db_path}")

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_name = self.db_path.stem

            if compress:
                backup_filename = f"{db_name}_{timestamp}_{reason}.kdbx.gz"
            else:
                backup_filename = f"{db_name}_{timestamp}_{reason}.kdbx"

            backup_path = self.backup_dir / backup_filename

            # Calculate original file checksum
            original_checksum = self._calculate_checksum(self.db_path)

            # Create backup
            if compress:
                self._create_compressed_backup(self.db_path, backup_path)
            else:
                shutil.copy2(self.db_path, backup_path)

            # Verify backup if requested
            if verify:
                if not self._verify_backup(backup_path, original_checksum, compress):
                    backup_path.unlink()  # Remove failed backup
                    raise BackupError("Backup verification failed")

            # Create backup metadata
            metadata = {
                "filename": backup_filename,
                "path": str(backup_path),
                "created_at": datetime.now().isoformat(),
                "reason": reason,
                "original_size": self.db_path.stat().st_size,
                "backup_size": backup_path.stat().st_size,
                "compressed": compress,
                "checksum": original_checksum,
                "verified": verify,
            }

            # Save metadata
            self._save_backup_metadata(backup_path, metadata)

            # Cleanup old backups
            self._cleanup_old_backups()

            self.logger.info(f"Backup created: {backup_filename} (reason: {reason})")
            return metadata

        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise BackupError(f"Failed to create backup: {e}")

    def restore_backup(
        self,
        backup_filename: str,
        verify_before_restore: bool = True,
        create_pre_restore_backup: bool = True,
    ) -> Dict[str, Any]:
        """
        Restore database from a backup.

        Args:
            backup_filename: Name of backup file to restore
            verify_before_restore: Verify backup integrity before restoring
            create_pre_restore_backup: Create backup of current database before restore

        Returns:
            Dictionary with restore information

        Raises:
            BackupError: If restore fails
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_filename}")

            # Load backup metadata
            metadata = self._load_backup_metadata(backup_path)

            # Verify backup before restore
            if verify_before_restore:
                expected_checksum = metadata.get("checksum") if metadata else None
                is_compressed = backup_filename.endswith(".gz")

                if not self._verify_backup(
                    backup_path, expected_checksum, is_compressed
                ):
                    raise BackupError("Backup verification failed before restore")

            # Create pre-restore backup of current database
            pre_restore_backup = None
            if create_pre_restore_backup and self.db_path.exists():
                pre_restore_backup = self.create_backup(
                    reason="pre_restore", compress=True, verify=True
                )

            # Create backup of original database path
            original_backup_path = None
            if self.db_path.exists():
                original_backup_path = self.db_path.with_suffix(".kdbx.original")
                shutil.copy2(self.db_path, original_backup_path)

            try:
                # Restore database
                if backup_filename.endswith(".gz"):
                    self._restore_compressed_backup(backup_path, self.db_path)
                else:
                    shutil.copy2(backup_path, self.db_path)

                # Verify restored database
                if verify_before_restore and metadata:
                    restored_checksum = self._calculate_checksum(self.db_path)
                    expected_checksum = metadata.get("checksum")

                    if expected_checksum and restored_checksum != expected_checksum:
                        # Restore failed, rollback
                        if original_backup_path and original_backup_path.exists():
                            shutil.copy2(original_backup_path, self.db_path)
                        raise BackupError("Restored database checksum mismatch")

                # Cleanup original backup
                if original_backup_path and original_backup_path.exists():
                    original_backup_path.unlink()

                restore_info = {
                    "backup_filename": backup_filename,
                    "restored_at": datetime.now().isoformat(),
                    "pre_restore_backup": pre_restore_backup,
                    "verified": verify_before_restore,
                    "original_metadata": metadata,
                }

                self.logger.info(f"Database restored from backup: {backup_filename}")
                return restore_info

            except Exception as restore_error:
                # Rollback on failure
                if original_backup_path and original_backup_path.exists():
                    shutil.copy2(original_backup_path, self.db_path)
                    original_backup_path.unlink()
                raise BackupError(f"Restore failed: {restore_error}")

        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            raise BackupError(f"Failed to restore backup: {e}")

    def list_backups(
        self, include_metadata: bool = True, sort_by: str = "date", limit: int = None
    ) -> List[Dict[str, Any]]:
        """
        List available backups.

        Args:
            include_metadata: Include backup metadata
            sort_by: Sort by 'date', 'size', or 'name'
            limit: Maximum number of backups to return

        Returns:
            List of backup information dictionaries
        """
        try:
            backups = []

            # Find all backup files
            for backup_file in self.backup_dir.glob("*.kdbx*"):
                if backup_file.suffix in [
                    ".kdbx",
                    ".gz",
                ] and not backup_file.name.endswith(".meta"):
                    backup_info = {
                        "filename": backup_file.name,
                        "path": str(backup_file),
                        "size": backup_file.stat().st_size,
                        "created_at": datetime.fromtimestamp(
                            backup_file.stat().st_mtime
                        ),
                        "compressed": backup_file.name.endswith(".gz"),
                    }

                    # Load metadata if requested
                    if include_metadata:
                        metadata = self._load_backup_metadata(backup_file)
                        if metadata:
                            backup_info.update(metadata)

                    backups.append(backup_info)

            # Sort backups
            if sort_by == "date":
                backups.sort(key=lambda x: x["created_at"], reverse=True)
            elif sort_by == "size":
                backups.sort(key=lambda x: x["size"], reverse=True)
            elif sort_by == "name":
                backups.sort(key=lambda x: x["filename"])

            # Apply limit
            if limit and limit > 0:
                backups = backups[:limit]

            return backups

        except Exception as e:
            self.logger.error(f"Failed to list backups: {e}")
            raise BackupError(f"Failed to list backups: {e}")

    def delete_backup(self, backup_filename: str) -> bool:
        """
        Delete a specific backup file.

        Args:
            backup_filename: Name of backup file to delete

        Returns:
            True if deletion successful

        Raises:
            BackupError: If deletion fails
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_filename}")

            # Delete backup file
            backup_path.unlink()

            # Delete metadata file if exists
            metadata_path = backup_path.with_suffix(backup_path.suffix + ".meta")
            if metadata_path.exists():
                metadata_path.unlink()

            self.logger.info(f"Backup deleted: {backup_filename}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to delete backup: {e}")
            raise BackupError(f"Failed to delete backup: {e}")

    def verify_backup(self, backup_filename: str) -> Dict[str, Any]:
        """
        Verify backup integrity.

        Args:
            backup_filename: Name of backup file to verify

        Returns:
            Verification result dictionary

        Raises:
            BackupError: If verification fails
        """
        try:
            backup_path = self.backup_dir / backup_filename

            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_filename}")

            # Load metadata
            metadata = self._load_backup_metadata(backup_path)
            expected_checksum = metadata.get("checksum") if metadata else None
            is_compressed = backup_filename.endswith(".gz")

            # Verify backup
            is_valid = self._verify_backup(
                backup_path, expected_checksum, is_compressed
            )

            verification_result = {
                "filename": backup_filename,
                "verified_at": datetime.now().isoformat(),
                "is_valid": is_valid,
                "has_metadata": metadata is not None,
                "checksum_match": expected_checksum is not None if is_valid else False,
                "file_exists": True,
                "file_size": backup_path.stat().st_size,
            }

            if metadata:
                verification_result.update(
                    {
                        "original_size": metadata.get("original_size"),
                        "backup_created": metadata.get("created_at"),
                        "backup_reason": metadata.get("reason"),
                    }
                )

            return verification_result

        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            raise BackupError(f"Failed to verify backup: {e}")

    def cleanup_old_backups(self) -> List[str]:
        """
        Clean up old backups based on retention policy.

        Returns:
            List of deleted backup filenames
        """
        try:
            backups = self.list_backups(include_metadata=False, sort_by="date")
            deleted_backups = []

            if len(backups) > self.max_backups:
                # Delete oldest backups
                backups_to_delete = backups[self.max_backups :]

                for backup in backups_to_delete:
                    try:
                        self.delete_backup(backup["filename"])
                        deleted_backups.append(backup["filename"])
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to delete old backup {backup['filename']}: {e}"
                        )

            if deleted_backups:
                self.logger.info(f"Cleaned up {len(deleted_backups)} old backups")

            return deleted_backups

        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            return []

    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics and information.

        Returns:
            Dictionary with backup statistics
        """
        try:
            backups = self.list_backups(include_metadata=True)

            if not backups:
                return {
                    "total_backups": 0,
                    "total_size": 0,
                    "oldest_backup": None,
                    "newest_backup": None,
                    "average_size": 0,
                    "compressed_count": 0,
                    "backup_reasons": {},
                }

            total_size = sum(backup["size"] for backup in backups)
            compressed_count = sum(
                1 for backup in backups if backup.get("compressed", False)
            )

            # Count backup reasons
            backup_reasons = {}
            for backup in backups:
                reason = backup.get("reason", "unknown")
                backup_reasons[reason] = backup_reasons.get(reason, 0) + 1

            statistics = {
                "total_backups": len(backups),
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "oldest_backup": (
                    backups[-1]["created_at"].isoformat() if backups else None
                ),
                "newest_backup": (
                    backups[0]["created_at"].isoformat() if backups else None
                ),
                "average_size": round(total_size / len(backups), 2),
                "average_size_mb": round(
                    (total_size / len(backups)) / (1024 * 1024), 2
                ),
                "compressed_count": compressed_count,
                "uncompressed_count": len(backups) - compressed_count,
                "backup_reasons": backup_reasons,
                "backup_directory": str(self.backup_dir),
                "max_backups_configured": self.max_backups,
            }

            return statistics

        except Exception as e:
            self.logger.error(f"Failed to get backup statistics: {e}")
            raise BackupError(f"Failed to get backup statistics: {e}")

    def _create_compressed_backup(self, source_path: Path, backup_path: Path) -> None:
        """Create compressed backup using gzip."""
        with open(source_path, "rb") as source_file:
            with gzip.open(backup_path, "wb") as backup_file:
                shutil.copyfileobj(source_file, backup_file)

    def _restore_compressed_backup(self, backup_path: Path, restore_path: Path) -> None:
        """Restore from compressed backup."""
        with gzip.open(backup_path, "rb") as backup_file:
            with open(restore_path, "wb") as restore_file:
                shutil.copyfileobj(backup_file, restore_file)

    def _verify_backup(
        self,
        backup_path: Path,
        expected_checksum: str = None,
        is_compressed: bool = False,
    ) -> bool:
        """Verify backup integrity."""
        try:
            if is_compressed:
                # For compressed backups, verify by decompressing and checking
                with gzip.open(backup_path, "rb") as f:
                    data = f.read()
                    if expected_checksum:
                        calculated_checksum = hashlib.sha256(data).hexdigest()
                        return calculated_checksum == expected_checksum
                    return True
            else:
                # For uncompressed backups, calculate checksum directly
                if expected_checksum:
                    calculated_checksum = self._calculate_checksum(backup_path)
                    return calculated_checksum == expected_checksum
                return backup_path.exists() and backup_path.stat().st_size > 0

        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _save_backup_metadata(
        self, backup_path: Path, metadata: Dict[str, Any]
    ) -> None:
        """Save backup metadata to a separate file."""
        metadata_path = backup_path.with_suffix(backup_path.suffix + ".meta")
        try:
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to save backup metadata: {e}")

    def _load_backup_metadata(self, backup_path: Path) -> Optional[Dict[str, Any]]:
        """Load backup metadata from metadata file."""
        metadata_path = backup_path.with_suffix(backup_path.suffix + ".meta")
        try:
            if metadata_path.exists():
                with open(metadata_path, "r") as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load backup metadata: {e}")
        return None

    def _cleanup_old_backups(self) -> None:
        """Internal method to cleanup old backups."""
        self.cleanup_old_backups()
