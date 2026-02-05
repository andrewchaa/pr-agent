"""Tests for template parser module."""

import pytest
from src.template_parser import (
    read_pr_template,
    parse_template_sections,
    get_pr_template_sections,
    DEFAULT_SECTIONS,
)


class TestReadPRTemplate:
    """Test reading PR template files."""

    def test_read_existing_template(self, tmp_path):
        """Test reading an existing template file."""
        # Create a test template
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template_file = github_dir / "pull_request_template.md"
        template_content = "## Why?\n\n## What?\n"
        template_file.write_text(template_content)

        result = read_pr_template(str(tmp_path))

        assert result == template_content

    def test_read_uppercase_template(self, tmp_path):
        """Test reading template with uppercase filename."""
        # Create template with uppercase filename
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template_file = github_dir / "PULL_REQUEST_TEMPLATE.md"
        template_content = "## Section 1\n"
        template_file.write_text(template_content)

        result = read_pr_template(str(tmp_path))

        assert result == template_content

    def test_read_docs_location(self, tmp_path):
        """Test reading template from docs directory."""
        # Create template in docs/
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        template_file = docs_dir / "pull_request_template.md"
        template_content = "## Documentation\n"
        template_file.write_text(template_content)

        result = read_pr_template(str(tmp_path))

        assert result == template_content

    def test_read_nonexistent_template(self, tmp_path):
        """Test reading when no template exists."""
        result = read_pr_template(str(tmp_path))

        assert result is None

    def test_priority_order(self, tmp_path):
        """Test that .github/pull_request_template.md has priority."""
        # Create multiple templates
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Lower priority template
        (docs_dir / "pull_request_template.md").write_text("## Docs")

        # Higher priority template
        priority_content = "## GitHub"
        (github_dir / "pull_request_template.md").write_text(priority_content)

        result = read_pr_template(str(tmp_path))

        assert result == priority_content


class TestParseTemplateSections:
    """Test parsing template sections."""

    def test_parse_h2_headers(self):
        """Test parsing ## headers."""
        template = """
## Why are you making this change?

Some description here.

## What is the impact?

More text.
"""
        sections = parse_template_sections(template)

        assert len(sections) == 2
        assert sections[0] == "Why are you making this change?"
        assert sections[1] == "What is the impact?"

    def test_parse_h3_headers(self):
        """Test parsing ### headers."""
        template = """
### First Section

Content here.

### Second Section

More content.
"""
        sections = parse_template_sections(template)

        assert len(sections) == 2
        assert sections[0] == "First Section"
        assert sections[1] == "Second Section"

    def test_parse_mixed_headers(self):
        """Test parsing mixed ## and ### headers."""
        template = """
## Main Section

Content.

### Subsection

More content.

## Another Main Section

Final content.
"""
        sections = parse_template_sections(template)

        assert len(sections) == 3
        assert sections[0] == "Main Section"
        assert sections[1] == "Subsection"
        assert sections[2] == "Another Main Section"

    def test_parse_empty_template(self):
        """Test parsing empty template."""
        sections = parse_template_sections("")

        assert sections == []

    def test_parse_no_headers(self):
        """Test parsing template with no headers."""
        template = "Just some text without headers."
        sections = parse_template_sections(template)

        assert sections == []

    def test_parse_ignores_h1(self):
        """Test that # headers are ignored."""
        template = """
# Title (ignored)

## Section 1

Content.
"""
        sections = parse_template_sections(template)

        assert len(sections) == 1
        assert sections[0] == "Section 1"

    def test_parse_strips_whitespace(self):
        """Test that whitespace is stripped from headers."""
        template = """
##   Lots of spaces

### Tabs and spaces

"""
        sections = parse_template_sections(template)

        assert sections[0] == "Lots of spaces"
        assert sections[1] == "Tabs and spaces"

    def test_parse_preserves_order(self):
        """Test that section order is preserved."""
        template = """
## Third by importance

## First alphabetically

## Second numerically
"""
        sections = parse_template_sections(template)

        assert sections[0] == "Third by importance"
        assert sections[1] == "First alphabetically"
        assert sections[2] == "Second numerically"


class TestGetPRTemplateSections:
    """Test getting PR template sections with fallback."""

    def test_get_sections_with_template(self, tmp_path):
        """Test getting sections when template exists."""
        # Create template
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template_file = github_dir / "pull_request_template.md"
        template_file.write_text("""
## Custom Section 1

## Custom Section 2

## Custom Section 3
""")

        sections = get_pr_template_sections(str(tmp_path))

        assert len(sections) == 3
        assert sections[0] == "Custom Section 1"
        assert sections[1] == "Custom Section 2"
        assert sections[2] == "Custom Section 3"

    def test_get_sections_without_template(self, tmp_path):
        """Test fallback to defaults when no template exists."""
        sections = get_pr_template_sections(str(tmp_path))

        assert sections == DEFAULT_SECTIONS

    def test_get_sections_with_empty_template(self, tmp_path):
        """Test fallback when template has no headers."""
        # Create empty template
        github_dir = tmp_path / ".github"
        github_dir.mkdir()
        template_file = github_dir / "pull_request_template.md"
        template_file.write_text("Just text, no headers.")

        sections = get_pr_template_sections(str(tmp_path))

        # Should fall back to defaults
        assert sections == DEFAULT_SECTIONS

    def test_get_sections_returns_copy(self, tmp_path):
        """Test that modifying returned list doesn't affect defaults."""
        sections1 = get_pr_template_sections(str(tmp_path))
        sections2 = get_pr_template_sections(str(tmp_path))

        sections1.append("Modified")

        # Should not affect second call
        assert len(sections2) == len(DEFAULT_SECTIONS)
        assert "Modified" not in sections2
