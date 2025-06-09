"""
Security and authentication management for KeePass MCP Server.
"""

import hashlib
import hmac
import logging
import secrets
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import keyring

    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from .exceptions import (
    AuthenticationError,
    SecurityError,
    SessionExpiredError,
)


class SecureSession:
    """Manages secure sessions with timeout and token management."""

    def __init__(self, session_timeout: int = 3600):
        self.session_timeout = session_timeout
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def create_session(self, user_id: str = "default") -> str:
        """Create a new secure session and return session token."""
        with self.lock:
            session_token = secrets.token_urlsafe(32)
            session_data = {
                "user_id": user_id,
                "created_at": time.time(),
                "last_access": time.time(),
                "access_count": 0,
            }
            self.sessions[session_token] = session_data

            self.logger.info(f"Created new session for user: {user_id}")
            return session_token

    def validate_session(self, session_token: str) -> bool:
        """Validate session token and update last access time."""
        with self.lock:
            if session_token not in self.sessions:
                return False

            session = self.sessions[session_token]
            current_time = time.time()

            # Check if session has expired
            if current_time - session["last_access"] > self.session_timeout:
                del self.sessions[session_token]
                raise SessionExpiredError()

            # Update access time and count
            session["last_access"] = current_time
            session["access_count"] += 1

            return True

    def destroy_session(self, session_token: str) -> None:
        """Destroy a session."""
        with self.lock:
            if session_token in self.sessions:
                user_id = self.sessions[session_token].get("user_id", "unknown")
                del self.sessions[session_token]
                self.logger.info(f"Destroyed session for user: {user_id}")

    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        with self.lock:
            current_time = time.time()
            expired_tokens = []

            for token, session in self.sessions.items():
                if current_time - session["last_access"] > self.session_timeout:
                    expired_tokens.append(token)

            for token in expired_tokens:
                user_id = self.sessions[token].get("user_id", "unknown")
                del self.sessions[token]
                self.logger.info(f"Cleaned up expired session for user: {user_id}")

    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        with self.lock:
            if session_token in self.sessions:
                session = self.sessions[session_token].copy()
                session["created_at"] = datetime.fromtimestamp(session["created_at"])
                session["last_access"] = datetime.fromtimestamp(session["last_access"])
                return session
            return None


class PasswordManager:
    """Secure password storage and retrieval using system keychain."""

    def __init__(self, service_name: str = "keepass-mcp-server"):
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)

        if not KEYRING_AVAILABLE:
            self.logger.warning(
                "Keyring library not available, passwords will not be cached"
            )

    def store_password(self, username: str, password: str) -> bool:
        """Store password in system keychain."""
        if not KEYRING_AVAILABLE:
            return False

        try:
            keyring.set_password(self.service_name, username, password)
            self.logger.info(f"Password stored in keychain for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to store password in keychain: {e}")
            return False

    def get_password(self, username: str) -> Optional[str]:
        """Retrieve password from system keychain."""
        if not KEYRING_AVAILABLE:
            return None

        try:
            password = keyring.get_password(self.service_name, username)
            if password:
                self.logger.info(
                    f"Password retrieved from keychain for user: {username}"
                )
            return password
        except Exception as e:
            self.logger.error(f"Failed to retrieve password from keychain: {e}")
            return None

    def delete_password(self, username: str) -> bool:
        """Delete password from system keychain."""
        if not KEYRING_AVAILABLE:
            return False

        try:
            keyring.delete_password(self.service_name, username)
            self.logger.info(f"Password deleted from keychain for user: {username}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete password from keychain: {e}")
            return False


class SecureMemory:
    """Secure memory management for sensitive data."""

    def __init__(self):
        self.sensitive_data: Dict[str, bytes] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

    def store(self, key: str, data: str) -> None:
        """Store sensitive data in memory."""
        with self.lock:
            self.sensitive_data[key] = data.encode("utf-8")

    def retrieve(self, key: str) -> Optional[str]:
        """Retrieve sensitive data from memory."""
        with self.lock:
            if key in self.sensitive_data:
                return self.sensitive_data[key].decode("utf-8")
            return None

    def delete(self, key: str) -> None:
        """Securely delete sensitive data from memory."""
        with self.lock:
            if key in self.sensitive_data:
                # Overwrite with random data
                data_length = len(self.sensitive_data[key])
                self.sensitive_data[key] = secrets.token_bytes(data_length)
                del self.sensitive_data[key]

    def clear_all(self) -> None:
        """Securely clear all sensitive data."""
        with self.lock:
            for key in list(self.sensitive_data.keys()):
                self.delete(key)

        self.logger.info("Cleared all sensitive data from memory")


