"""
Test search functionality for KeePass MCP Server.
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
import urllib.parse

from keepass_mcp_server.search_engine import SearchEngine
from keepass_mcp_server.exceptions import ValidationError


class TestSearchEngine:
    """Test cases for SearchEngine."""
    
    @pytest.fixture
    def search_engine(self):
        """Create SearchEngine instance for testing."""
        return SearchEngine()
    
    @pytest.fixture
    def sample_entries(self):
        """Create sample entries for testing."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(weeks=1)
        
        return [
            {
                'id': 'entry1',
                'title': 'GitHub Account',
                'username': 'developer',
                'password': 'StrongPassword123!',
                'url': 'https://github.com',
                'notes': 'Development account with 2FA',
                'group': 'Development',
                'tags': ['development', 'git', 'important'],
                'date_created': last_week,
                'date_modified': yesterday,
                'custom_fields': {'API_Token': 'ghp_xxxxx'}
            },
            {
                'id': 'entry2',
                'title': 'GitLab Repository',
                'username': 'dev_user',
                'password': 'GitLabPass456',
                'url': 'https://gitlab.com',
                'notes': 'Secondary git hosting',
                'group': 'Development',
                'tags': ['development', 'git'],
                'date_created': last_week,
                'date_modified': now,
                'custom_fields': {}
            },
            {
                'id': 'entry3',
                'title': 'Bank Account',
                'username': 'customer123',
                'password': 'BankSecure789!',
                'url': 'https://bank.example.com',
                'notes': 'Personal banking',
                'group': 'Finance',
                'tags': ['banking', 'important'],
                'date_created': now,
                'date_modified': now,
                'custom_fields': {'Account_Number': '1234567890'}
            },
            {
                'id': 'entry4',
                'title': 'Email Account',
                'username': 'user@email.com',
                'password': 'weak',
                'url': '',
                'notes': '',
                'group': 'Personal',
                'tags': ['email'],
                'date_created': yesterday,
                'date_modified': yesterday,
                'custom_fields': {}
            },
            {
                'id': 'entry5',
                'title': 'Test Entry',
                'username': 'testuser',
                'password': '',  # Empty password
                'url': 'https://test.example.com',
                'notes': 'Test account for development',
                'group': 'Development',
                'tags': ['test'],
                'date_created': now,
                'date_modified': now,
                'custom_fields': {}
            }
        ]
    
    def test_basic_search_by_title(self, search_engine, sample_entries):
        """Test basic search by title."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="GitHub",
            search_fields=['title']
        )
        
        assert len(results) == 1
        assert results[0]['title'] == 'GitHub Account'
        assert results[0]['relevance_score'] > 0
    
    def test_search_multiple_fields(self, search_engine, sample_entries):
        """Test search across multiple fields."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="git",
            search_fields=['title', 'tags', 'notes']
        )
        
        # Should find GitHub and GitLab entries
        assert len(results) >= 2
        titles = [r['title'] for r in results]
        assert 'GitHub Account' in titles
        assert 'GitLab Repository' in titles
    
    def test_case_sensitive_search(self, search_engine, sample_entries):
        """Test case-sensitive search."""
        # Case insensitive (default)
        results_insensitive = search_engine.search_entries(
            entries=sample_entries,
            query="GITHUB",
            case_sensitive=False
        )
        assert len(results_insensitive) == 1
        
        # Case sensitive
        results_sensitive = search_engine.search_entries(
            entries=sample_entries,
            query="GITHUB",
            case_sensitive=True
        )
        assert len(results_sensitive) == 0  # No exact case match
    
    def test_exact_match_search(self, search_engine, sample_entries):
        """Test exact match search."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="GitHub Account",
            exact_match=True
        )
        
        assert len(results) == 1
        assert results[0]['title'] == 'GitHub Account'
    
    def test_regex_search(self, search_engine, sample_entries):
        """Test regex pattern search."""
        # Search for entries with "Git" followed by any characters
        results = search_engine.search_entries(
            entries=sample_entries,
            query=r"Git\w+",
            regex_search=True
        )
        
        assert len(results) >= 2  # GitHub and GitLab
    
    def test_tag_filter(self, search_engine, sample_entries):
        """Test filtering by tags."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            tags=['important']
        )
        
        assert len(results) == 2  # GitHub and Bank entries
        for result in results:
            assert 'important' in result['tags']
    
    def test_group_filter(self, search_engine, sample_entries):
        """Test filtering by group."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            group_filter="Development"
        )
        
        assert len(results) == 3  # GitHub, GitLab, and Test entries
        for result in results:
            assert result['group'] == 'Development'
    
    def test_date_filters(self, search_engine, sample_entries):
        """Test date-based filtering."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Find entries created after yesterday
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            date_created_after=yesterday
        )
        
        # Should find Bank and Test entries (created today)
        assert len(results) == 2
        for result in results:
            assert result['date_created'] > yesterday
    
    def test_content_filters(self, search_engine, sample_entries):
        """Test content-based filters."""
        # Find entries with URLs
        results_with_url = search_engine.search_entries(
            entries=sample_entries,
            query="",
            has_url=True
        )
        assert len(results_with_url) == 4  # All except Email
        
        # Find entries without URLs
        results_without_url = search_engine.search_entries(
            entries=sample_entries,
            query="",
            has_url=False
        )
        assert len(results_without_url) == 1  # Only Email
        
        # Find entries with notes
        results_with_notes = search_engine.search_entries(
            entries=sample_entries,
            query="",
            has_notes=True
        )
        assert len(results_with_notes) == 4  # All except Email
    
    def test_sort_by_relevance(self, search_engine, sample_entries):
        """Test sorting by relevance score."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="git",
            sort_by="relevance"
        )
        
        # Results should be sorted by relevance (highest first)
        if len(results) > 1:
            assert results[0]['relevance_score'] >= results[1]['relevance_score']
    
    def test_sort_by_title(self, search_engine, sample_entries):
        """Test sorting by title."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            sort_by="title"
        )
        
        # Results should be sorted alphabetically
        titles = [r['title'] for r in results]
        assert titles == sorted(titles, key=str.lower)
    
    def test_limit_results(self, search_engine, sample_entries):
        """Test limiting number of results."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            limit=2
        )
        
        assert len(results) == 2
    
    def test_search_by_url_exact_match(self, search_engine, sample_entries):
        """Test URL search with exact match."""
        results = search_engine.search_by_url(
            entries=sample_entries,
            url="https://github.com",
            fuzzy_match=False
        )
        
        assert len(results) == 1
        assert results[0]['url'] == 'https://github.com'
        assert results[0]['relevance_score'] == 10.0  # Exact match score
    
    def test_search_by_url_domain_match(self, search_engine, sample_entries):
        """Test URL search with domain matching."""
        results = search_engine.search_by_url(
            entries=sample_entries,
            url="https://github.com/user/repo",
            fuzzy_match=True
        )
        
        assert len(results) >= 1
        # Should find GitHub entry due to domain match
        github_entry = next((r for r in results if 'github' in r['url']), None)
        assert github_entry is not None
    
    def test_search_by_url_fuzzy_match(self, search_engine, sample_entries):
        """Test URL search with fuzzy matching."""
        results = search_engine.search_by_url(
            entries=sample_entries,
            url="github.com",
            fuzzy_match=True
        )
        
        assert len(results) >= 1
        # Should find GitHub entry
        github_entry = next((r for r in results if 'GitHub' in r['title']), None)
        assert github_entry is not None
    
    def test_search_similar_entries(self, search_engine, sample_entries):
        """Test finding similar entries."""
        # Use GitHub entry as reference
        github_entry = next(e for e in sample_entries if e['title'] == 'GitHub Account')
        
        results = search_engine.search_similar_entries(
            entries=sample_entries,
            reference_entry=github_entry,
            similarity_threshold=0.3
        )
        
        # Should find GitLab entry (similar tags and group)
        assert len(results) >= 1
        gitlab_entry = next((r for r in results if 'GitLab' in r['title']), None)
        assert gitlab_entry is not None
        assert gitlab_entry['similarity_score'] > 0.3
    
    def test_search_weak_passwords(self, search_engine, sample_entries):
        """Test finding entries with weak passwords."""
        results = search_engine.search_weak_passwords(
            entries=sample_entries,
            min_length=8,
            require_complexity=True
        )
        
        # Should find Email entry (password: "weak")
        assert len(results) >= 1
        weak_entry = next((r for r in results if r['password'] == 'weak'), None)
        assert weak_entry is not None
        assert 'weakness_reasons' in weak_entry
    
    def test_search_duplicates(self, search_engine):
        """Test finding duplicate entries."""
        # Create entries with duplicates
        entries_with_duplicates = [
            {
                'id': 'entry1',
                'title': 'GitHub',
                'username': 'user1',
                'url': 'https://github.com',
                'password': 'pass1'
            },
            {
                'id': 'entry2',
                'title': 'GitHub',  # Duplicate title
                'username': 'user1',  # Duplicate username
                'url': 'https://github.com',  # Duplicate URL
                'password': 'pass2'
            },
            {
                'id': 'entry3',
                'title': 'GitLab',
                'username': 'user2',
                'url': 'https://gitlab.com',
                'password': 'pass3'
            }
        ]
        
        results = search_engine.search_duplicates(
            entries=entries_with_duplicates,
            check_fields=['title', 'username', 'url']
        )
        
        assert len(results) == 1  # One group of duplicates
        assert len(results[0]) == 2  # Two entries in the duplicate group
    
    def test_get_search_suggestions(self, search_engine, sample_entries):
        """Test search suggestions."""
        suggestions = search_engine.get_search_suggestions(
            partial_query="git",
            entries=sample_entries,
            max_suggestions=5
        )
        
        assert len(suggestions) > 0
        # Should include titles and domains containing "git"
        assert any('git' in s.lower() for s in suggestions)
    
    def test_search_history(self, search_engine, sample_entries):
        """Test search history tracking."""
        # Perform some searches
        search_engine.search_entries(sample_entries, "github")
        search_engine.search_entries(sample_entries, "banking", tags=['important'])
        
        history = search_engine.get_search_history()
        
        assert len(history) == 2
        assert history[-1]['query'] == 'banking'  # Most recent first
        assert history[-1]['tags'] == ['important']
    
    def test_clear_search_history(self, search_engine, sample_entries):
        """Test clearing search history."""
        # Perform a search
        search_engine.search_entries(sample_entries, "test")
        
        # Verify history exists
        history = search_engine.get_search_history()
        assert len(history) == 1
        
        # Clear history
        search_engine.clear_search_history()
        
        # Verify history is empty
        history = search_engine.get_search_history()
        assert len(history) == 0
    
    def test_relevance_scoring(self, search_engine, sample_entries):
        """Test relevance score calculation."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="GitHub",
            search_fields=['title', 'username', 'notes']
        )
        
        assert len(results) > 0
        github_result = results[0]
        
        # Should have higher relevance for title match
        assert github_result['relevance_score'] > 0
        # Title matches should score higher than other field matches
        assert github_result['relevance_score'] >= 3.0  # Title weight is 3.0
    
    def test_url_relevance_calculation(self, search_engine):
        """Test URL relevance calculation method."""
        # Test exact URL match
        relevance = search_engine._calculate_url_relevance(
            entry_url="https://github.com",
            search_url="https://github.com",
            search_domain="github.com",
            fuzzy_match=True
        )
        assert relevance == 10.0  # Exact match
        
        # Test domain match
        relevance = search_engine._calculate_url_relevance(
            entry_url="https://github.com/user/repo",
            search_url="https://github.com",
            search_domain="github.com",
            fuzzy_match=True
        )
        assert relevance == 8.0  # Domain match
        
        # Test subdomain match
        relevance = search_engine._calculate_url_relevance(
            entry_url="https://api.github.com",
            search_url="https://github.com",
            search_domain="github.com",
            fuzzy_match=True
        )
        assert relevance == 6.0  # Subdomain match
    
    def test_entry_similarity_calculation(self, search_engine):
        """Test entry similarity calculation."""
        similarity = search_engine._calculate_entry_similarity(
            entry={
                'title': 'GitHub Repository',
                'url': 'https://github.com/user/repo',
                'username': 'developer',
                'tags': ['development', 'git']
            },
            ref_title='github account',
            ref_url='https://github.com',
            ref_username='developer',
            ref_tags={'development', 'git', 'important'}
        )
        
        # Should have high similarity due to:
        # - Similar titles (GitHub)
        # - Same domain
        # - Same username
        # - Common tags
        assert similarity > 0.5
    
    def test_keyboard_pattern_detection(self, search_engine):
        """Test keyboard pattern detection."""
        # Test with keyboard pattern
        assert search_engine._has_keyboard_pattern("qwerty123") is True
        assert search_engine._has_keyboard_pattern("123456789") is True
        assert search_engine._has_keyboard_pattern("asdfgh") is True
        
        # Test with non-pattern password
        assert search_engine._has_keyboard_pattern("RandomPassword123!") is False
    
    def test_invalid_regex_fallback(self, search_engine, sample_entries):
        """Test fallback to normal search when regex is invalid."""
        # Use invalid regex pattern
        results = search_engine.search_entries(
            entries=sample_entries,
            query="[invalid",  # Invalid regex
            regex_search=True
        )
        
        # Should still return results using normal search
        assert isinstance(results, list)
    
    def test_empty_query_handling(self, search_engine, sample_entries):
        """Test handling of empty search query."""
        results = search_engine.search_entries(
            entries=sample_entries,
            query="",
            limit=3
        )
        
        # Should return all entries (up to limit)
        assert len(results) == 3
        for result in results:
            assert result['relevance_score'] == 1.0  # Default score for empty query


class TestSearchEngineEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def search_engine(self):
        return SearchEngine()
    
    def test_empty_entries_list(self, search_engine):
        """Test search with empty entries list."""
        results = search_engine.search_entries(
            entries=[],
            query="test"
        )
        
        assert results == []
    
    def test_malformed_entries(self, search_engine):
        """Test search with malformed entries."""
        malformed_entries = [
            {'title': 'Valid Entry', 'username': 'user'},
            {'username': 'user2'},  # Missing title
            None,  # Invalid entry
            {'title': 123, 'username': 'user3'}  # Wrong type
        ]
        
        # Should handle gracefully and not crash
        results = search_engine.search_entries(
            entries=malformed_entries,
            query="Valid"
        )
        
        # Should find at least the valid entry
        assert len(results) >= 1
    
    def test_invalid_search_query(self, search_engine):
        """Test with invalid search query."""
        with pytest.raises(ValidationError):
            search_engine.search_entries(
                entries=[],
                query="SELECT * FROM entries; DROP TABLE users;--"  # SQL injection attempt
            )
    
    def test_very_long_query(self, search_engine):
        """Test with very long search query."""
        long_query = "a" * 300  # Exceeds 200 char limit
        
        with pytest.raises(ValidationError):
            search_engine.search_entries(
                entries=[],
                query=long_query
            )
    
    def test_unicode_handling(self, search_engine):
        """Test search with unicode characters."""
        unicode_entries = [
            {
                'id': 'entry1',
                'title': 'Café München',
                'username': 'müller',
                'url': 'https://café.example.com',
                'notes': '测试账户',
                'group': 'Personal',
                'tags': ['café', '中文'],
                'date_created': datetime.now(),
                'date_modified': datetime.now(),
                'custom_fields': {}
            }
        ]
        
        # Search for unicode text
        results = search_engine.search_entries(
            entries=unicode_entries,
            query="café"
        )
        
        assert len(results) == 1
        assert results[0]['title'] == 'Café München'


if __name__ == "__main__":
    pytest.main([__file__])
