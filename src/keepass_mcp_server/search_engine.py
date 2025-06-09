"""
Advanced search engine for KeePass entries and groups.
"""

import logging
import re
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from .exceptions import ValidationError
from .validators import Validators


class SearchEngine:
    """Advanced search functionality for KeePass database entries."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.search_history: List[Dict[str, Any]] = []
        self.max_history = 100

    def search_entries(
        self,
        entries: List[Dict[str, Any]],
        query: str = "",
        search_fields: List[str] = None,
        case_sensitive: bool = False,
        exact_match: bool = False,
        regex_search: bool = False,
        tags: List[str] = None,
        group_filter: str = None,
        date_created_after: datetime = None,
        date_created_before: datetime = None,
        date_modified_after: datetime = None,
        date_modified_before: datetime = None,
        has_url: bool = None,
        has_notes: bool = None,
        has_attachments: bool = None,
        password_age_days: int = None,
        sort_by: str = "relevance",
        limit: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Advanced search for entries with multiple criteria.

        Args:
            entries: List of entry dictionaries to search
            query: Search query string
            search_fields: Fields to search in (title, username, url, notes, tags)
            case_sensitive: Whether search should be case sensitive
            exact_match: Whether to require exact string match
            regex_search: Whether to use regex pattern matching
            tags: Tags that entries must have
            group_filter: Group name/path filter
            date_created_after: Only entries created after this date
            date_created_before: Only entries created before this date
            date_modified_after: Only entries modified after this date
            date_modified_before: Only entries modified before this date
            has_url: Filter by presence of URL
            has_notes: Filter by presence of notes
            has_attachments: Filter by presence of attachments
            password_age_days: Find entries with passwords older than N days
            sort_by: Sort method (relevance, title, date_created, date_modified)
            limit: Maximum number of results to return

        Returns:
            List of matching entries with relevance scores
        """
        try:
            # Validate inputs
            if query:
                query = Validators.validate_search_query(query)

            if search_fields is None:
                search_fields = ["title", "username", "url", "notes", "tags"]

            # Record search in history
            self._record_search(query, search_fields, tags, group_filter)

            results = []

            for entry in entries:
                # Apply filters
                if not self._apply_filters(
                    entry,
                    group_filter=group_filter,
                    date_created_after=date_created_after,
                    date_created_before=date_created_before,
                    date_modified_after=date_modified_after,
                    date_modified_before=date_modified_before,
                    has_url=has_url,
                    has_notes=has_notes,
                    has_attachments=has_attachments,
                    password_age_days=password_age_days,
                    tags=tags,
                ):
                    continue

                # Search query matching
                if query:
                    relevance_score = self._calculate_relevance(
                        entry,
                        query,
                        search_fields,
                        case_sensitive=case_sensitive,
                        exact_match=exact_match,
                        regex_search=regex_search,
                    )

                    if relevance_score > 0:
                        entry_copy = entry.copy()
                        entry_copy["relevance_score"] = relevance_score
                        results.append(entry_copy)
                else:
                    # No query, just apply filters
                    entry_copy = entry.copy()
                    entry_copy["relevance_score"] = 1.0
                    results.append(entry_copy)

            # Sort results
            results = self._sort_results(results, sort_by)

            # Apply limit
            if limit and limit > 0:
                results = results[:limit]

            self.logger.info(f"Search completed: {len(results)} results found")
            return results

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            raise ValidationError(f"Search failed: {e}")

    def search_by_url(
        self, entries: List[Dict[str, Any]], url: str, fuzzy_match: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search for entries matching a specific URL.

        Args:
            entries: List of entry dictionaries
            url: URL to search for
            fuzzy_match: Allow fuzzy URL matching

        Returns:
            List of matching entries sorted by relevance
        """
        try:
            url = Validators.validate_url(url)
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()

            results = []

            for entry in entries:
                entry_url = entry.get("url", "").strip()
                if not entry_url:
                    continue

                relevance = self._calculate_url_relevance(
                    entry_url, url, domain, fuzzy_match
                )
                if relevance > 0:
                    entry_copy = entry.copy()
                    entry_copy["relevance_score"] = relevance
                    results.append(entry_copy)

            # Sort by relevance
            results.sort(key=lambda x: x["relevance_score"], reverse=True)

            self.logger.info(f"URL search for '{domain}': {len(results)} results")
            return results

        except Exception as e:
            self.logger.error(f"URL search failed: {e}")
            raise ValidationError(f"URL search failed: {e}")

    def search_similar_entries(
        self,
        entries: List[Dict[str, Any]],
        reference_entry: Dict[str, Any],
        similarity_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Find entries similar to a reference entry.

        Args:
            entries: List of entry dictionaries
            reference_entry: Entry to find similar entries to
            similarity_threshold: Minimum similarity score (0.0-1.0)

        Returns:
            List of similar entries with similarity scores
        """
        try:
            results = []
            ref_title = reference_entry.get("title", "").lower()
            ref_url = reference_entry.get("url", "").lower()
            ref_username = reference_entry.get("username", "").lower()
            ref_tags = set(tag.lower() for tag in reference_entry.get("tags", []))

            for entry in entries:
                if entry.get("id") == reference_entry.get("id"):
                    continue  # Skip the reference entry itself

                similarity = self._calculate_entry_similarity(
                    entry, ref_title, ref_url, ref_username, ref_tags
                )

                if similarity >= similarity_threshold:
                    entry_copy = entry.copy()
                    entry_copy["similarity_score"] = similarity
                    results.append(entry_copy)

            # Sort by similarity
            results.sort(key=lambda x: x["similarity_score"], reverse=True)

            self.logger.info(f"Similarity search: {len(results)} similar entries found")
            return results

        except Exception as e:
            self.logger.error(f"Similarity search failed: {e}")
            raise ValidationError(f"Similarity search failed: {e}")

    def search_weak_passwords(
        self,
        entries: List[Dict[str, Any]],
        min_length: int = 8,
        require_complexity: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find entries with weak passwords.

        Args:
            entries: List of entry dictionaries
            min_length: Minimum password length
            require_complexity: Require mixed character types

        Returns:
            List of entries with weak passwords
        """
        try:
            weak_entries = []

            for entry in entries:
                password = entry.get("password", "")
                if not password:
                    continue

                is_weak = False
                weakness_reasons = []

                # Check length
                if len(password) < min_length:
                    is_weak = True
                    weakness_reasons.append(f"Too short (< {min_length} chars)")

                # Check complexity
                if require_complexity:
                    has_upper = any(c.isupper() for c in password)
                    has_lower = any(c.islower() for c in password)
                    has_digit = any(c.isdigit() for c in password)
                    has_symbol = any(not c.isalnum() for c in password)

                    complexity_count = sum(
                        [has_upper, has_lower, has_digit, has_symbol]
                    )
                    if complexity_count < 3:
                        is_weak = True
                        weakness_reasons.append("Low complexity")

                # Check common passwords
                common_passwords = [
                    "password",
                    "123456",
                    "qwerty",
                    "abc123",
                    "password123",
                    "admin",
                    "letmein",
                    "welcome",
                    "monkey",
                    "dragon",
                ]
                if password.lower() in common_passwords:
                    is_weak = True
                    weakness_reasons.append("Common password")

                # Check for patterns
                if self._has_keyboard_pattern(password):
                    is_weak = True
                    weakness_reasons.append("Keyboard pattern")

                if is_weak:
                    entry_copy = entry.copy()
                    entry_copy["weakness_reasons"] = weakness_reasons
                    entry_copy["password_strength"] = "weak"
                    weak_entries.append(entry_copy)

            self.logger.info(f"Weak password search: {len(weak_entries)} entries found")
            return weak_entries

        except Exception as e:
            self.logger.error(f"Weak password search failed: {e}")
            raise ValidationError(f"Weak password search failed: {e}")

    def search_duplicates(
        self, entries: List[Dict[str, Any]], check_fields: List[str] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Find duplicate entries based on specified fields.

        Args:
            entries: List of entry dictionaries
            check_fields: Fields to check for duplicates (title, username, url)

        Returns:
            List of lists, each containing duplicate entries
        """
        try:
            if check_fields is None:
                check_fields = ["title", "username", "url"]

            duplicates = {}

            for entry in entries:
                # Create signature for duplicate detection
                signature_parts = []
                for field in check_fields:
                    value = entry.get(field, "").strip().lower()
                    if value:
                        signature_parts.append(f"{field}:{value}")

                if signature_parts:
                    signature = "|".join(signature_parts)

                    if signature not in duplicates:
                        duplicates[signature] = []
                    duplicates[signature].append(entry)

            # Return only groups with actual duplicates
            duplicate_groups = [
                group for group in duplicates.values() if len(group) > 1
            ]

            self.logger.info(
                f"Duplicate search: {len(duplicate_groups)} duplicate groups found"
            )
            return duplicate_groups

        except Exception as e:
            self.logger.error(f"Duplicate search failed: {e}")
            raise ValidationError(f"Duplicate search failed: {e}")

    def get_search_suggestions(
        self,
        partial_query: str,
        entries: List[Dict[str, Any]],
        max_suggestions: int = 10,
    ) -> List[str]:
        """
        Get search suggestions based on partial query.

        Args:
            partial_query: Partial search query
            entries: List of entry dictionaries
            max_suggestions: Maximum number of suggestions

        Returns:
            List of search suggestions
        """
        try:
            if len(partial_query) < 2:
                return []

            suggestions = set()
            query_lower = partial_query.lower()

            for entry in entries:
                # Check title
                title = entry.get("title", "")
                if query_lower in title.lower():
                    suggestions.add(title)

                # Check URL domain
                url = entry.get("url", "")
                if url:
                    try:
                        domain = urllib.parse.urlparse(url).netloc
                        if query_lower in domain.lower():
                            suggestions.add(domain)
                    except:
                        pass

                # Check tags
                for tag in entry.get("tags", []):
                    if query_lower in tag.lower():
                        suggestions.add(tag)

                # Check username
                username = entry.get("username", "")
                if query_lower in username.lower():
                    suggestions.add(username)

            # Sort suggestions by length (shorter first, more specific)
            sorted_suggestions = sorted(list(suggestions), key=len)

            return sorted_suggestions[:max_suggestions]

        except Exception as e:
            self.logger.error(f"Search suggestions failed: {e}")
            return []

    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent search history."""
        return self.search_history[-limit:] if self.search_history else []

    def clear_search_history(self) -> None:
        """Clear search history."""
        self.search_history.clear()
        self.logger.info("Search history cleared")

    def _apply_filters(
        self,
        entry: Dict[str, Any],
        group_filter: str = None,
        date_created_after: datetime = None,
        date_created_before: datetime = None,
        date_modified_after: datetime = None,
        date_modified_before: datetime = None,
        has_url: bool = None,
        has_notes: bool = None,
        has_attachments: bool = None,
        password_age_days: int = None,
        tags: List[str] = None,
    ) -> bool:
        """Apply various filters to an entry."""

        # Group filter
        if group_filter:
            entry_group = entry.get("group", "").lower()
            if group_filter.lower() not in entry_group:
                return False

        # Date filters
        if date_created_after:
            entry_created = entry.get("date_created")
            if not entry_created or entry_created < date_created_after:
                return False

        if date_created_before:
            entry_created = entry.get("date_created")
            if not entry_created or entry_created > date_created_before:
                return False

        if date_modified_after:
            entry_modified = entry.get("date_modified")
            if not entry_modified or entry_modified < date_modified_after:
                return False

        if date_modified_before:
            entry_modified = entry.get("date_modified")
            if not entry_modified or entry_modified > date_modified_before:
                return False

        # Content filters
        if has_url is not None:
            entry_has_url = bool(entry.get("url", "").strip())
            if has_url != entry_has_url:
                return False

        if has_notes is not None:
            entry_has_notes = bool(entry.get("notes", "").strip())
            if has_notes != entry_has_notes:
                return False

        if has_attachments is not None:
            entry_has_attachments = bool(entry.get("attachments", []))
            if has_attachments != entry_has_attachments:
                return False

        # Password age filter
        if password_age_days is not None:
            password_changed = entry.get("password_changed")
            if password_changed:
                age = (datetime.now() - password_changed).days
                if age < password_age_days:
                    return False

        # Tags filter
        if tags:
            entry_tags = set(tag.lower() for tag in entry.get("tags", []))
            required_tags = set(tag.lower() for tag in tags)
            if not required_tags.issubset(entry_tags):
                return False

        return True

    def _calculate_relevance(
        self,
        entry: Dict[str, Any],
        query: str,
        search_fields: List[str],
        case_sensitive: bool = False,
        exact_match: bool = False,
        regex_search: bool = False,
    ) -> float:
        """Calculate relevance score for an entry against a query."""

        if not query:
            return 1.0

        total_score = 0.0
        field_weights = {
            "title": 3.0,
            "username": 2.0,
            "url": 2.5,
            "notes": 1.0,
            "tags": 2.0,
        }

        search_query = query if case_sensitive else query.lower()

        for field in search_fields:
            if field not in entry:
                continue

            field_value = str(entry[field])
            if not case_sensitive:
                field_value = field_value.lower()

            field_score = 0.0
            weight = field_weights.get(field, 1.0)

            if regex_search:
                try:
                    if re.search(search_query, field_value):
                        field_score = weight
                except re.error:
                    # Fall back to normal search if regex is invalid
                    if search_query in field_value:
                        field_score = weight
            elif exact_match:
                if search_query == field_value:
                    field_score = weight
            else:
                if search_query in field_value:
                    # Higher score for matches at the beginning
                    if field_value.startswith(search_query):
                        field_score = weight
                    else:
                        field_score = weight * 0.7

                    # Bonus for whole word matches
                    if " " + search_query + " " in " " + field_value + " ":
                        field_score *= 1.2

            total_score += field_score

        return min(total_score, 10.0)  # Cap at 10.0

    def _calculate_url_relevance(
        self, entry_url: str, search_url: str, search_domain: str, fuzzy_match: bool
    ) -> float:
        """Calculate URL relevance score."""

        try:
            entry_parsed = urllib.parse.urlparse(entry_url)
            entry_domain = entry_parsed.netloc.lower()

            # Exact URL match
            if entry_url.lower() == search_url.lower():
                return 10.0

            # Exact domain match
            if entry_domain == search_domain:
                return 8.0

            if fuzzy_match:
                # Subdomain match
                if search_domain in entry_domain or entry_domain in search_domain:
                    return 6.0

                # Domain parts match
                search_parts = search_domain.split(".")
                entry_parts = entry_domain.split(".")

                common_parts = set(search_parts) & set(entry_parts)
                if common_parts and len(common_parts) >= 2:
                    return 4.0

                # Partial domain match
                for part in search_parts:
                    if len(part) > 3 and part in entry_domain:
                        return 2.0

            return 0.0

        except:
            return 0.0

    def _calculate_entry_similarity(
        self,
        entry: Dict[str, Any],
        ref_title: str,
        ref_url: str,
        ref_username: str,
        ref_tags: Set[str],
    ) -> float:
        """Calculate similarity between entries."""

        similarity = 0.0

        # Title similarity
        entry_title = entry.get("title", "").lower()
        if entry_title and ref_title:
            if entry_title == ref_title:
                similarity += 0.4
            elif ref_title in entry_title or entry_title in ref_title:
                similarity += 0.2

        # URL similarity
        entry_url = entry.get("url", "").lower()
        if entry_url and ref_url:
            try:
                entry_domain = urllib.parse.urlparse(entry_url).netloc
                ref_domain = urllib.parse.urlparse(ref_url).netloc
                if entry_domain == ref_domain:
                    similarity += 0.3
                elif ref_domain in entry_domain or entry_domain in ref_domain:
                    similarity += 0.15
            except:
                pass

        # Username similarity
        entry_username = entry.get("username", "").lower()
        if entry_username and ref_username:
            if entry_username == ref_username:
                similarity += 0.2

        # Tags similarity
        entry_tags = set(tag.lower() for tag in entry.get("tags", []))
        if entry_tags and ref_tags:
            common_tags = entry_tags & ref_tags
            if common_tags:
                similarity += (
                    0.1 * len(common_tags) / max(len(entry_tags), len(ref_tags))
                )

        return min(similarity, 1.0)

    def _has_keyboard_pattern(self, password: str) -> bool:
        """Check if password contains keyboard patterns."""
        keyboard_patterns = [
            "qwerty",
            "asdf",
            "zxcv",
            "123456",
            "098765",
            "qwertyuiop",
            "asdfghjkl",
            "zxcvbnm",
        ]

        password_lower = password.lower()
        for pattern in keyboard_patterns:
            if pattern in password_lower:
                return True

        return False

    def _sort_results(
        self, results: List[Dict[str, Any]], sort_by: str
    ) -> List[Dict[str, Any]]:
        """Sort search results."""

        if sort_by == "relevance":
            return sorted(
                results, key=lambda x: x.get("relevance_score", 0), reverse=True
            )
        elif sort_by == "title":
            return sorted(results, key=lambda x: x.get("title", "").lower())
        elif sort_by == "date_created":
            return sorted(
                results, key=lambda x: x.get("date_created", datetime.min), reverse=True
            )
        elif sort_by == "date_modified":
            return sorted(
                results,
                key=lambda x: x.get("date_modified", datetime.min),
                reverse=True,
            )
        else:
            return results

    def _record_search(
        self,
        query: str,
        search_fields: List[str],
        tags: List[str] = None,
        group_filter: str = None,
    ) -> None:
        """Record search in history."""
        search_record = {
            "timestamp": datetime.now(),
            "query": query,
            "fields": search_fields,
            "tags": tags or [],
            "group_filter": group_filter,
        }

        self.search_history.append(search_record)

        # Keep only recent searches
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[-self.max_history :]
