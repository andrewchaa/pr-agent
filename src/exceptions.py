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
        super().__init__(
            "No changes detected. Please commit your changes before creating a PR."
        )


class BranchNameError(GitError):
    """Raised when branch name is invalid or missing ticket number."""
    pass


class GitHubError(PRAgentError):
    """Raised when GitHub CLI operations fail."""
    pass


class NotAuthenticatedError(GitHubError):
    """Raised when GitHub CLI is not authenticated."""

    def __init__(self):
        super().__init__(
            "GitHub CLI not authenticated. Please run: gh auth login"
        )


class LLMError(PRAgentError):
    """Raised when LLM operations fail."""
    pass


class OllamaNotAvailableError(LLMError):
    """Raised when Ollama service is not available."""

    def __init__(self, url: str = "http://localhost:11434"):
        super().__init__(
            f"Ollama service not available at {url}. "
            "Please start it with: ollama serve"
        )


class ModelNotFoundError(LLMError):
    """Raised when the specified model is not available."""

    def __init__(self, model: str):
        super().__init__(
            f"Model '{model}' not found. Please pull it with: ollama pull {model}"
        )


class ConfigError(PRAgentError):
    """Raised when configuration is invalid."""
    pass
