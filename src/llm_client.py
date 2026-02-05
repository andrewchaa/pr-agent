"""
Ollama LLM client module.

Provides interface to interact with local Ollama service for text generation.
"""

import json
from typing import Optional, Dict, Any

import requests
from requests.exceptions import ConnectionError, Timeout

from src.exceptions import OllamaNotAvailableError, ModelNotFoundError, LLMError


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120):
        """
        Initialize Ollama client.

        Args:
            base_url: Base URL for Ollama API. Default: "http://localhost:11434"
            timeout: Request timeout in seconds. Default: 120
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.generate_url = f"{self.base_url}/api/generate"
        self.tags_url = f"{self.base_url}/api/tags"

    def check_availability(self) -> bool:
        """
        Check if Ollama service is running and available.

        Returns:
            True if service is available.

        Raises:
            OllamaNotAvailableError: If service is not reachable.
        """
        try:
            response = requests.get(self.base_url, timeout=5)
            return response.status_code == 200
        except (ConnectionError, Timeout):
            raise OllamaNotAvailableError(self.base_url)

    def check_model_exists(self, model: str) -> bool:
        """
        Check if the specified model is available locally.

        Args:
            model: Model name to check (e.g., "qwen2.5:3b")

        Returns:
            True if model exists.

        Raises:
            ModelNotFoundError: If model is not found.
            OllamaNotAvailableError: If Ollama service is not available.
        """
        try:
            response = requests.get(self.tags_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            models = data.get("models", [])

            # Check if model exists in the list
            for m in models:
                if m.get("name") == model or m.get("name").startswith(f"{model}:"):
                    return True

            raise ModelNotFoundError(model)

        except (ConnectionError, Timeout):
            raise OllamaNotAvailableError(self.base_url)
        except requests.exceptions.HTTPError as e:
            raise LLMError(f"Failed to check model availability: {e}")

    def generate(
        self,
        prompt: str,
        model: str = "qwen2.5:3b",
        system: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> str:
        """
        Generate text using Ollama API.

        Args:
            prompt: The prompt to generate from.
            model: Model name to use. Default: "qwen2.5:3b"
            system: Optional system prompt for context.
            temperature: Sampling temperature (0.0 to 1.0). Default: 0.7
            stream: Whether to stream the response. Default: False

        Returns:
            Generated text response.

        Raises:
            LLMError: If generation fails.
            OllamaNotAvailableError: If service is not available.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            return data.get("response", "").strip()

        except (ConnectionError, Timeout):
            raise OllamaNotAvailableError(self.base_url)
        except requests.exceptions.HTTPError as e:
            # Check if it's a model not found error
            if response.status_code == 404:
                raise ModelNotFoundError(model)
            raise LLMError(f"Failed to generate text: {e}")
        except json.JSONDecodeError as e:
            raise LLMError(f"Failed to parse Ollama response: {e}")

    def generate_with_context(
        self,
        prompt: str,
        context: Optional[str] = None,
        model: str = "qwen2.5:3b",
        max_context_length: int = 8000,
    ) -> str:
        """
        Generate text with optional context (e.g., git diff).

        Handles context length limits by truncating if needed.

        Args:
            prompt: The prompt to generate from.
            context: Optional context to include (e.g., git diff).
            model: Model name to use. Default: "qwen2.5:3b"
            max_context_length: Maximum characters for context. Default: 8000

        Returns:
            Generated text response.
        """
        full_prompt = prompt

        if context:
            # Truncate context if too long
            if len(context) > max_context_length:
                context = context[:max_context_length] + "\n\n... (diff truncated)"

            full_prompt = f"{prompt}\n\nContext:\n{context}"

        return self.generate(full_prompt, model=model)

    def extract_ticket_number(
        self,
        branch_name: str,
        ticket_prefix: str = "STAR",
        model: str = "qwen2.5:3b",
    ) -> Optional[str]:
        """
        Extract ticket number from branch name using LLM.

        Args:
            branch_name: Branch name to extract ticket from
            ticket_prefix: Expected ticket prefix (e.g., "STAR", "JIRA", "ENG")
            model: Model name to use. Default: "qwen2.5:3b"

        Returns:
            Ticket number (e.g., "STAR-12345") or None if not found.
        """
        from src.prompts import PRPrompts

        prompt = PRPrompts.extract_ticket_number_prompt(branch_name, ticket_prefix)

        response = self.generate(
            prompt=prompt,
            model=model,
            temperature=0.1,  # Low temperature for consistent extraction
        )

        # Parse response
        response = response.strip().upper()

        # Check if LLM found a ticket
        if response == "NONE" or not response:
            return None

        # Clean up response - extract just the ticket number
        # Format should be: STAR-12345
        import re
        match = re.search(rf"{ticket_prefix.upper()}-\d+", response)
        if match:
            return match.group(0)

        return None

    def generate_commit_message(
        self,
        ticket_number: str,
        changed_files: list,
        diff: str,
        model: str = "qwen2.5:3b",
    ) -> str:
        """
        Generate a commit message from uncommitted changes.

        Args:
            ticket_number: Ticket identifier (e.g., "STAR-41789")
            changed_files: List of modified files
            diff: Git diff of uncommitted changes
            model: Model name to use

        Returns:
            Generated commit message in format: "TICKET-NUMBER: description"
        """
        from src.prompts import PRPrompts

        # Truncate diff for token limits
        diff_summary = PRPrompts.extract_diff_summary(diff, max_length=2000)

        prompt = PRPrompts.generate_commit_message_prompt(
            ticket_number=ticket_number,
            changed_files=changed_files,
            diff_summary=diff_summary,
        )

        response = self.generate(
            prompt=prompt,
            model=model,
            temperature=0.3,  # Moderately low for consistency
        )

        return response.strip()
