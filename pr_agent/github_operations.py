"""
GitHub CLI operations module.

Provides wrapper around GitHub CLI for authentication checks
and PR creation.
"""

import json
import subprocess
from typing import Optional, Dict, Any

from pr_agent.exceptions import NotAuthenticatedError, GitHubError


class GitHubOperations:
    """Handles GitHub CLI operations."""

    def __init__(self):
        """Initialize GitHub operations handler."""
        self.gh_cmd = "gh"

    def check_gh_installed(self) -> bool:
        """
        Check if GitHub CLI is installed.

        Returns:
            True if gh is installed.

        Raises:
            GitHubError: If gh is not installed.
        """
        try:
            result = subprocess.run(
                [self.gh_cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            raise GitHubError(
                "GitHub CLI (gh) not found. Please install it from: "
                "https://cli.github.com/"
            )
        except subprocess.TimeoutExpired:
            raise GitHubError("GitHub CLI check timed out")

    def check_gh_auth(self) -> bool:
        """
        Check if GitHub CLI is authenticated.

        Returns:
            True if authenticated.

        Raises:
            NotAuthenticatedError: If not authenticated.
            GitHubError: If gh is not installed or check fails.
        """
        self.check_gh_installed()

        try:
            result = subprocess.run(
                [self.gh_cmd, "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise NotAuthenticatedError()

            return True

        except subprocess.TimeoutExpired:
            raise GitHubError("GitHub authentication check timed out")

    def get_repo_info(self) -> Dict[str, str]:
        """
        Get current repository information.

        Returns:
            Dictionary with 'owner' and 'name' keys.

        Raises:
            GitHubError: If unable to get repository info.
        """
        try:
            result = subprocess.run(
                [self.gh_cmd, "repo", "view", "--json", "owner,name"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise GitHubError(
                    f"Failed to get repository info: {result.stderr.strip()}"
                )

            data = json.loads(result.stdout)
            return {
                "owner": data.get("owner", {}).get("login", ""),
                "name": data.get("name", ""),
            }

        except subprocess.TimeoutExpired:
            raise GitHubError("Repository info check timed out")
        except json.JSONDecodeError as e:
            raise GitHubError(f"Failed to parse repository info: {e}")

    def create_pull_request(
        self,
        title: str,
        body: str,
        base: str = "main",
        draft: bool = False,
        web: bool = False,
    ) -> str:
        """
        Create a pull request using GitHub CLI.

        Args:
            title: PR title
            body: PR description/body
            base: Base branch for the PR. Default: "main"
            draft: Create as draft PR. Default: False
            web: Open PR in browser after creation. Default: False

        Returns:
            PR URL.

        Raises:
            GitHubError: If PR creation fails.
        """
        # Build command
        cmd = [
            self.gh_cmd, "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base,
        ]

        if draft:
            cmd.append("--draft")

        if web:
            cmd.append("--web")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise GitHubError(f"Failed to create PR: {error_msg}")

            # Extract PR URL from output
            pr_url = result.stdout.strip()

            # gh pr create returns the URL on the last line
            if "\n" in pr_url:
                pr_url = pr_url.split("\n")[-1].strip()

            return pr_url

        except subprocess.TimeoutExpired:
            raise GitHubError("PR creation timed out")

    def check_remote_branch_exists(self, branch: str) -> bool:
        """
        Check if a branch exists on the remote.

        Args:
            branch: Branch name to check

        Returns:
            True if branch exists on remote.
        """
        try:
            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin", branch],
                capture_output=True,
                text=True,
                timeout=10
            )

            return bool(result.stdout.strip())

        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def push_current_branch(self, set_upstream: bool = True) -> bool:
        """
        Push current branch to remote.

        Args:
            set_upstream: Set upstream tracking. Default: True

        Returns:
            True if push successful.

        Raises:
            GitHubError: If push fails.
        """
        cmd = ["git", "push"]

        if set_upstream:
            cmd.extend(["-u", "origin", "HEAD"])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                raise GitHubError(f"Failed to push branch: {result.stderr.strip()}")

            return True

        except subprocess.TimeoutExpired:
            raise GitHubError("Push operation timed out")
