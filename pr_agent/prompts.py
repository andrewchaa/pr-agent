"""
LLM prompt templates for PR generation.

Provides engineered prompts for generating high-quality PR descriptions
with focus on clarity, completeness, and reviewer value.
"""

from typing import List


class PRPrompts:
    """Collection of prompts for PR description generation."""

    SYSTEM_PROMPT = """You are a helpful assistant that writes clear, concise pull request descriptions.
Be direct and brief. Avoid headers, numbered sections, or verbose explanations.
Focus on practical information that helps reviewers understand the change quickly."""

    @staticmethod
    def extract_ticket_number_prompt(branch_name: str, ticket_prefix: str = "STAR") -> str:
        """
        Generate prompt for extracting ticket number from branch name using LLM.

        Args:
            branch_name: Branch name to extract ticket from
            ticket_prefix: Expected ticket prefix (e.g., "STAR", "JIRA", "ENG")

        Returns:
            Prompt for ticket extraction.
        """
        return f"""Extract the ticket number from this git branch name: "{branch_name}"

The ticket number typically starts with "{ticket_prefix}" followed by a dash and numbers.
Common formats include:
- {ticket_prefix}-12345
- {ticket_prefix.lower()}-12345
- {ticket_prefix.upper()}-12345

Branch name variations:
- feature/{ticket_prefix}-123-description
- {ticket_prefix}-123-some-feature
- bugfix-{ticket_prefix.lower()}-456-fix
- {ticket_prefix.lower()}_789_something
- and many other creative formats

Instructions:
1. Look for the ticket identifier in the branch name
2. Return ONLY the ticket number in the format: {ticket_prefix.upper()}-[number]
3. If you find the ticket, return just the ticket like: {ticket_prefix.upper()}-12345
4. If no ticket number is found, return exactly: NONE

Examples:
- "star-422270-test" → STAR-422270
- "feature/STAR-12345-add-auth" → STAR-12345
- "bugfix_star_999_memory_leak" → STAR-999
- "some-branch-without-ticket" → NONE

Now extract from: "{branch_name}"

Return ONLY the ticket number or NONE, nothing else."""

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

        return f"""Explain why this change is being made in 2-3 sentences.

User's purpose: {user_intent}
Files modified: {files_str}

Focus on: What problem this solves and why it's needed.
Be direct and concise. No headers, bullet points, or extra formatting."""

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

        return f"""List the potential production impacts of this change.

Files modified:
{files_str}

{commits_str}

Provide 2-4 brief bullet points covering real risks (performance, security, compatibility, areas to test).
If low-risk, say so. Be practical, not theoretical.
NO headers, numbered lists, or summary sections - just simple bullet points."""

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

        return f"""List anything important for reviewers (dependencies, config changes, migrations, special review areas).

Files modified:
{files_str}

Change summary:
{diff_summary}

If nothing notable: "No additional notes."
Otherwise: 1-3 brief bullet points. No headers or extra formatting."""

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
