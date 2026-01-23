"""Tests for PR generator module."""

import pytest
from unittest.mock import Mock
from pr_agent.pr_generator import PRGenerator
from pr_agent.prompts import PRPrompts


class TestPRGenerator:
    """Test PR generation functionality."""

    def test_format_pr_body(self):
        """Test PR body formatting."""
        mock_llm = Mock()
        mock_git = Mock()

        generator = PRGenerator(mock_llm, mock_git)

        sections = {
            "why": "This change adds authentication.",
            "impact": "May affect login flow.",
            "notes": "No additional notes."
        }

        template_sections = [
            "Why are you making this change?",
            "What are the possible impacts?",
            "Anything else?"
        ]

        body = generator.format_pr_body(sections, template_sections)

        assert "## Why are you making this change?" in body
        assert "This change adds authentication." in body
        assert "## What are the possible impacts?" in body


class TestPRPrompts:
    """Test prompt generation."""

    def test_extract_diff_summary(self):
        """Test diff summary extraction."""
        diff = """diff --git a/file.py b/file.py
+++ b/file.py
@@ -1,5 +1,5 @@
+new line
-old line
"""

        summary = PRPrompts.extract_diff_summary(diff, max_length=500)

        assert "diff --git" in summary
        assert "+new line" in summary
