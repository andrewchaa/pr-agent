"""
Custom exceptions for pr-agent.

Provides specific exception types for different error conditions
with helpful error messages and suggestions.
"""


class PRAgentError(Exception):
    """Base exception for all pr-agent errors."""

    pass


class GitError(PRAgentError):
    """Raised when git operations fail."""

    pass


class NotInGitRepoError(GitError):
    """Raised when not in a git repository."""

    def __init__(self):
        super().__init__(
            "Not in a git repository. Please run this command from within a git repository."
        )


class NoChangesError(GitError):
    """Raised when there are no git changes to commit."""

    def __init__(self):
        super().__init__("No changes detected. Please commit your changes before creating a PR.")


class BranchNameError(GitError):
    """Raised when branch name is invalid or missing ticket number."""

    pass


class GitHubError(PRAgentError):
    """Raised when GitHub CLI operations fail."""

    pass


class NotAuthenticatedError(GitHubError):
    """Raised when GitHub CLI is not authenticated."""

    def __init__(self):
        super().__init__("GitHub CLI not authenticated. Please run: gh auth login")


class LLMError(PRAgentError):
    """Raised when LLM operations fail."""

    pass


class CopilotAuthError(LLMError):
    """Raised when GitHub Copilot authentication fails."""

    def __init__(self, message: str = ""):
        default_msg = (
            "GitHub Copilot authentication failed. "
            "Please ensure your GitHub token has Copilot access. "
            "Set GITHUB_TOKEN or PR_AGENT_COPILOT_KEY environment variable."
        )
        super().__init__(message or default_msg)


class CopilotConfigError(LLMError):
    """Raised when Copilot configuration is invalid."""

    def __init__(self, message: str = ""):
        default_msg = (
            "Copilot configuration error. "
            "Please verify copilot_api_base and copilot_api_key settings."
        )
        super().__init__(message or default_msg)


class ConfigError(PRAgentError):
    """Raised when configuration is invalid."""

    pass
