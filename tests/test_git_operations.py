"""Tests for git operations module."""

import pytest
from src.git_operations import GitOperations
from src.exceptions import NotInGitRepoError


class TestTicketExtraction:
    """Test ticket number extraction from branch names."""

    def test_extract_ticket_standard_format(self):
        """Test extraction with standard format."""
        git_ops = GitOperations()

        # Test with various branch name formats
        assert git_ops.extract_ticket_number("feature/STAR-12345-add-feature", r"STAR-(\d+)") == "STAR-12345"
        assert git_ops.extract_ticket_number("STAR-999-bugfix", r"STAR-(\d+)") == "STAR-999"
        assert git_ops.extract_ticket_number("bugfix/STAR-456-fix-leak", r"STAR-(\d+)") == "STAR-456"

    def test_extract_ticket_no_match(self):
        """Test extraction when no ticket found."""
        git_ops = GitOperations()

        assert git_ops.extract_ticket_number("feature-no-ticket", r"STAR-(\d+)") is None
        assert git_ops.extract_ticket_number("main", r"STAR-(\d+)") is None

    def test_extract_ticket_lowercase(self):
        """Test extraction with lowercase ticket in branch name."""
        git_ops = GitOperations()

        # Lowercase variants should work and return uppercase
        assert git_ops.extract_ticket_number("star-422270-test", r"STAR-(\d+)") == "STAR-422270"
        assert git_ops.extract_ticket_number("feature/star-12345-add-feature", r"STAR-(\d+)") == "STAR-12345"
        assert git_ops.extract_ticket_number("Star-999-bugfix", r"STAR-(\d+)") == "STAR-999"

    def test_extract_ticket_custom_pattern(self):
        """Test extraction with custom pattern."""
        git_ops = GitOperations()

        # JIRA-style
        assert git_ops.extract_ticket_number("feature/JIRA-123", r"JIRA-(\d+)") == "JIRA-123"
        assert git_ops.extract_ticket_number("feature/jira-123", r"JIRA-(\d+)") == "JIRA-123"

        # Linear-style
        assert git_ops.extract_ticket_number("ENG-456-feature", r"ENG-(\d+)") == "ENG-456"
        assert git_ops.extract_ticket_number("eng-456-feature", r"ENG-(\d+)") == "ENG-456"
