"""
Test security features for KeePass MCP Server.
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime

from keepass_mcp_server.security import (
    SecureSession,
    PasswordManager,
    SecureMemory,
    AuditLogger,
    SecurityManager
)
from keepass_mcp_server.exceptions import (
    AuthenticationError,
    SecurityError,
    SessionExpiredError
)


class TestSecureSession:
    """Test cases for SecureSession."""
    
    @pytest.fixture
    def secure_session(self):
        """Create SecureSession instance for testing."""
        return SecureSession(session_timeout=3600)  # 1 hour timeout
    
    def test_create_session(self, secure_session):
        """Test session creation."""
        session_token = secure_session.create_session("test_user")
        
        assert isinstance(session_token, str)
        assert len(session_token) > 32  # URL-safe token
        assert session_token in secure_session.sessions
        
        session_data = secure_session.sessions[session_token]
        assert session_data['user_id'] == "test_user"
        assert session_data['access_count'] == 0
    
    def test_validate_session_success(self, secure_session):
        """Test successful session validation."""
        session_token = secure_session.create_session("test_user")
        
        # Validate immediately
        is_valid = secure_session.validate_session(session_token)
        
        assert is_valid is True
        
        # Check that access count increased
        session_data = secure_session.sessions[session_token]
        assert session_data['access_count'] == 1
    
    def test_validate_session_invalid_token(self, secure_session):
        """Test validation with invalid token."""
        is_valid = secure_session.validate_session("invalid_token")
        
        assert is_valid is False
    
    def test_validate_session_expired(self, secure_session):
        """Test validation of expired session."""
        # Create session with very short timeout
        short_session = SecureSession(session_timeout=1)  # 1 second
        session_token = short_session.create_session("test_user")
        
        # Wait for session to expire
        time.sleep(2)
        
        with pytest.raises(SessionExpiredError):
            short_session.validate_session(session_token)
        
        # Session should be removed after expiration
        assert session_token not in short_session.sessions
    
    def test_destroy_session(self, secure_session):
        """Test session destruction."""
        session_token = secure_session.create_session("test_user")
        
        # Verify session exists
        assert session_token in secure_session.sessions
        
        # Destroy session
        secure_session.destroy_session(session_token)
        
        # Verify session is removed
        assert session_token not in secure_session.sessions
    
    def test_cleanup_expired_sessions(self, secure_session):
        """Test cleanup of expired sessions."""
        # Create sessions with different timeouts
        short_session = SecureSession(session_timeout=1)
        
        token1 = short_session.create_session("user1")
        token2 = short_session.create_session("user2")
        
        # Wait for sessions to expire
        time.sleep(2)
        
        # Create new session (should not expire)
        token3 = short_session.create_session("user3")
        
        # Cleanup expired sessions
        short_session.cleanup_expired_sessions()
        
        # Only the new session should remain
        assert token1 not in short_session.sessions
        assert token2 not in short_session.sessions
        assert token3 in short_session.sessions
    
    def test_get_session_info(self, secure_session):
        """Test getting session information."""
        session_token = secure_session.create_session("test_user")
        
        # Update access count
        secure_session.validate_session(session_token)
        
        session_info = secure_session.get_session_info(session_token)
        
        assert session_info is not None
        assert session_info['user_id'] == "test_user"
        assert session_info['access_count'] == 1
        assert isinstance(session_info['created_at'], datetime)
        assert isinstance(session_info['last_access'], datetime)
    
    def test_get_session_info_invalid_token(self, secure_session):
        """Test getting info for invalid session."""
        session_info = secure_session.get_session_info("invalid_token")
        
        assert session_info is None


class TestPasswordManager:
    """Test cases for PasswordManager."""
    
    @pytest.fixture
    def password_manager(self):
        """Create PasswordManager instance for testing."""
        return PasswordManager("test_service")
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring.set_password')
    def test_store_password_success(self, mock_set_password, password_manager):
        """Test successful password storage."""
        result = password_manager.store_password("test_user", "test_password")
        
        assert result is True
        mock_set_password.assert_called_once_with("test_service", "test_user", "test_password")
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', False)
    def test_store_password_no_keyring(self, password_manager):
        """Test password storage when keyring unavailable."""
        result = password_manager.store_password("test_user", "test_password")
        
        assert result is False
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring.set_password', side_effect=Exception("Keyring error"))
    def test_store_password_error(self, mock_set_password, password_manager):
        """Test password storage with error."""
        result = password_manager.store_password("test_user", "test_password")
        
        assert result is False
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring.get_password', return_value="stored_password")
    def test_get_password_success(self, mock_get_password, password_manager):
        """Test successful password retrieval."""
        password = password_manager.get_password("test_user")
        
        assert password == "stored_password"
        mock_get_password.assert_called_once_with("test_service", "test_user")
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring.get_password', return_value=None)
    def test_get_password_not_found(self, mock_get_password, password_manager):
        """Test password retrieval when not found."""
        password = password_manager.get_password("test_user")
        
        assert password is None
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring.delete_password')
    def test_delete_password_success(self, mock_delete_password, password_manager):
        """Test successful password deletion."""
        result = password_manager.delete_password("test_user")
        
        assert result is True
        mock_delete_password.assert_called_once_with("test_service", "test_user")


class TestSecureMemory:
    """Test cases for SecureMemory."""
    
    @pytest.fixture
    def secure_memory(self):
        """Create SecureMemory instance for testing."""
        return SecureMemory()
    
    def test_store_and_retrieve(self, secure_memory):
        """Test storing and retrieving sensitive data."""
        key = "test_key"
        data = "sensitive_data"
        
        secure_memory.store(key, data)
        retrieved = secure_memory.retrieve(key)
        
        assert retrieved == data
    
    def test_retrieve_nonexistent(self, secure_memory):
        """Test retrieving non-existent data."""
        retrieved = secure_memory.retrieve("nonexistent_key")
        
        assert retrieved is None
    
    def test_delete_data(self, secure_memory):
        """Test secure deletion of data."""
        key = "test_key"
        data = "sensitive_data"
        
        secure_memory.store(key, data)
        assert secure_memory.retrieve(key) == data
        
        secure_memory.delete(key)
        assert secure_memory.retrieve(key) is None
    
    def test_clear_all_data(self, secure_memory):
        """Test clearing all sensitive data."""
        secure_memory.store("key1", "data1")
        secure_memory.store("key2", "data2")
        
        assert secure_memory.retrieve("key1") == "data1"
        assert secure_memory.retrieve("key2") == "data2"
        
        secure_memory.clear_all()
        
        assert secure_memory.retrieve("key1") is None
        assert secure_memory.retrieve("key2") is None


class TestAuditLogger:
    """Test cases for AuditLogger."""
    
    @pytest.fixture
    def audit_logger(self):
        """Create AuditLogger instance for testing."""
        return AuditLogger()
    
    @patch('logging.getLogger')
    def test_log_authentication(self, mock_get_logger, audit_logger):
        """Test authentication logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger.log_authentication("test_user", True, "password")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "AUTH_SUCCESS" in call_args
        assert "test_user" in call_args
        assert "password" in call_args
    
    @patch('logging.getLogger')
    def test_log_authentication_failure(self, mock_get_logger, audit_logger):
        """Test authentication failure logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger.log_authentication("test_user", False, "password")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "AUTH_FAILURE" in call_args
    
    @patch('logging.getLogger')
    def test_log_database_access(self, mock_get_logger, audit_logger):
        """Test database access logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger.log_database_access("READ", "test_user", "entry_search")
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "DB_ACCESS" in call_args
        assert "READ" in call_args
        assert "test_user" in call_args
    
    @patch('logging.getLogger')
    def test_log_security_event(self, mock_get_logger, audit_logger):
        """Test security event logging."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        audit_logger.log_security_event("SUSPICIOUS_ACTIVITY", "test_user", "Multiple failed attempts")
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "SECURITY_EVENT" in call_args
        assert "SUSPICIOUS_ACTIVITY" in call_args


class TestSecurityManager:
    """Test cases for SecurityManager."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        config = Mock()
        config.session_timeout = 3600
        config.max_retries = 3
        config.use_keychain = True
        config.auto_lock_timeout = 1800
        return config
    
    @pytest.fixture
    def security_manager(self, mock_config):
        """Create SecurityManager instance for testing."""
        return SecurityManager(mock_config)
    
    def test_authenticate_user_success(self, security_manager):
        """Test successful user authentication."""
        session_token = security_manager.authenticate_user("test_user", "valid_password")
        
        assert isinstance(session_token, str)
        assert len(session_token) > 32
        
        # Verify session was created
        is_valid = security_manager.validate_session(session_token)
        assert is_valid is True
    
    def test_authenticate_user_weak_password(self, security_manager):
        """Test authentication with weak password."""
        with pytest.raises(AuthenticationError):
            security_manager.authenticate_user("test_user", "weak")  # Less than 8 chars
    
    def test_rate_limiting(self, security_manager):
        """Test authentication rate limiting."""
        user_id = "test_user"
        
        # Perform multiple failed attempts
        for _ in range(3):
            try:
                security_manager.authenticate_user(user_id, "weak")
            except AuthenticationError:
                pass
        
        # Next attempt should be rate limited
        with pytest.raises(AuthenticationError, match="Too many authentication attempts"):
            security_manager.authenticate_user(user_id, "weak")
    
    def test_validate_session_locked_system(self, security_manager):
        """Test session validation when system is locked."""
        # Create and validate session first
        session_token = security_manager.authenticate_user("test_user", "valid_password")
        assert security_manager.validate_session(session_token) is True
        
        # Lock system
        security_manager.lock_system()
        
        # Session validation should fail
        with pytest.raises(SecurityError, match="System is locked"):
            security_manager.validate_session(session_token)
    
    def test_logout_user(self, security_manager):
        """Test user logout."""
        session_token = security_manager.authenticate_user("test_user", "valid_password")
        
        # Verify session exists
        assert security_manager.validate_session(session_token) is True
        
        # Logout user
        security_manager.logout_user(session_token)
        
        # Session should no longer be valid
        assert security_manager.validate_session(session_token) is False
    
    def test_lock_system(self, security_manager):
        """Test system locking."""
        # Create session
        session_token = security_manager.authenticate_user("test_user", "valid_password")
        
        # Lock system
        security_manager.lock_system()
        
        assert security_manager.is_locked is True
        
        # All sessions should be destroyed
        assert len(security_manager.session_manager.sessions) == 0
    
    def test_unlock_system(self, security_manager):
        """Test system unlocking."""
        # Lock system first
        security_manager.lock_system()
        assert security_manager.is_locked is True
        
        # Unlock system
        session_token = security_manager.unlock_system("test_user", "valid_password")
        
        assert security_manager.is_locked is False
        assert isinstance(session_token, str)
    
    def test_unlock_system_already_unlocked(self, security_manager):
        """Test unlocking system when already unlocked."""
        with pytest.raises(SecurityError, match="System is not locked"):
            security_manager.unlock_system("test_user", "valid_password")
    
    def test_auto_lock_check(self, security_manager):
        """Test automatic system locking."""
        # Set very short timeout for testing
        security_manager.auto_lock_timeout = 1  # 1 second
        
        # Update activity and check - should not lock
        security_manager._update_activity()
        security_manager.check_auto_lock()
        assert security_manager.is_locked is False
        
        # Wait for timeout and check again
        time.sleep(2)
        security_manager.check_auto_lock()
        assert security_manager.is_locked is True
    
    def test_rate_limit_reset_on_success(self, security_manager):
        """Test that rate limiting resets on successful authentication."""
        user_id = "test_user"
        
        # Perform 2 failed attempts
        for _ in range(2):
            try:
                security_manager.authenticate_user(user_id, "weak")
            except AuthenticationError:
                pass
        
        # Successful authentication should reset rate limiting
        session_token = security_manager.authenticate_user(user_id, "valid_password")
        assert isinstance(session_token, str)
        
        # Should be able to authenticate again
        security_manager.logout_user(session_token)
        session_token2 = security_manager.authenticate_user(user_id, "valid_password2")
        assert isinstance(session_token2, str)
    
    def test_concurrent_sessions(self, security_manager):
        """Test handling of concurrent sessions."""
        # Create multiple sessions for same user
        session1 = security_manager.authenticate_user("user1", "password1")
        session2 = security_manager.authenticate_user("user2", "password2")
        
        # Both sessions should be valid
        assert security_manager.validate_session(session1) is True
        assert security_manager.validate_session(session2) is True
        
        # Logout one session
        security_manager.logout_user(session1)
        
        # Only second session should remain valid
        assert security_manager.validate_session(session1) is False
        assert security_manager.validate_session(session2) is True
    
    def test_cleanup(self, security_manager):
        """Test security manager cleanup."""
        # Create session and store data
        session_token = security_manager.authenticate_user("test_user", "valid_password")
        security_manager.secure_memory.store("test_key", "test_data")
        
        # Cleanup should clear everything
        security_manager.cleanup()
        
        # All sensitive data should be cleared
        assert security_manager.secure_memory.retrieve("test_key") is None
        assert len(security_manager.session_manager.sessions) == 0
    
    def test_activity_update(self, security_manager):
        """Test activity timestamp update."""
        initial_activity = security_manager.last_activity
        
        # Small delay to ensure timestamp difference
        time.sleep(0.1)
        
        # Update activity
        security_manager._update_activity()
        
        assert security_manager.last_activity > initial_activity
    
    def test_auth_attempt_recording(self, security_manager):
        """Test authentication attempt recording."""
        user_id = "test_user"
        
        # Record attempt
        security_manager._record_auth_attempt(user_id)
        
        # Should have recorded attempt
        assert user_id in security_manager.auth_attempts
        assert len(security_manager.auth_attempts[user_id]) == 1
    
    def test_rate_limit_window_cleanup(self, security_manager):
        """Test cleanup of old authentication attempts."""
        user_id = "test_user"
        
        # Manually add old attempt (simulate old timestamp)
        old_time = time.time() - 400  # 400 seconds ago (outside 5-minute window)
        security_manager.auth_attempts[user_id] = [old_time]
        
        # Check rate limit (should clean up old attempts)
        is_allowed = security_manager._check_rate_limit(user_id)
        
        assert is_allowed is True
        assert len(security_manager.auth_attempts[user_id]) == 0


