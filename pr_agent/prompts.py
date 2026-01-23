"""
LLM prompt templates for PR generation.

Provides engineered prompts for generating high-quality PR descriptions
with focus on clarity, completeness, and reviewer value.
"""

from typing import List


class PRPrompts:
    """Collection of prompts for PR description generation."""

    SYSTEM_PROMPT = """You are a helpful assistant that writes clear, concise, and informative
pull request descriptions. You analyze code changes and explain them in a way that helps
code reviewers understand the purpose, impact, and context of the changes."""

    @staticmethod
    def generate_title_prompt(ticket_number: str, branch_name: str, user_intent: str) -> str:
        """
        Generate prompt for PR title creation.

        Args:
            ticket_number: Ticket identifier (e.g., "STAR-12345")
            branch_name: Current branch name
            user_intent: User's description of the change

        Returns:
            Prompt for title generation.
        """
        return f"""Generate a concise PR title following this format: "{ticket_number}: <description>"

Branch name: {branch_name}
Change purpose: {user_intent}

Requirements:
- Start with the ticket number: {ticket_number}
- Follow with a colon and space
- Write a clear, actionable description (3-8 words)
- Use imperative mood (e.g., "Add", "Fix", "Update", not "Added", "Fixed", "Updated")
- Be specific but concise

Examples:
- STAR-123: Add user authentication flow
- STAR-456: Fix memory leak in data processor
- STAR-789: Update API error handling

Generate only the title, nothing else."""

    @staticmethod
    def generate_why_prompt(user_intent: str, changed_files: List[str]) -> str:
        """
        Generate prompt for "Why are you making this change?" section.

        Args:
            user_intent: User's description of the change purpose
            changed_files: List of modified files

        Returns:
            Prompt for why section.
        """
        files_str = "\n".join(f"- {f}" for f in changed_files[:10])  # Limit to 10 files
        if len(changed_files) > 10:
            files_str += f"\n... and {len(changed_files) - 10} more files"

        return f"""Based on the following information, explain why this change is being made.

User's stated purpose: {user_intent}

Files modified:
{files_str}

Write a clear, concise explanation (2-4 sentences) that answers:
1. What problem does this solve or what feature does it add?
2. Why is this change necessary or valuable?

Be specific and focus on the business or technical value. Avoid repeating obvious information
from the code changes. Write from a developer's perspective explaining to reviewers."""

    @staticmethod
    def generate_impact_prompt(changed_files: List[str], commit_messages: List[str]) -> str:
        """
        Generate prompt for "What are the possible impacts?" section.

        Args:
            changed_files: List of modified files
            commit_messages: List of commit messages

        Returns:
            Prompt for impact section.
        """
        files_str = "\n".join(f"- {f}" for f in changed_files[:15])
        if len(changed_files) > 15:
            files_str += f"\n... and {len(changed_files) - 15} more files"

        commits_str = ""
        if commit_messages:
            commits_str = "Commits:\n" + "\n".join(f"- {msg}" for msg in commit_messages[:5])

        return f"""Analyze the potential production impacts of this change.

Files modified:
{files_str}

{commits_str}

Consider and briefly describe:
1. What parts of the system could be affected?
2. Are there any performance, security, or data implications?
3. What should QA or reviewers test specifically?
4. Any backwards compatibility concerns?

Be practical and focus on real risks, not theoretical ones. If the change is low-risk,
it's fine to say so. Write 2-5 concise bullet points."""

    @staticmethod
    def generate_notes_prompt(changed_files: List[str], diff_summary: str) -> str:
        """
        Generate prompt for "Anything else reviewers should know?" section.

        Args:
            changed_files: List of modified files
            diff_summary: Summary or excerpt of the diff

        Returns:
            Prompt for notes section.
        """
        files_str = "\n".join(f"- {f}" for f in changed_files[:10])

        return f"""Based on this change, identify anything important that code reviewers should know.

Files modified:
{files_str}

Change summary:
{diff_summary}

Consider mentioning (if applicable):
- Dependencies on other PRs or changes
- Configuration changes needed
- Database migrations or data changes
- New dependencies or libraries introduced
- Areas that need special attention during review
- Known limitations or follow-up work planned
- Any assumptions or design decisions made

If there's nothing notable, respond with "No additional notes."
Otherwise, provide 1-4 concise bullet points."""

    @staticmethod
    def extract_diff_summary(diff: str, max_length: int = 1000) -> str:
        """
        Extract a meaningful summary from a git diff.

        Args:
            diff: Full git diff
            max_length: Maximum characters to include

        Returns:
            Summarized diff focusing on changed files and additions.
        """
        lines = diff.split('\n')
        summary_lines = []
        char_count = 0

        for line in lines:
            # Include file headers and some context
            if line.startswith('diff --git') or line.startswith('+++') or \
               line.startswith('---') or line.startswith('@@'):
                summary_lines.append(line)
                char_count += len(line)
            # Include added/removed lines sparingly
            elif line.startswith('+') or line.startswith('-'):
                if char_count < max_length * 0.7:  # Reserve space for headers
                    summary_lines.append(line)
                    char_count += len(line)

            if char_count >= max_length:
                summary_lines.append("... (diff truncated)")
                break

        return '\n'.join(summary_lines)
