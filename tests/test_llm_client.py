"""Tests for LLM client module."""

import pytest
from unittest.mock import Mock, patch
from pr_agent.llm_client import CopilotClient
from pr_agent.exceptions import LLMError


class TestCopilotClient:
    """Test Copilot client functionality."""

    def test_initialization(self):
        """Test client initialization."""
        client = CopilotClient(
            api_base="https://api.githubcopilot.com", api_key="test-key", timeout=60
        )
        assert client.api_base == "https://api.githubcopilot.com/v1"
        assert client.api_key == "test-key"
        assert client.timeout == 60

    def test_api_base_normalization(self):
        """Test API base URL normalization."""
        client = CopilotClient(api_base="https://api.githubcopilot.com/", api_key="test-key")
        assert client.api_base == "https://api.githubcopilot.com/v1"

    @patch("requests.post")
    def test_generate_success(self, mock_post):
        """Test successful generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated content"}}]
        }
        mock_post.return_value = mock_response

        client = CopilotClient(api_base="https://api.githubcopilot.com", api_key="test-key")
        result = client.generate("Test prompt")
        assert result == "Generated content"

    @patch("requests.post")
    def test_generate_auth_failure(self, mock_post):
        """Test authentication failure."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorized")
        mock_post.return_value = mock_response

        client = CopilotClient(api_base="https://api.githubcopilot.com", api_key="invalid-key")
        with pytest.raises(LLMError, match="authentication failed"):
            client.generate("Test prompt")