class AuditLogger:
    """Audit logging for security operations."""

    def __init__(self):
        self.logger = logging.getLogger("keepass_mcp.audit")

    def log_authentication(self, user_id: str, success: bool, method: str):
        """Log authentication attempts."""
        status = "SUCCESS" if success else "FAILURE"
        self.logger.info(f"AUTH_{status} - User: {user_id} - Method: {method}")

    def log_database_access(self, operation: str, user_id: str, details: str = ""):
        """Log database access operations."""
        self.logger.info(
            f"DB_ACCESS - User: {user_id} - Operation: {operation} - Details: {details}"
        )

    def log_entry_operation(self, operation: str, user_id: str, entry_title: str):
        """Log entry operations (without sensitive data)."""
        self.logger.info(
            f"ENTRY_{operation.upper()} - User: {user_id} - Entry: {entry_title}"
        )

    def log_group_operation(self, operation: str, user_id: str, group_name: str):
        """Log group operations."""
        self.logger.info(
            f"GROUP_{operation.upper()} - User: {user_id} - Group: {group_name}"
        )

    def log_security_event(self, event: str, user_id: str, details: str = ""):
        """Log security events."""
        self.logger.warning(
            f"SECURITY_EVENT - User: {user_id} - Event: {event} - Details: {details}"
        )

    def log_session_event(self, event: str, user_id: str, session_token: str = ""):
        """Log session-related events."""
        # Only log first 8 characters of token for audit purposes
        token_snippet = session_token[:8] + "..." if session_token else ""
        self.logger.info(
            f"SESSION_{event.upper()} - User: {user_id} - Token: {token_snippet}"
        )


class SecurityManager:
    """Main security manager orchestrating all security components."""

    def __init__(self, config):
        self.config = config
        self.session_manager = SecureSession(config.session_timeout)
        self.password_manager = PasswordManager()
        self.secure_memory = SecureMemory()
        self.audit_logger = AuditLogger()
        self.logger = logging.getLogger(__name__)

        # Rate limiting for authentication attempts
        self.auth_attempts: Dict[str, list] = {}
        self.max_attempts = config.max_retries
        self.attempt_window = 300  # 5 minutes

        # Auto-lock functionality
        self.auto_lock_timeout = config.auto_lock_timeout
        self.last_activity = time.time()
        self.is_locked = False
        self.lock = threading.RLock()

    def authenticate_user(
        self, user_id: str, password: str, method: str = "password"
    ) -> str:
        """Authenticate user and create session."""
        # Check rate limiting
        if not self._check_rate_limit(user_id):
            self.audit_logger.log_authentication(user_id, False, "rate_limited")
            raise AuthenticationError(
                "Too many authentication attempts. Please try again later."
            )

        # Record authentication attempt
        self._record_auth_attempt(user_id)

        # For now, we'll implement a simple authentication
        # In a real implementation, this would verify against proper credentials
        if len(password) < 8:
            self.audit_logger.log_authentication(user_id, False, method)
            raise AuthenticationError("Authentication failed")

        # Store password in keychain if requested
        if self.config.use_keychain:
            self.password_manager.store_password(user_id, password)

        # Create session
        session_token = self.session_manager.create_session(user_id)

        # Reset rate limiting on successful auth
        if user_id in self.auth_attempts:
            del self.auth_attempts[user_id]

        self.audit_logger.log_authentication(user_id, True, method)
        self.audit_logger.log_session_event("created", user_id, session_token)

        return session_token

    def validate_session(self, session_token: str) -> bool:
        """Validate session and update activity."""
        if self.is_locked:
            raise SecurityError("System is locked")

        try:
            valid = self.session_manager.validate_session(session_token)
            if valid:
                self._update_activity()
            return valid
        except SessionExpiredError:
            self.audit_logger.log_session_event("expired", "unknown", session_token)
            raise

    def logout_user(self, session_token: str) -> None:
        """Logout user and destroy session."""
        session_info = self.session_manager.get_session_info(session_token)
        user_id = session_info.get("user_id", "unknown") if session_info else "unknown"

        self.session_manager.destroy_session(session_token)
        self.audit_logger.log_session_event("destroyed", user_id, session_token)

    def lock_system(self) -> None:
        """Lock the system and clear sensitive data."""
        with self.lock:
            self.is_locked = True
            self.secure_memory.clear_all()

            # Destroy all sessions
            for token in list(self.session_manager.sessions.keys()):
                self.session_manager.destroy_session(token)

            self.audit_logger.log_security_event("system_locked", "system")
            self.logger.info("System locked and sensitive data cleared")

    def unlock_system(self, user_id: str, password: str) -> str:
        """Unlock the system and create new session."""
        if not self.is_locked:
            raise SecurityError("System is not locked")

        # Authenticate user
        session_token = self.authenticate_user(user_id, password, "unlock")

        with self.lock:
            self.is_locked = False
            self._update_activity()

        self.audit_logger.log_security_event("system_unlocked", user_id)
        return session_token

    def check_auto_lock(self) -> None:
        """Check if system should be auto-locked."""
        if self.is_locked:
            return

        current_time = time.time()
        if current_time - self.last_activity > self.auto_lock_timeout:
            self.lock_system()

    def _update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user is rate limited."""
        current_time = time.time()

        if user_id not in self.auth_attempts:
            return True

        # Remove old attempts outside the window
        self.auth_attempts[user_id] = [
            attempt
            for attempt in self.auth_attempts[user_id]
            if current_time - attempt < self.attempt_window
        ]

        return len(self.auth_attempts[user_id]) < self.max_attempts

    def _record_auth_attempt(self, user_id: str) -> None:
        """Record authentication attempt for rate limiting."""
        current_time = time.time()

        if user_id not in self.auth_attempts:
            self.auth_attempts[user_id] = []

        self.auth_attempts[user_id].append(current_time)

    def cleanup(self) -> None:
        """Cleanup resources and clear sensitive data."""
        self.secure_memory.clear_all()
        self.session_manager.cleanup_expired_sessions()
        self.logger.info("Security manager cleanup completed")
