"""
Configuration management for KeePass MCP Server.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class KeePassMCPConfig(BaseSettings):
    """Configuration settings for KeePass MCP Server."""

    # Database settings
    keepass_db_path: str = Field(..., env="KEEPASS_DB_PATH")
    keepass_key_file: Optional[str] = Field(None, env="KEEPASS_KEY_FILE")
    keepass_backup_dir: str = Field("./backups", env="KEEPASS_BACKUP_DIR")

    # Access and security settings
    access_mode: str = Field("readonly", env="KEEPASS_ACCESS_MODE")
    auto_save: bool = Field(True, env="KEEPASS_AUTO_SAVE")
    backup_count: int = Field(10, env="KEEPASS_BACKUP_COUNT")
    session_timeout: int = Field(3600, env="KEEPASS_SESSION_TIMEOUT")  # seconds
    auto_lock_timeout: int = Field(1800, env="KEEPASS_AUTO_LOCK")  # seconds

    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    audit_log: bool = Field(True, env="AUDIT_LOG")

    # Server settings
    server_host: str = Field("127.0.0.1", env="MCP_HOST")
    server_port: int = Field(8080, env="MCP_PORT")

    # Security settings
    use_keychain: bool = Field(True, env="USE_KEYCHAIN")
    master_password_prompt: bool = Field(True, env="MASTER_PASSWORD_PROMPT")
    max_retries: int = Field(3, env="MAX_RETRIES")

    # Performance settings
    cache_timeout: int = Field(300, env="CACHE_TIMEOUT")  # seconds
    max_concurrent_operations: int = Field(5, env="MAX_CONCURRENT_OPERATIONS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("keepass_db_path")
    @classmethod
    def validate_db_path(cls, v):
        """Validate that the database path is reasonable (don't check if file exists during init)."""
        path = Path(v)

        # Only validate extension, not existence (database might not be accessible during init)
        if not path.suffix.lower() == ".kdbx":
            raise ValueError(f"Invalid KeePass database file extension: {v}")

        return str(path.absolute())

    @field_validator("keepass_key_file")
    @classmethod
    def validate_key_file(cls, v):
        """Validate key file if provided (don't check existence during init)."""
        if v is None:
            return v
        path = Path(v)
        # Don't check if file exists during init - will be validated when actually used
        return str(path.absolute())

    @field_validator("access_mode")
    @classmethod
    def validate_access_mode(cls, v):
        """Validate access mode."""
        if v.lower() not in ["readonly", "readwrite"]:
            raise ValueError("Access mode must be 'readonly' or 'readwrite'")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @field_validator("backup_count")
    @classmethod
    def validate_backup_count(cls, v):
        """Validate backup count."""
        if v < 1:
            raise ValueError("Backup count must be at least 1")
        return v

    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        handlers = []

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)

        # File handler if specified
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(logging.Formatter(log_format))
            handlers.append(file_handler)

        logging.basicConfig(
            level=getattr(logging, self.log_level), handlers=handlers, format=log_format
        )

        # Create audit logger if enabled
        if self.audit_log:
            audit_logger = logging.getLogger("keepass_mcp.audit")
            audit_handler = logging.FileHandler("audit.log")
            audit_handler.setFormatter(
                logging.Formatter("%(asctime)s - AUDIT - %(message)s")
            )
            audit_logger.addHandler(audit_handler)
            audit_logger.setLevel(logging.INFO)

    def get_backup_dir(self) -> Path:
        """Get backup directory as Path object."""
        backup_path = Path(self.keepass_backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        return backup_path

    def is_read_only(self) -> bool:
        """Check if server is in read-only mode."""
        return self.access_mode == "readonly"


def get_config() -> KeePassMCPConfig:
    """Get application configuration."""
    return KeePassMCPConfig()
