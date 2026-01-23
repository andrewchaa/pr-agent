"""
Git operations module.

Handles all git-related operations including branch name extraction,
ticket number parsing, diff retrieval, and repository validation.
"""

import re
from pathlib import Path
from typing import Optional, List

import git
from git.exc import InvalidGitRepositoryError

from pr_agent.exceptions import NotInGitRepoError, NoChangesError, BranchNameError


class GitOperations:
    """Handles git operations for PR creation."""

    def __init__(self, repo_path: Optional[Path] = None):
        """
        Initialize GitOperations.

        Args:
            repo_path: Path to git repository. Defaults to current directory.

        Raises:
            NotInGitRepoError: If the path is not a git repository.
        """
        try:
            self.repo = git.Repo(repo_path or Path.cwd(), search_parent_directories=True)
        except InvalidGitRepositoryError:
            raise NotInGitRepoError()

    def validate_git_repo(self) -> bool:
        """
        Validate that we're in a git repository.

        Returns:
            True if in a valid git repository.

        Raises:
            NotInGitRepoError: If not in a git repository.
        """
        if self.repo.bare:
            raise NotInGitRepoError()
        return True

    def get_current_branch(self) -> str:
        """
        Get the name of the current branch.

        Returns:
            Current branch name.

        Raises:
            GitError: If unable to determine current branch.
        """
        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            raise BranchNameError("Detached HEAD state. Please checkout a branch.")

    def extract_ticket_number(self, branch_name: Optional[str] = None,
                             pattern: str = r"STAR-(\d+)") -> Optional[str]:
        """
        Extract ticket number from branch name using regex pattern.

        Args:
            branch_name: Branch name to parse. If None, uses current branch.
            pattern: Regex pattern to extract ticket number. Default: "STAR-(\\d+)"

        Returns:
            Ticket number (e.g., "STAR-12345") or None if not found.

        Examples:
            >>> git_ops.extract_ticket_number("feature/STAR-12345-add-feature")
            "STAR-12345"
            >>> git_ops.extract_ticket_number("STAR-999-bugfix")
            "STAR-999"
            >>> git_ops.extract_ticket_number("feature-no-ticket")
            None
        """
        if branch_name is None:
            branch_name = self.get_current_branch()

        match = re.search(pattern, branch_name, re.IGNORECASE)
        if match:
            # Return the full match in uppercase (e.g., "STAR-12345")
            return match.group(0).upper()
        return None

    def get_diff(self, base_branch: str = "main") -> str:
        """
        Get unified diff against base branch.

        Args:
            base_branch: Branch to diff against. Default: "main"

        Returns:
            Unified diff string.

        Raises:
            NoChangesError: If there are no changes.
        """
        try:
            # Get diff between base branch and current HEAD
            diff = self.repo.git.diff(f"{base_branch}...HEAD")

            if not diff.strip():
                raise NoChangesError()

            return diff
        except git.exc.GitCommandError as e:
            if "unknown revision" in str(e).lower():
                raise BranchNameError(
                    f"Base branch '{base_branch}' not found. "
                    "Please specify a valid base branch."
                )
            raise

    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """
        Get list of files changed compared to base branch.

        Args:
            base_branch: Branch to compare against. Default: "main"

        Returns:
            List of file paths that have been modified.
        """
        try:
            # Get list of changed files
            changed = self.repo.git.diff(
                f"{base_branch}...HEAD",
                name_only=True
            ).strip().split('\n')

            # Filter out empty strings
            return [f for f in changed if f]
        except git.exc.GitCommandError:
            return []

    def get_commit_messages(self, base_branch: str = "main") -> List[str]:
        """
        Get commit messages from current branch compared to base.

        Args:
            base_branch: Branch to compare against. Default: "main"

        Returns:
            List of commit messages.
        """
        try:
            log = self.repo.git.log(
                f"{base_branch}..HEAD",
                pretty="format:%s"
            ).strip()

            if not log:
                return []

            return log.split('\n')
        except git.exc.GitCommandError:
            return []

    def has_uncommitted_changes(self) -> bool:
        """
        Check if there are uncommitted changes.

        Returns:
            True if there are uncommitted changes.
        """
        return self.repo.is_dirty()

    def get_repository_root(self) -> Path:
        """
        Get the root directory of the git repository.

        Returns:
            Path to repository root.
        """
        return Path(self.repo.working_dir)
