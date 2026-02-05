"""
Template parser module.

Parses .github/pull_request_template.md to extract section headers
for dynamic PR description generation.
"""

import re
from pathlib import Path
from typing import List, Optional


# Default sections to use when no template is found
DEFAULT_SECTIONS = [
    "Why are you making this change?",
    "What are the possible impacts of your change to production?",
    "Is there anything else PR reviewers should know about?",
]


def read_pr_template(repo_path: str) -> Optional[str]:
    """
    Read PR template from .github directory.

    Checks multiple common locations:
    - .github/pull_request_template.md
    - .github/PULL_REQUEST_TEMPLATE.md
    - docs/pull_request_template.md

    Args:
        repo_path: Path to git repository root

    Returns:
        Template content or None if not found
    """
    repo = Path(repo_path)

    # Common template locations
    template_paths = [
        repo / ".github" / "pull_request_template.md",
        repo / ".github" / "PULL_REQUEST_TEMPLATE.md",
        repo / "docs" / "pull_request_template.md",
    ]

    for template_path in template_paths:
        if template_path.exists() and template_path.is_file():
            try:
                return template_path.read_text(encoding="utf-8")
            except Exception:
                # If we can't read this file, try the next one
                continue

    return None


def parse_template_sections(template_content: str) -> List[str]:
    """
    Extract section headers from markdown template.

    Looks for markdown headers (## or ###) and extracts the text.
    Preserves the order from the template.

    Args:
        template_content: Raw markdown content from template file

    Returns:
        List of section header strings (without markdown syntax)
    """
    if not template_content:
        return []

    sections = []

    # Match markdown headers (## or ###) at start of line
    # Pattern: ^#{2,3}\s+(.+)$
    pattern = r"^#{2,3}\s+(.+)$"

    for line in template_content.split('\n'):
        match = re.match(pattern, line.strip())
        if match:
            # Extract header text and clean it
            header_text = match.group(1).strip()
            if header_text:
                sections.append(header_text)

    return sections


def get_pr_template_sections(repo_path: str) -> List[str]:
    """
    Get PR template sections with fallback to defaults.

    Tries to read and parse the repository's PR template.
    Falls back to default sections if:
    - Template file doesn't exist
    - Template has no valid headers
    - Template parsing fails

    Args:
        repo_path: Path to git repository root

    Returns:
        List of section headers from template, or default sections
    """
    # Try to read template
    template_content = read_pr_template(repo_path)

    if template_content:
        # Parse sections from template
        sections = parse_template_sections(template_content)

        # Only use parsed sections if we found any
        if sections:
            return sections

    # Fallback to defaults
    return DEFAULT_SECTIONS.copy()
