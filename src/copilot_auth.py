"""
GitHub Copilot authentication module.

Handles OAuth device flow and token exchange for GitHub Copilot API access.
"""

import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import requests

from src.exceptions import CopilotAuthError


GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"

COPILOT_VERSION = "0.26.7"
EDITOR_VERSION = "vscode/1.95.0"
EDITOR_PLUGIN_VERSION = f"copilot-chat/{COPILOT_VERSION}"
USER_AGENT = f"GitHubCopilotChat/{COPILOT_VERSION}"


class CopilotAuthenticator:
    """Handles GitHub Copilot authentication via OAuth device flow."""

    def __init__(self, token_dir: Optional[str] = None):
        """
        Initialize Copilot authenticator.

        Args:
            token_dir: Directory to store tokens. Defaults to ~/.config/pr-agent/copilot
        """
        if token_dir is None:
            token_dir = os.path.expanduser("~/.config/pr-agent/copilot")

        self.token_dir = token_dir
        os.makedirs(self.token_dir, exist_ok=True)

        self.access_token_file = os.path.join(self.token_dir, "access-token")
        self.api_key_file = os.path.join(self.token_dir, "api-key.json")

    def get_copilot_token(self) -> str:
        """
        Get valid Copilot API token, refreshing if needed.

        Returns:
            Valid Copilot API token

        Raises:
            CopilotAuthError: If authentication fails
        """
        try:
            api_key_info = self._load_api_key()
            if api_key_info and not self._is_token_expired(api_key_info):
                return api_key_info["token"]
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

        access_token = self._get_access_token()
        api_key_info = self._exchange_for_copilot_token(access_token)
        self._save_api_key(api_key_info)

        return api_key_info["token"]

    def _load_api_key(self) -> Optional[Dict[str, Any]]:
        """Load API key from cache."""
        if not os.path.exists(self.api_key_file):
            return None

        with open(self.api_key_file, "r") as f:
            return json.load(f)

    def _save_api_key(self, api_key_info: Dict[str, Any]) -> None:
        """Save API key to cache."""
        with open(self.api_key_file, "w") as f:
            json.dump(api_key_info, f)

    def _is_token_expired(self, api_key_info: Dict[str, Any]) -> bool:
        """Check if API token is expired."""
        expires_at = api_key_info.get("expires_at")
        if not expires_at:
            return True

        expiry_time = datetime.fromtimestamp(expires_at)
        return datetime.now() >= expiry_time - timedelta(minutes=5)

    def _get_access_token(self) -> str:
        """
        Get GitHub access token via device flow or from cache.

        Returns:
            GitHub access token

        Raises:
            CopilotAuthError: If device flow fails
        """
        if os.path.exists(self.access_token_file):
            with open(self.access_token_file, "r") as f:
                token = f.read().strip()
                if token:
                    return token

        return self._initiate_device_flow()

    def _initiate_device_flow(self) -> str:
        """
        Initiate GitHub OAuth device flow.

        Returns:
            GitHub access token

        Raises:
            CopilotAuthError: If device flow fails
        """
        try:
            device_info = self._request_device_code()
            print(f"\n🔐 GitHub Copilot Authentication Required")
            print(f"Visit: {device_info['verification_uri']}")
            print(f"Enter code: {device_info['user_code']}\n")

            access_token = self._poll_for_token(device_info)

            with open(self.access_token_file, "w") as f:
                f.write(access_token)

            return access_token

        except requests.exceptions.RequestException as e:
            raise CopilotAuthError(f"Device flow failed: {e}")

    def _request_device_code(self) -> Dict[str, Any]:
        """Request device code from GitHub."""
        response = requests.post(
            GITHUB_DEVICE_CODE_URL,
            json={"client_id": GITHUB_CLIENT_ID, "scope": "read:user"},
            headers={"accept": "application/json", "content-type": "application/json"},
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        required_fields = ["device_code", "user_code", "verification_uri", "interval"]
        if not all(field in data for field in required_fields):
            raise CopilotAuthError("Device code response missing required fields")

        return data

    def _poll_for_token(self, device_info: Dict[str, Any]) -> str:
        """
        Poll GitHub for access token after user authorization.

        Args:
            device_info: Device code information from GitHub

        Returns:
            GitHub access token

        Raises:
            CopilotAuthError: If polling fails or times out
        """
        interval = device_info.get("interval", 5)
        expires_in = device_info.get("expires_in", 900)
        max_attempts = expires_in // interval

        for attempt in range(max_attempts):
            time.sleep(interval)

            response = requests.post(
                GITHUB_ACCESS_TOKEN_URL,
                json={
                    "client_id": GITHUB_CLIENT_ID,
                    "device_code": device_info["device_code"],
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"accept": "application/json", "content-type": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                continue

            result = response.json()

            if "access_token" in result:
                print("✅ Authentication successful!\n")
                return result["access_token"]

            error = result.get("error")
            if error == "authorization_pending":
                if attempt % 3 == 0:
                    print(f"⏳ Waiting for authorization... ({attempt + 1}/{max_attempts})")
                continue
            elif error == "slow_down":
                interval += 5
                continue
            elif error in ["expired_token", "access_denied"]:
                raise CopilotAuthError(f"Authorization {error}")

        raise CopilotAuthError("Device flow timeout - authorization not received")

    def _exchange_for_copilot_token(self, access_token: str) -> Dict[str, Any]:
        """
        Exchange GitHub access token for Copilot API token.

        Args:
            access_token: GitHub access token

        Returns:
            Copilot API token information with expiration

        Raises:
            CopilotAuthError: If token exchange fails
        """
        try:
            response = requests.get(
                GITHUB_COPILOT_TOKEN_URL,
                headers={
                    "authorization": f"token {access_token}",
                    "editor-version": EDITOR_VERSION,
                    "editor-plugin-version": EDITOR_PLUGIN_VERSION,
                    "user-agent": USER_AGENT,
                    "accept": "application/json",
                },
                timeout=30,
            )

            if response.status_code == 401:
                raise CopilotAuthError(
                    "GitHub token is invalid or expired. Please re-authenticate."
                )
            elif response.status_code == 403:
                raise CopilotAuthError(
                    "Access denied. Ensure you have an active GitHub Copilot subscription."
                )

            response.raise_for_status()
            data = response.json()

            if "token" not in data:
                raise CopilotAuthError("Copilot token response missing 'token' field")

            return data

        except requests.exceptions.RequestException as e:
            raise CopilotAuthError(f"Token exchange failed: {e}")

    def clear_tokens(self) -> None:
        """Clear all cached tokens."""
        for token_file in [self.access_token_file, self.api_key_file]:
            if os.path.exists(token_file):
                os.remove(token_file)