class TestSecurityIntegration:
    """Integration tests for security components."""
    
    def test_complete_authentication_flow(self):
        """Test complete authentication and session management flow."""
        mock_config = Mock()
        mock_config.session_timeout = 3600
        mock_config.max_retries = 3
        mock_config.use_keychain = True
        mock_config.auto_lock_timeout = 1800
        
        security_manager = SecurityManager(mock_config)
        
        # 1. Authenticate user
        session_token = security_manager.authenticate_user("test_user", "secure_password")
        assert isinstance(session_token, str)
        
        # 2. Validate session multiple times
        for _ in range(3):
            assert security_manager.validate_session(session_token) is True
        
        # 3. Check session info
        session_info = security_manager.session_manager.get_session_info(session_token)
        assert session_info['access_count'] == 3
        
        # 4. Store sensitive data
        security_manager.secure_memory.store("secret", "sensitive_info")
        assert security_manager.secure_memory.retrieve("secret") == "sensitive_info"
        
        # 5. Lock system
        security_manager.lock_system()
        assert security_manager.is_locked is True
        assert security_manager.secure_memory.retrieve("secret") is None
        
        # 6. Unlock system
        new_session = security_manager.unlock_system("test_user", "secure_password")
        assert security_manager.is_locked is False
        assert isinstance(new_session, str)
        assert new_session != session_token  # New session created
    
    @patch('keepass_mcp_server.security.KEYRING_AVAILABLE', True)
    @patch('keepass_mcp_server.security.keyring')
    def test_keychain_integration(self, mock_keyring):
        """Test integration with system keychain."""
        mock_config = Mock()
        mock_config.session_timeout = 3600
        mock_config.max_retries = 3
        mock_config.use_keychain = True
        mock_config.auto_lock_timeout = 1800
        
        security_manager = SecurityManager(mock_config)
        
        # Mock keyring methods
        mock_keyring.set_password.return_value = None
        mock_keyring.delete_password.return_value = None
        
        # Authenticate user (should store password in keychain)
        session_token = security_manager.authenticate_user("test_user", "secure_password")
        
        # Verify keychain was used
        mock_keyring.set_password.assert_called_with("keepass-mcp-server", "test_user", "secure_password")
        
        # Logout should clear keychain
        security_manager.logout_user(session_token)
        
        # Lock system should also clear keychain
        security_manager.lock_system()


if __name__ == "__main__":
    pytest.main([__file__])
