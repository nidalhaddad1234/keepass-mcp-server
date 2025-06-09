"""
Custom exceptions for KeePass MCP Server.
"""


class KeePassMCPError(Exception):
    """Base exception for all KeePass MCP Server errors."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"


class DatabaseError(KeePassMCPError):
    """Raised when there's an issue with the KeePass database."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "DATABASE_ERROR")


class AuthenticationError(KeePassMCPError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "AUTH_ERROR")


class ValidationError(KeePassMCPError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "VALIDATION_ERROR")


class SecurityError(KeePassMCPError):
    """Raised when there's a security-related issue."""
    
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "SECURITY_ERROR")


class DatabaseLockedError(DatabaseError):
    """Raised when attempting to access a locked database."""
    
    def __init__(self, message: str = "Database is locked"):
        super().__init__(message, "DATABASE_LOCKED")


class DatabaseCorruptedError(DatabaseError):
    """Raised when the database file is corrupted."""
    
    def __init__(self, message: str = "Database file is corrupted"):
        super().__init__(message, "DATABASE_CORRUPTED")


class EntryNotFoundError(KeePassMCPError):
    """Raised when a requested entry is not found."""
    
    def __init__(self, entry_id: str):
        super().__init__(f"Entry not found: {entry_id}", "ENTRY_NOT_FOUND")
        self.entry_id = entry_id


class GroupNotFoundError(KeePassMCPError):
    """Raised when a requested group is not found."""
    
    def __init__(self, group_id: str):
        super().__init__(f"Group not found: {group_id}", "GROUP_NOT_FOUND")
        self.group_id = group_id


class DuplicateEntryError(ValidationError):
    """Raised when attempting to create a duplicate entry."""
    
    def __init__(self, title: str):
        super().__init__(f"Entry already exists: {title}", "DUPLICATE_ENTRY")
        self.title = title


class ReadOnlyModeError(SecurityError):
    """Raised when attempting write operations in read-only mode."""
    
    def __init__(self, operation: str):
        super().__init__(
            f"Operation '{operation}' not allowed in read-only mode",
            "READ_ONLY_MODE"
        )
        self.operation = operation


class SessionExpiredError(SecurityError):
    """Raised when the session has expired."""
    
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message, "SESSION_EXPIRED")


class ConcurrentAccessError(DatabaseError):
    """Raised when there's a concurrent access conflict."""
    
    def __init__(self, message: str = "Concurrent access conflict"):
        super().__init__(message, "CONCURRENT_ACCESS")


class BackupError(KeePassMCPError):
    """Raised when backup operations fail."""
    
    def __init__(self, message: str):
        super().__init__(message, "BACKUP_ERROR")


class ImportError(ValidationError):
    """Raised when import operations fail."""
    
    def __init__(self, message: str, failed_entries: list = None):
        super().__init__(message, "IMPORT_ERROR")
        self.failed_entries = failed_entries or []


class ExportError(KeePassMCPError):
    """Raised when export operations fail."""
    
    def __init__(self, message: str):
        super().__init__(message, "EXPORT_ERROR")


class PasswordGenerationError(KeePassMCPError):
    """Raised when password generation fails."""
    
    def __init__(self, message: str):
        super().__init__(message, "PASSWORD_GENERATION_ERROR")


class OperationTimeoutError(KeePassMCPError):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout: int):
        super().__init__(
            f"Operation '{operation}' timed out after {timeout} seconds",
            "OPERATION_TIMEOUT"
        )
        self.operation = operation
        self.timeout = timeout
