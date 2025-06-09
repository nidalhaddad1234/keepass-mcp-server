"""
Input validation and sanitization for KeePass MCP Server.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional
from pathlib import Path

from .exceptions import ValidationError


class Validators:
    """Collection of validation functions for various input types."""
    
    # Regular expressions for validation
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    URL_REGEX = re.compile(
        r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    )
    UUID_REGEX = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    
    @staticmethod
    def validate_entry_title(title: str) -> str:
        """Validate and sanitize entry title."""
        if not title or not isinstance(title, str):
            raise ValidationError("Entry title must be a non-empty string")
        
        title = title.strip()
        if len(title) < 1:
            raise ValidationError("Entry title cannot be empty")
        
        if len(title) > 200:
            raise ValidationError("Entry title cannot exceed 200 characters")
        
        # Remove dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in dangerous_chars:
            title = title.replace(char, '')
        
        return title
    
    @staticmethod
    def validate_username(username: str) -> str:
        """Validate and sanitize username."""
        if not isinstance(username, str):
            raise ValidationError("Username must be a string")
        
        username = username.strip()
        if len(username) > 100:
            raise ValidationError("Username cannot exceed 100 characters")
        
        return username
    
    @staticmethod
    def validate_password(password: str) -> str:
        """Validate password."""
        if not isinstance(password, str):
            raise ValidationError("Password must be a string")
        
        if len(password) > 1000:
            raise ValidationError("Password cannot exceed 1000 characters")
        
        return password
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and normalize URL."""
        if not isinstance(url, str):
            raise ValidationError("URL must be a string")
        
        url = url.strip()
        if not url:
            return ""
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Validate URL format
        try:
            parsed = urllib.parse.urlparse(url)
            if not parsed.netloc:
                raise ValidationError(f"Invalid URL format: {url}")
        except Exception:
            raise ValidationError(f"Invalid URL format: {url}")
        
        return url
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        if not isinstance(email, str):
            raise ValidationError("Email must be a string")
        
        email = email.strip().lower()
        if not email:
            return ""
        
        if not Validators.EMAIL_REGEX.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return email
    
    @staticmethod
    def validate_group_name(name: str) -> str:
        """Validate and sanitize group name."""
        if not name or not isinstance(name, str):
            raise ValidationError("Group name must be a non-empty string")
        
        name = name.strip()
        if len(name) < 1:
            raise ValidationError("Group name cannot be empty")
        
        if len(name) > 100:
            raise ValidationError("Group name cannot exceed 100 characters")
        
        # Check for reserved names
        reserved_names = ['root', 'recycle bin', 'backup']
        if name.lower() in reserved_names:
            raise ValidationError(f"Group name '{name}' is reserved")
        
        # Remove dangerous characters
        dangerous_chars = ['/', '\\', '<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in dangerous_chars:
            name = name.replace(char, '')
        
        return name
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """Validate UUID format."""
        if not isinstance(uuid_str, str):
            raise ValidationError("UUID must be a string")
        
        uuid_str = uuid_str.strip()
        if not Validators.UUID_REGEX.match(uuid_str):
            raise ValidationError(f"Invalid UUID format: {uuid_str}")
        
        return uuid_str.lower()
    
    @staticmethod
    def validate_notes(notes: str) -> str:
        """Validate and sanitize notes field."""
        if not isinstance(notes, str):
            raise ValidationError("Notes must be a string")
        
        if len(notes) > 10000:
            raise ValidationError("Notes cannot exceed 10000 characters")
        
        return notes
    
    @staticmethod
    def validate_tags(tags: List[str]) -> List[str]:
        """Validate and sanitize tags."""
        if not isinstance(tags, list):
            raise ValidationError("Tags must be a list")
        
        validated_tags = []
        for tag in tags:
            if not isinstance(tag, str):
                raise ValidationError("Each tag must be a string")
            
            tag = tag.strip()
            if len(tag) > 50:
                raise ValidationError("Tag cannot exceed 50 characters")
            
            if tag and tag not in validated_tags:
                validated_tags.append(tag)
        
        if len(validated_tags) > 20:
            raise ValidationError("Cannot have more than 20 tags")
        
        return validated_tags
    
    @staticmethod
    def validate_custom_fields(custom_fields: Dict[str, str]) -> Dict[str, str]:
        """Validate and sanitize custom fields."""
        if not isinstance(custom_fields, dict):
            raise ValidationError("Custom fields must be a dictionary")
        
        validated_fields = {}
        for key, value in custom_fields.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValidationError("Custom field keys and values must be strings")
            
            key = key.strip()
            if len(key) > 100:
                raise ValidationError("Custom field key cannot exceed 100 characters")
            
            if len(value) > 1000:
                raise ValidationError("Custom field value cannot exceed 1000 characters")
            
            if key:
                validated_fields[key] = value
        
        if len(validated_fields) > 50:
            raise ValidationError("Cannot have more than 50 custom fields")
        
        return validated_fields
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """Validate and sanitize search query."""
        if not isinstance(query, str):
            raise ValidationError("Search query must be a string")
        
        query = query.strip()
        if len(query) > 200:
            raise ValidationError("Search query cannot exceed 200 characters")
        
        # Remove potentially dangerous SQL-like characters
        dangerous_patterns = [';', '--', '/*', '*/', 'DROP ', 'DELETE ', 'INSERT ']
        for pattern in dangerous_patterns:
            if pattern.lower() in query.lower():
                raise ValidationError(f"Search query contains invalid pattern: {pattern}")
        
        return query
    
    @staticmethod
    def validate_file_path(file_path: str) -> Path:
        """Validate file path."""
        if not isinstance(file_path, str):
            raise ValidationError("File path must be a string")
        
        try:
            path = Path(file_path).resolve()
        except Exception as e:
            raise ValidationError(f"Invalid file path: {e}")
        
        # Check for path traversal attempts
        if '..' in str(path):
            raise ValidationError("Path traversal not allowed")
        
        return path
    
    @staticmethod
    def validate_password_requirements(
        length: int = 12,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = False
    ) -> Dict[str, Any]:
        """Validate password generation requirements."""
        if not isinstance(length, int) or length < 4 or length > 128:
            raise ValidationError("Password length must be between 4 and 128 characters")
        
        # At least one character type must be selected
        if not any([include_uppercase, include_lowercase, include_numbers, include_symbols]):
            raise ValidationError("At least one character type must be selected")
        
        return {
            'length': length,
            'include_uppercase': include_uppercase,
            'include_lowercase': include_lowercase,
            'include_numbers': include_numbers,
            'include_symbols': include_symbols,
            'exclude_ambiguous': exclude_ambiguous
        }
    
    @staticmethod
    def sanitize_for_logging(data: Any) -> str:
        """Sanitize data for safe logging (remove sensitive information)."""
        if isinstance(data, dict):
            sanitized = {}
            sensitive_keys = ['password', 'secret', 'key', 'token', 'credential']
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = Validators.sanitize_for_logging(value)
            
            return str(sanitized)
        
        elif isinstance(data, list):
            return str([Validators.sanitize_for_logging(item) for item in data])
        
        elif isinstance(data, str):
            # Don't log long strings that might contain sensitive data
            if len(data) > 100:
                return f"[STRING:{len(data)} chars]"
            return data
        
        else:
            return str(data)
