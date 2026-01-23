"""Tests for LLM client module."""

import pytest
from unittest.mock import Mock, patch
from pr_agent.llm_client import OllamaClient
from pr_agent.exceptions import OllamaNotAvailableError, ModelNotFoundError


class TestOllamaClient:
    """Test Ollama client functionality."""

    def test_initialization(self):
        """Test client initialization."""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.timeout == 120

    def test_custom_url(self):
        """Test client with custom URL."""
        client = OllamaClient(base_url="http://custom:8080")
        assert client.base_url == "http://custom:8080"

    @patch('requests.get')
    def test_check_availability_success(self, mock_get):
        """Test successful availability check."""
        mock_get.return_value.status_code = 200

        client = OllamaClient()
        assert client.check_availability() is True

    @patch('requests.get')
    def test_check_availability_failure(self, mock_get):
        """Test failed availability check."""
        mock_get.side_effect = ConnectionError()

        client = OllamaClient()
        with pytest.raises(OllamaNotAvailableError):
            client.check_availability()
