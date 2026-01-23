"""
PR generation logic module.

Coordinates LLM calls to generate comprehensive PR titles and descriptions
using git information and user input.
"""

from typing import List, Optional, Dict

from pr_agent.llm_client import OllamaClient
from pr_agent.prompts import PRPrompts
from pr_agent.git_operations import GitOperations


class PRGenerator:
    """Generates PR titles and descriptions using LLM."""

    def __init__(
        self,
        llm_client: OllamaClient,
        git_ops: GitOperations,
        model: str = "qwen2.5:3b",
        max_diff_tokens: int = 8000,
    ):
        """
        Initialize PR generator.

        Args:
            llm_client: Ollama client for LLM interactions
            git_ops: Git operations handler
            model: Model name to use for generation
            max_diff_tokens: Maximum characters for diff context
        """
        self.llm_client = llm_client
        self.git_ops = git_ops
        self.model = model
        self.max_diff_tokens = max_diff_tokens
        self.prompts = PRPrompts()

    def generate_title(
        self,
        ticket_number: str,
        branch_name: str,
        user_intent: str,
    ) -> str:
        """
        Generate PR title.

        Args:
            ticket_number: Ticket identifier (e.g., "STAR-12345")
            branch_name: Current branch name
            user_intent: User's description of the change purpose

        Returns:
            Generated PR title in format: "STAR-XXX: Description"
        """
        prompt = self.prompts.generate_title_prompt(
            ticket_number, branch_name, user_intent
        )

        title = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system=self.prompts.SYSTEM_PROMPT,
            temperature=0.5,  # Lower temperature for more consistent titles
        )

        # Ensure title starts with ticket number
        if not title.startswith(ticket_number):
            # Extract description from generated title if it doesn't have ticket
            if ":" in title:
                description = title.split(":", 1)[1].strip()
            else:
                description = title.strip()
            title = f"{ticket_number}: {description}"

        return title.strip()

    def generate_why_section(
        self,
        user_intent: str,
        changed_files: List[str],
        diff: Optional[str] = None,
    ) -> str:
        """
        Generate "Why are you making this change?" section.

        Args:
            user_intent: User's description of change purpose
            changed_files: List of modified files
            diff: Optional git diff for additional context

        Returns:
            Generated explanation text.
        """
        prompt = self.prompts.generate_why_prompt(user_intent, changed_files)

        # Add diff context if available and not too large
        if diff and len(diff) < self.max_diff_tokens:
            diff_summary = self.prompts.extract_diff_summary(diff, 1500)
            prompt += f"\n\nCode changes (summary):\n{diff_summary}"

        response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system=self.prompts.SYSTEM_PROMPT,
            temperature=0.7,
        )

        return response.strip()

    def generate_impact_section(
        self,
        changed_files: List[str],
        commit_messages: List[str],
        diff: Optional[str] = None,
    ) -> str:
        """
        Generate "What are the possible impacts?" section.

        Args:
            changed_files: List of modified files
            commit_messages: List of commit messages
            diff: Optional git diff for additional context

        Returns:
            Generated impact analysis text.
        """
        prompt = self.prompts.generate_impact_prompt(changed_files, commit_messages)

        # Add limited diff context
        if diff:
            diff_summary = self.prompts.extract_diff_summary(diff, 1000)
            prompt += f"\n\nCode changes (summary):\n{diff_summary}"

        response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system=self.prompts.SYSTEM_PROMPT,
            temperature=0.7,
        )

        return response.strip()

    def generate_notes_section(
        self,
        changed_files: List[str],
        diff: Optional[str] = None,
    ) -> str:
        """
        Generate "Anything else reviewers should know?" section.

        Args:
            changed_files: List of modified files
            diff: Optional git diff for additional context

        Returns:
            Generated notes text.
        """
        diff_summary = ""
        if diff:
            diff_summary = self.prompts.extract_diff_summary(diff, 1000)

        prompt = self.prompts.generate_notes_prompt(changed_files, diff_summary)

        response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system=self.prompts.SYSTEM_PROMPT,
            temperature=0.7,
        )

        return response.strip()

    def generate_description(
        self,
        user_intent: str,
        base_branch: str = "main",
        template_sections: Optional[List[str]] = None,
    ) -> str:
        """
        Generate complete PR description.

        Args:
            user_intent: User's description of change purpose
            base_branch: Base branch for diff comparison
            template_sections: Custom template sections (uses defaults if None)

        Returns:
            Formatted PR description with all sections.
        """
        # Get git information
        changed_files = self.git_ops.get_changed_files(base_branch)
        commit_messages = self.git_ops.get_commit_messages(base_branch)
        diff = self.git_ops.get_diff(base_branch)

        # Truncate diff if too large
        if len(diff) > self.max_diff_tokens:
            diff = diff[:self.max_diff_tokens] + "\n\n... (diff truncated)"

        # Use default sections if not provided
        if template_sections is None:
            template_sections = [
                "Why are you making this change?",
                "What are the possible impacts of your change to production?",
                "Is there anything else PR reviewers should know about?",
            ]

        # Generate each section
        sections: Dict[str, str] = {}

        # Section 1: Why
        sections["why"] = self.generate_why_section(
            user_intent, changed_files, diff
        )

        # Section 2: Impact
        sections["impact"] = self.generate_impact_section(
            changed_files, commit_messages, diff
        )

        # Section 3: Notes
        sections["notes"] = self.generate_notes_section(
            changed_files, diff
        )

        # Format into final description
        return self.format_pr_body(sections, template_sections)

    def format_pr_body(
        self,
        sections: Dict[str, str],
        template_sections: List[str],
    ) -> str:
        """
        Format sections into final PR body template.

        Args:
            sections: Generated content for each section
            template_sections: Section headers

        Returns:
            Formatted PR description.
        """
        body_parts = []

        # Section 1: Why
        if len(template_sections) > 0:
            body_parts.append(f"## {template_sections[0]}")
            body_parts.append(sections.get("why", ""))
            body_parts.append("")

        # Section 2: Impact
        if len(template_sections) > 1:
            body_parts.append(f"## {template_sections[1]}")
            body_parts.append(sections.get("impact", ""))
            body_parts.append("")

        # Section 3: Notes
        if len(template_sections) > 2:
            body_parts.append(f"## {template_sections[2]}")
            notes = sections.get("notes", "")
            if notes and notes.lower() != "no additional notes.":
                body_parts.append(notes)
            else:
                body_parts.append("No additional notes.")
            body_parts.append("")

        return "\n".join(body_parts).strip()
