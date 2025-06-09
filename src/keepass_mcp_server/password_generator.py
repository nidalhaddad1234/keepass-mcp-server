"""
Secure password generation for KeePass MCP Server.
"""

import logging
import secrets
import string
from typing import Any, Dict, List

from .exceptions import PasswordGenerationError, ValidationError
from .validators import Validators


class PasswordGenerator:
    """Secure password generator with customizable rules."""

    # Character sets for password generation
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    NUMBERS = string.digits
    SYMBOLS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    AMBIGUOUS = "0O1lI"  # Characters that can be confused

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_password(
        self,
        length: int = 16,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = False,
        exclude_similar: bool = False,
        min_uppercase: int = 1,
        min_lowercase: int = 1,
        min_numbers: int = 1,
        min_symbols: int = 1,
        custom_symbols: str = None,
        forbidden_chars: str = None,
    ) -> str:
        """
        Generate a secure password with specified requirements.

        Args:
            length: Password length (4-128)
            include_uppercase: Include uppercase letters
            include_lowercase: Include lowercase letters
            include_numbers: Include numbers
            include_symbols: Include symbols
            exclude_ambiguous: Exclude ambiguous characters (0, O, 1, l, I)
            exclude_similar: Exclude similar looking characters
            min_uppercase: Minimum number of uppercase letters
            min_lowercase: Minimum number of lowercase letters
            min_numbers: Minimum number of numbers
            min_symbols: Minimum number of symbols
            custom_symbols: Custom symbol set to use instead of default
            forbidden_chars: Characters to exclude

        Returns:
            Generated password string

        Raises:
            PasswordGenerationError: If generation fails or requirements are impossible
        """
        try:
            # Validate requirements
            requirements = Validators.validate_password_requirements(
                length=length,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_numbers=include_numbers,
                include_symbols=include_symbols,
                exclude_ambiguous=exclude_ambiguous,
            )

            # Build character sets
            charset = self._build_charset(
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_numbers=include_numbers,
                include_symbols=include_symbols,
                exclude_ambiguous=exclude_ambiguous,
                exclude_similar=exclude_similar,
                custom_symbols=custom_symbols,
                forbidden_chars=forbidden_chars,
            )

            if not charset:
                raise PasswordGenerationError(
                    "No characters available for password generation"
                )

            # Check if minimum requirements are achievable
            total_minimums = (
                (min_uppercase if include_uppercase else 0)
                + (min_lowercase if include_lowercase else 0)
                + (min_numbers if include_numbers else 0)
                + (min_symbols if include_symbols else 0)
            )

            if total_minimums > length:
                raise PasswordGenerationError(
                    f"Minimum character requirements ({total_minimums}) exceed password length ({length})"
                )

            # Generate password ensuring minimum requirements
            password = self._generate_with_requirements(
                length=length,
                charset=charset,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_numbers=include_numbers,
                include_symbols=include_symbols,
                min_uppercase=min_uppercase,
                min_lowercase=min_lowercase,
                min_numbers=min_numbers,
                min_symbols=min_symbols,
                exclude_ambiguous=exclude_ambiguous,
                exclude_similar=exclude_similar,
                custom_symbols=custom_symbols,
                forbidden_chars=forbidden_chars,
            )

            # Validate generated password
            if not self._validate_generated_password(
                password=password,
                include_uppercase=include_uppercase,
                include_lowercase=include_lowercase,
                include_numbers=include_numbers,
                include_symbols=include_symbols,
                min_uppercase=min_uppercase,
                min_lowercase=min_lowercase,
                min_numbers=min_numbers,
                min_symbols=min_symbols,
            ):
                # Retry generation if validation fails
                return self.generate_password(
                    length=length,
                    include_uppercase=include_uppercase,
                    include_lowercase=include_lowercase,
                    include_numbers=include_numbers,
                    include_symbols=include_symbols,
                    exclude_ambiguous=exclude_ambiguous,
                    exclude_similar=exclude_similar,
                    min_uppercase=min_uppercase,
                    min_lowercase=min_lowercase,
                    min_numbers=min_numbers,
                    min_symbols=min_symbols,
                    custom_symbols=custom_symbols,
                    forbidden_chars=forbidden_chars,
                )

            self.logger.info(f"Generated password with length {length}")
            return password

        except Exception as e:
            self.logger.error(f"Password generation failed: {e}")
            raise PasswordGenerationError(f"Failed to generate password: {e}")

    def generate_passphrase(
        self,
        word_count: int = 4,
        separator: str = "-",
        include_numbers: bool = True,
        capitalize: bool = True,
        word_list: List[str] = None,
    ) -> str:
        """
        Generate a passphrase using random words.

        Args:
            word_count: Number of words in passphrase
            separator: Character to separate words
            include_numbers: Include random numbers
            capitalize: Capitalize first letter of each word
            word_list: Custom word list (uses default if None)

        Returns:
            Generated passphrase
        """
        try:
            if word_count < 2 or word_count > 10:
                raise ValidationError("Word count must be between 2 and 10")

            # Default word list (in production, this should be loaded from a file)
            if word_list is None:
                word_list = [
                    "apple",
                    "bridge",
                    "castle",
                    "dragon",
                    "eagle",
                    "forest",
                    "guitar",
                    "harbor",
                    "island",
                    "jungle",
                    "kitchen",
                    "library",
                    "mountain",
                    "ocean",
                    "palace",
                    "quiet",
                    "river",
                    "sunset",
                    "tiger",
                    "umbrella",
                    "village",
                    "window",
                    "yellow",
                    "zebra",
                    "anchor",
                    "butter",
                    "candle",
                    "danger",
                    "engine",
                    "flower",
                    "garden",
                    "hammer",
                    "ice",
                    "jacket",
                    "knight",
                    "ladder",
                    "magic",
                    "nature",
                    "orange",
                    "pencil",
                    "queen",
                    "robot",
                    "silver",
                    "table",
                    "unique",
                    "violet",
                    "wizard",
                    "x-ray",
                ]

            words = []
            for _ in range(word_count):
                word = secrets.choice(word_list)
                if capitalize:
                    word = word.capitalize()
                words.append(word)

            passphrase = separator.join(words)

            if include_numbers:
                # Add 2-3 random numbers
                for _ in range(secrets.randbelow(2) + 2):
                    number = str(secrets.randbelow(100))
                    passphrase += separator + number

            self.logger.info(f"Generated passphrase with {word_count} words")
            return passphrase

        except Exception as e:
            self.logger.error(f"Passphrase generation failed: {e}")
            raise PasswordGenerationError(f"Failed to generate passphrase: {e}")

    def generate_pin(self, length: int = 6) -> str:
        """
        Generate a numeric PIN.

        Args:
            length: PIN length (4-12)

        Returns:
            Generated PIN
        """
        try:
            if length < 4 or length > 12:
                raise ValidationError("PIN length must be between 4 and 12")

            # Ensure first digit is not 0
            pin = str(secrets.randbelow(9) + 1)

            # Add remaining digits
            for _ in range(length - 1):
                pin += str(secrets.randbelow(10))

            self.logger.info(f"Generated PIN with length {length}")
            return pin

        except Exception as e:
            self.logger.error(f"PIN generation failed: {e}")
            raise PasswordGenerationError(f"Failed to generate PIN: {e}")

    def check_password_strength(self, password: str) -> Dict[str, Any]:
        """
        Analyze password strength and provide feedback.

        Args:
            password: Password to analyze

        Returns:
            Dictionary with strength analysis
        """
        try:
            analysis = {
                "score": 0,
                "strength": "Very Weak",
                "feedback": [],
                "length": len(password),
                "has_uppercase": any(c.isupper() for c in password),
                "has_lowercase": any(c.islower() for c in password),
                "has_numbers": any(c.isdigit() for c in password),
                "has_symbols": any(c in self.SYMBOLS for c in password),
                "has_ambiguous": any(c in self.AMBIGUOUS for c in password),
                "character_sets": 0,
                "entropy": 0,
            }

            # Calculate character sets used
            if analysis["has_uppercase"]:
                analysis["character_sets"] += 1
            if analysis["has_lowercase"]:
                analysis["character_sets"] += 1
            if analysis["has_numbers"]:
                analysis["character_sets"] += 1
            if analysis["has_symbols"]:
                analysis["character_sets"] += 1

            # Calculate entropy (simplified)
            charset_size = 0
            if analysis["has_uppercase"]:
                charset_size += 26
            if analysis["has_lowercase"]:
                charset_size += 26
            if analysis["has_numbers"]:
                charset_size += 10
            if analysis["has_symbols"]:
                charset_size += len(self.SYMBOLS)

            if charset_size > 0:
                import math

                analysis["entropy"] = len(password) * math.log2(charset_size)

            # Score calculation
            score = 0

            # Length scoring
            if len(password) >= 12:
                score += 25
            elif len(password) >= 8:
                score += 15
            elif len(password) >= 6:
                score += 5

            # Character set scoring
            score += analysis["character_sets"] * 15

            # Entropy scoring
            if analysis["entropy"] >= 60:
                score += 20
            elif analysis["entropy"] >= 40:
                score += 10

            # Penalty for common patterns
            if password.lower() in ["password", "123456", "qwerty"]:
                score -= 50

            analysis["score"] = max(0, min(100, score))

            # Determine strength
            if analysis["score"] >= 80:
                analysis["strength"] = "Very Strong"
            elif analysis["score"] >= 60:
                analysis["strength"] = "Strong"
            elif analysis["score"] >= 40:
                analysis["strength"] = "Moderate"
            elif analysis["score"] >= 20:
                analysis["strength"] = "Weak"
            else:
                analysis["strength"] = "Very Weak"

            # Generate feedback
            if len(password) < 8:
                analysis["feedback"].append("Use at least 8 characters")
            if not analysis["has_uppercase"]:
                analysis["feedback"].append("Add uppercase letters")
            if not analysis["has_lowercase"]:
                analysis["feedback"].append("Add lowercase letters")
            if not analysis["has_numbers"]:
                analysis["feedback"].append("Add numbers")
            if not analysis["has_symbols"]:
                analysis["feedback"].append("Add symbols")
            if analysis["has_ambiguous"]:
                analysis["feedback"].append(
                    "Avoid ambiguous characters (0, O, 1, l, I)"
                )

            return analysis

        except Exception as e:
            self.logger.error(f"Password strength check failed: {e}")
            raise PasswordGenerationError(f"Failed to check password strength: {e}")

    def _build_charset(
        self,
        include_uppercase: bool,
        include_lowercase: bool,
        include_numbers: bool,
        include_symbols: bool,
        exclude_ambiguous: bool,
        exclude_similar: bool,
        custom_symbols: str,
        forbidden_chars: str,
    ) -> str:
        """Build character set for password generation."""
        charset = ""

        if include_lowercase:
            charset += self.LOWERCASE
        if include_uppercase:
            charset += self.UPPERCASE
        if include_numbers:
            charset += self.NUMBERS
        if include_symbols:
            if custom_symbols:
                charset += custom_symbols
            else:
                charset += self.SYMBOLS

        # Remove excluded characters
        if exclude_ambiguous:
            charset = "".join(c for c in charset if c not in self.AMBIGUOUS)

        if exclude_similar:
            similar_chars = "il1Lo0O"
            charset = "".join(c for c in charset if c not in similar_chars)

        if forbidden_chars:
            charset = "".join(c for c in charset if c not in forbidden_chars)

        # Remove duplicates while preserving order
        seen = set()
        unique_charset = ""
        for char in charset:
            if char not in seen:
                seen.add(char)
                unique_charset += char

        return unique_charset

    def _generate_with_requirements(self, length: int, charset: str, **kwargs) -> str:
        """Generate password ensuring minimum character requirements."""
        password_chars = []

        # Add required characters first
        if kwargs.get("include_uppercase") and kwargs.get("min_uppercase", 1) > 0:
            upper_chars = [c for c in charset if c.isupper()]
            for _ in range(min(kwargs.get("min_uppercase", 1), len(upper_chars))):
                if upper_chars:
                    password_chars.append(secrets.choice(upper_chars))

        if kwargs.get("include_lowercase") and kwargs.get("min_lowercase", 1) > 0:
            lower_chars = [c for c in charset if c.islower()]
            for _ in range(min(kwargs.get("min_lowercase", 1), len(lower_chars))):
                if lower_chars:
                    password_chars.append(secrets.choice(lower_chars))

        if kwargs.get("include_numbers") and kwargs.get("min_numbers", 1) > 0:
            number_chars = [c for c in charset if c.isdigit()]
            for _ in range(min(kwargs.get("min_numbers", 1), len(number_chars))):
                if number_chars:
                    password_chars.append(secrets.choice(number_chars))

        if kwargs.get("include_symbols") and kwargs.get("min_symbols", 1) > 0:
            symbol_chars = [
                c
                for c in charset
                if c in self.SYMBOLS
                or (
                    kwargs.get("custom_symbols")
                    and c in kwargs.get("custom_symbols", "")
                )
            ]
            for _ in range(min(kwargs.get("min_symbols", 1), len(symbol_chars))):
                if symbol_chars:
                    password_chars.append(secrets.choice(symbol_chars))

        # Fill remaining length with random characters
        while len(password_chars) < length:
            password_chars.append(secrets.choice(charset))

        # Shuffle the password
        for i in range(len(password_chars)):
            j = secrets.randbelow(len(password_chars))
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return "".join(password_chars)

    def _validate_generated_password(
        self,
        password: str,
        include_uppercase: bool,
        include_lowercase: bool,
        include_numbers: bool,
        include_symbols: bool,
        min_uppercase: int,
        min_lowercase: int,
        min_numbers: int,
        min_symbols: int,
    ) -> bool:
        """Validate that generated password meets requirements."""
        if include_uppercase and min_uppercase > 0:
            if sum(1 for c in password if c.isupper()) < min_uppercase:
                return False

        if include_lowercase and min_lowercase > 0:
            if sum(1 for c in password if c.islower()) < min_lowercase:
                return False

        if include_numbers and min_numbers > 0:
            if sum(1 for c in password if c.isdigit()) < min_numbers:
                return False

        if include_symbols and min_symbols > 0:
            if sum(1 for c in password if c in self.SYMBOLS) < min_symbols:
                return False

        return True
