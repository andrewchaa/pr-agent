# Security Fix Plan: Migrate from Public to Enterprise Copilot

## Problem Statement

**CRITICAL SECURITY ISSUE**: The PR agent currently uses:
- Public GitHub OAuth client ID (`Iv1.b507a08c87ecfe98`)
- Public GitHub API endpoints (`https://api.github.com`, `https://api.githubcopilot.com`)
- Public Copilot token exchange endpoint

This means all company source code, diffs, and commit messages are being sent to **public GitHub Copilot APIs** instead of the company's **Enterprise Copilot endpoints**, creating significant data leakage risk.

## Current Architecture (Insecure)

### Authentication Flow
```
1. User initiates device flow with PUBLIC client ID
2. Authenticates via public github.com
3. Exchanges for public Copilot token (https://api.github.com/copilot_internal/v2/token)
4. Makes API calls to public Copilot (https://api.githubcopilot.com)
```

### Hardcoded Public Values (src/copilot_auth.py:18-21)
```python
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # PUBLIC CLIENT ID
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"  # PUBLIC
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # PUBLIC
GITHUB_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"  # PUBLIC
```

### Public API Usage (src/llm_client.py, src/config.py)
```python
copilot_api_base: str = "https://api.githubcopilot.com"  # PUBLIC API
```

## Required Information from Security Team

Before implementing, need to obtain from your security/platform team:

### 1. Enterprise GitHub Setup
- [ ] Are you using **GitHub Enterprise Cloud** or **GitHub Enterprise Server**?
- [ ] What is your GitHub Enterprise URL? (e.g., `https://github.yourcompany.com`)
- [ ] Is this Copilot Business or Copilot Enterprise?

### 2. Enterprise OAuth App
- [ ] **Enterprise OAuth App Client ID** (replaces `Iv1.b507a08c87ecfe98`)
- [ ] OAuth app configuration (should be created in enterprise instance)
- [ ] Required scopes: `read:user`, `copilot`

### 3. Enterprise API Endpoints
- [ ] **Enterprise GitHub API base URL** (e.g., `https://api.github.yourcompany.com` or `https://github.yourcompany.com/api/v3`)
- [ ] **Enterprise Copilot API base URL** (e.g., `https://copilot-proxy.yourcompany.com` or enterprise-specific endpoint)
- [ ] **Copilot token exchange endpoint** (enterprise version of `/copilot_internal/v2/token`)

### 4. Network/Proxy Configuration
- [ ] Are there proxy servers required for external API calls?
- [ ] VPN requirements?
- [ ] Certificate/TLS requirements (self-signed certs for GHES?)

### 5. Authentication Method
Confirm if enterprise uses:
- [ ] **OAuth Device Flow** (same as current, but with enterprise endpoints)
- [ ] **Personal Access Token** (PAT) with Copilot scope
- [ ] **GitHub App authentication** (machine-to-machine)
- [ ] **SSO/SAML** integration requirements

## Implementation Plan

### Phase 1: Make Configuration Flexible (Week 1)

#### 1.1 Update Configuration Schema
**File**: `src/config.py`

Add new configuration fields:
```python
@dataclass
class Config:
    # Existing fields...

    # NEW: Enterprise GitHub settings
    github_enterprise_url: Optional[str] = None  # e.g., "https://github.yourcompany.com"
    github_api_base: Optional[str] = None        # e.g., "https://api.github.yourcompany.com"

    # NEW: Enterprise OAuth settings
    github_client_id: Optional[str] = None       # Enterprise OAuth app client ID
    oauth_device_code_url: Optional[str] = None  # Enterprise device code endpoint
    oauth_token_url: Optional[str] = None        # Enterprise token endpoint

    # NEW: Enterprise Copilot settings
    copilot_token_url: Optional[str] = None      # Enterprise Copilot token exchange
    copilot_api_base: str = "https://api.githubcopilot.com"  # Keep as default, override for enterprise

    # NEW: Security settings
    verify_ssl: bool = True                      # For GHES with self-signed certs
    use_enterprise_endpoints: bool = False       # Feature flag for gradual rollout
```

Add environment variable mappings:
```python
env_mapping = {
    # Existing...

    # NEW mappings
    "PR_AGENT_GITHUB_ENTERPRISE_URL": "github_enterprise_url",
    "PR_AGENT_GITHUB_API_BASE": "github_api_base",
    "PR_AGENT_GITHUB_CLIENT_ID": "github_client_id",
    "PR_AGENT_OAUTH_DEVICE_CODE_URL": "oauth_device_code_url",
    "PR_AGENT_OAUTH_TOKEN_URL": "oauth_token_url",
    "PR_AGENT_COPILOT_TOKEN_URL": "copilot_token_url",
    "PR_AGENT_VERIFY_SSL": "verify_ssl",
    "PR_AGENT_USE_ENTERPRISE": "use_enterprise_endpoints",
}
```

#### 1.2 Create Enterprise Configuration Helper
**File**: `src/config.py` (add new method)

```python
@classmethod
def for_enterprise(
    cls,
    enterprise_url: str,
    client_id: str,
    copilot_api_base: Optional[str] = None,
    verify_ssl: bool = True,
) -> "Config":
    """
    Create enterprise-ready configuration.

    Args:
        enterprise_url: GitHub Enterprise URL (e.g., "https://github.yourcompany.com")
        client_id: Enterprise OAuth app client ID
        copilot_api_base: Enterprise Copilot API URL (if different from default)
        verify_ssl: Whether to verify SSL certificates

    Returns:
        Config configured for enterprise use
    """
    # Auto-detect API endpoints from enterprise URL
    api_base = f"{enterprise_url}/api/v3"  # Standard GHES pattern

    return cls(
        github_enterprise_url=enterprise_url,
        github_api_base=api_base,
        github_client_id=client_id,
        oauth_device_code_url=f"{enterprise_url}/login/device/code",
        oauth_token_url=f"{enterprise_url}/login/oauth/access_token",
        copilot_token_url=f"{api_base}/copilot_internal/v2/token",
        copilot_api_base=copilot_api_base or "https://api.githubcopilot.com",
        verify_ssl=verify_ssl,
        use_enterprise_endpoints=True,
    )
```

#### 1.3 Update Default Config File Template
**File**: `src/config.py` (update `create_default_config_file`)

```yaml
# Example config with enterprise settings (commented out by default)
#
# For public GitHub (default):
# copilot_api_base: "https://api.githubcopilot.com"
#
# For GitHub Enterprise:
# use_enterprise_endpoints: true
# github_enterprise_url: "https://github.yourcompany.com"
# github_client_id: "Iv1.YOUR_ENTERPRISE_CLIENT_ID"
# github_api_base: "https://github.yourcompany.com/api/v3"
# copilot_api_base: "https://copilot.yourcompany.com"  # If different
# verify_ssl: true
```

### Phase 2: Update Authentication Layer (Week 1)

#### 2.1 Refactor CopilotAuthenticator
**File**: `src/copilot_auth.py`

**Changes needed:**

1. **Remove hardcoded constants**, make them configurable:
```python
# BEFORE (lines 18-21):
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # HARDCODED PUBLIC
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"

# AFTER:
# Move to defaults that can be overridden
DEFAULT_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # Public fallback (for backward compat)
DEFAULT_DEVICE_CODE_URL = "https://github.com/login/device/code"
DEFAULT_TOKEN_URL = "https://github.com/login/oauth/access_token"
DEFAULT_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
```

2. **Update `__init__` to accept configuration**:
```python
class CopilotAuthenticator:
    def __init__(
        self,
        token_dir: Optional[str] = None,
        client_id: Optional[str] = None,
        device_code_url: Optional[str] = None,
        token_url: Optional[str] = None,
        copilot_token_url: Optional[str] = None,
        verify_ssl: bool = True,
    ):
        """
        Initialize Copilot authenticator.

        Args:
            token_dir: Directory to store tokens
            client_id: OAuth client ID (enterprise or public)
            device_code_url: Device code endpoint URL
            token_url: Access token endpoint URL
            copilot_token_url: Copilot token exchange endpoint
            verify_ssl: Whether to verify SSL certificates
        """
        if token_dir is None:
            token_dir = os.path.expanduser("~/.config/pr-agent/copilot")

        self.token_dir = token_dir
        self.client_id = client_id or DEFAULT_CLIENT_ID
        self.device_code_url = device_code_url or DEFAULT_DEVICE_CODE_URL
        self.token_url = token_url or DEFAULT_TOKEN_URL
        self.copilot_token_url = copilot_token_url or DEFAULT_COPILOT_TOKEN_URL
        self.verify_ssl = verify_ssl

        os.makedirs(self.token_dir, exist_ok=True)
        # ... rest of init
```

3. **Update all methods to use instance variables**:
```python
def _request_device_code(self) -> Dict[str, Any]:
    """Request device code from GitHub (enterprise or public)."""
    response = requests.post(
        self.device_code_url,  # Use instance variable
        json={"client_id": self.client_id, "scope": "read:user"},  # Use instance variable
        headers={"accept": "application/json", "content-type": "application/json"},
        timeout=30,
        verify=self.verify_ssl,  # NEW: SSL verification control
    )
    # ... rest of method

def _poll_for_token(self, device_info: Dict[str, Any]) -> str:
    # ...
    response = requests.post(
        self.token_url,  # Use instance variable instead of hardcoded
        json={
            "client_id": self.client_id,  # Use instance variable
            "device_code": device_info["device_code"],
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
        headers={"accept": "application/json", "content-type": "application/json"},
        timeout=30,
        verify=self.verify_ssl,  # NEW: SSL verification control
    )
    # ... rest of method

def _exchange_for_copilot_token(self, access_token: str) -> Dict[str, Any]:
    response = requests.get(
        self.copilot_token_url,  # Use instance variable
        headers={
            "authorization": f"token {access_token}",
            "editor-version": EDITOR_VERSION,
            "editor-plugin-version": EDITOR_PLUGIN_VERSION,
            "user-agent": USER_AGENT,
            "accept": "application/json",
        },
        timeout=30,
        verify=self.verify_ssl,  # NEW: SSL verification control
    )
    # ... rest of method
```

### Phase 3: Update LLM Client (Week 1)

#### 3.1 Add SSL Verification to LLM Client
**File**: `src/llm_client.py`

```python
class CopilotClient:
    def __init__(
        self,
        api_base: str,
        api_key: str,
        timeout: int = 60,
        verify_ssl: bool = True,  # NEW
    ):
        """
        Initialize Copilot client.

        Args:
            api_base: Base URL for Copilot API (enterprise or public)
            api_key: GitHub Copilot API key
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates (for GHES)
        """
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl  # NEW
        self.chat_url = f"{self.api_base}/chat/completions"

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = self._get_headers()

        response = requests.post(
            self.chat_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
            verify=self.verify_ssl,  # NEW: SSL verification control
        )
        # ... rest of method
```

### Phase 4: Wire Configuration Through CLI (Week 1)

#### 4.1 Update CLI to Pass Config to Authenticator
**File**: `src/cli.py` (around line 240-260)

```python
# BEFORE:
authenticator = CopilotAuthenticator(token_dir=cfg.copilot_token_dir)

# AFTER:
authenticator = CopilotAuthenticator(
    token_dir=cfg.copilot_token_dir,
    client_id=cfg.github_client_id,
    device_code_url=cfg.oauth_device_code_url,
    token_url=cfg.oauth_token_url,
    copilot_token_url=cfg.copilot_token_url,
    verify_ssl=cfg.verify_ssl,
)
```

#### 4.2 Update LLM Client Initialization
**File**: `src/cli.py` (around line 254-259)

```python
# BEFORE:
llm_client = CopilotClient(
    api_base=cfg.copilot_api_base,
    api_key=copilot_token,
    timeout=cfg.copilot_timeout,
)

# AFTER:
llm_client = CopilotClient(
    api_base=cfg.copilot_api_base,
    api_key=copilot_token,
    timeout=cfg.copilot_timeout,
    verify_ssl=cfg.verify_ssl,  # NEW
)
```

### Phase 5: Documentation and Migration Guide (Week 2)

#### 5.1 Create Enterprise Setup Guide
**File**: `docs/ENTERPRISE_SETUP.md`

```markdown
# Enterprise GitHub Copilot Setup

## Prerequisites

1. Active GitHub Copilot Business or Enterprise subscription
2. Enterprise OAuth app created in your GitHub Enterprise instance
3. API endpoints for your enterprise

## Configuration

### Option 1: Environment Variables (Recommended for CI/CD)

```bash
export PR_AGENT_USE_ENTERPRISE=true
export PR_AGENT_GITHUB_ENTERPRISE_URL="https://github.yourcompany.com"
export PR_AGENT_GITHUB_CLIENT_ID="Iv1.YOUR_ENTERPRISE_CLIENT_ID"
export PR_AGENT_GITHUB_API_BASE="https://github.yourcompany.com/api/v3"
export PR_AGENT_COPILOT_TOKEN_URL="https://github.yourcompany.com/api/v3/copilot_internal/v2/token"
export PR_AGENT_COPILOT_API_BASE="https://copilot.yourcompany.com"
```

### Option 2: Config File

Edit `~/.config/pr-agent/config.yaml`:

```yaml
use_enterprise_endpoints: true
github_enterprise_url: "https://github.yourcompany.com"
github_client_id: "Iv1.YOUR_ENTERPRISE_CLIENT_ID"
github_api_base: "https://github.yourcompany.com/api/v3"
copilot_token_url: "https://github.yourcompany.com/api/v3/copilot_internal/v2/token"
copilot_api_base: "https://copilot.yourcompany.com"
verify_ssl: true
```

### Self-Signed Certificates (GitHub Enterprise Server)

If using self-signed certificates:

```yaml
verify_ssl: false  # WARNING: Only use in secure networks
```

Or better, add your enterprise CA certificate to system trust store.

## OAuth App Setup

Your platform team needs to create an OAuth app in GitHub Enterprise:

1. Navigate to: `https://github.yourcompany.com/settings/apps`
2. Create new OAuth app
3. Set callback URL: `http://127.0.0.1` (for device flow)
4. Required permissions:
   - `read:user`
   - `copilot` (if available as scope)
5. Copy the Client ID

## Verification

Test your setup:

```bash
# Clear existing tokens
rm -rf ~/.config/pr-agent/copilot

# Run pr-agent
pr-agent create

# Verify you're prompted with your enterprise URL
# Should see: "Visit: https://github.yourcompany.com/login/device"
```

## Troubleshooting

### "Invalid client_id" error
- Verify client ID matches your enterprise OAuth app
- Check that OAuth app is active

### "Token exchange failed" error
- Verify `copilot_token_url` is correct
- Check that your enterprise has Copilot enabled
- Verify your user has Copilot access

### SSL certificate errors
- Add enterprise CA cert to system trust store, or
- Use `verify_ssl: false` (not recommended for production)
```

#### 5.2 Update Main README
**File**: `README.md`

Add enterprise section:
```markdown
## Enterprise Setup

For GitHub Enterprise Cloud or Server with Copilot Business/Enterprise:

See [Enterprise Setup Guide](docs/ENTERPRISE_SETUP.md) for detailed configuration.

Quick start:
```bash
export PR_AGENT_USE_ENTERPRISE=true
export PR_AGENT_GITHUB_ENTERPRISE_URL="https://github.yourcompany.com"
export PR_AGENT_GITHUB_CLIENT_ID="your-enterprise-client-id"
```

#### 5.3 Update CLAUDE.md
**File**: `CLAUDE.md`

Add security section:
```markdown
## Security & Enterprise Usage

**IMPORTANT**: The tool supports both public GitHub Copilot and Enterprise Copilot.

### For Enterprise Users:
Always configure enterprise endpoints to prevent data leakage:
- Set `use_enterprise_endpoints: true` in config
- Provide enterprise OAuth client ID
- Specify enterprise API endpoints

See `docs/ENTERPRISE_SETUP.md` for full setup.

### Default Behavior:
Without configuration, uses public GitHub endpoints (suitable for open source only).
```

### Phase 6: Testing & Validation (Week 2)

#### 6.1 Create Enterprise Test Suite
**File**: `tests/test_enterprise_config.py`

```python
"""Tests for enterprise configuration."""

import pytest
from src.config import Config
from src.copilot_auth import CopilotAuthenticator

def test_enterprise_config_creation():
    """Test creating enterprise configuration."""
    config = Config.for_enterprise(
        enterprise_url="https://github.example.com",
        client_id="Iv1.enterprise123",
    )

    assert config.use_enterprise_endpoints is True
    assert config.github_enterprise_url == "https://github.example.com"
    assert config.github_client_id == "Iv1.enterprise123"
    assert config.oauth_device_code_url == "https://github.example.com/login/device/code"
    assert config.oauth_token_url == "https://github.example.com/login/oauth/access_token"
    assert config.copilot_token_url == "https://github.example.com/api/v3/copilot_internal/v2/token"

def test_enterprise_auth_uses_custom_endpoints():
    """Test that authenticator uses enterprise endpoints."""
    auth = CopilotAuthenticator(
        client_id="Iv1.enterprise123",
        device_code_url="https://github.example.com/login/device/code",
        token_url="https://github.example.com/login/oauth/access_token",
        copilot_token_url="https://github.example.com/api/v3/copilot_internal/v2/token",
    )

    assert auth.client_id == "Iv1.enterprise123"
    assert "github.example.com" in auth.device_code_url
    assert "github.example.com" in auth.token_url
    assert "github.example.com" in auth.copilot_token_url

def test_public_copilot_still_works():
    """Test backward compatibility with public Copilot."""
    auth = CopilotAuthenticator()  # No args = public

    assert "Iv1.b507a08c87ecfe98" in auth.client_id
    assert "github.com" in auth.device_code_url
    assert "api.github.com" in auth.copilot_token_url
```

#### 6.2 Manual Testing Checklist

**Pre-deployment testing:**
- [ ] Test public Copilot still works (backward compatibility)
- [ ] Test enterprise config creation via `Config.for_enterprise()`
- [ ] Test environment variable loading
- [ ] Test config file loading
- [ ] Verify SSL verification can be disabled
- [ ] Test with mock enterprise endpoints

**Post-deployment testing with real enterprise:**
- [ ] Test device flow with enterprise URL
- [ ] Verify OAuth uses enterprise client ID
- [ ] Verify token exchange hits enterprise endpoint
- [ ] Verify API calls go to enterprise Copilot API
- [ ] Test with self-signed certs (if applicable)
- [ ] Verify no calls to public APIs appear in network logs

### Phase 7: Rollout & Migration (Week 3)

#### 7.1 Phased Rollout Plan

**Week 3, Day 1-2: Internal Testing**
- Deploy to development environment
- Test with 2-3 volunteer developers
- Monitor network traffic to confirm no public API calls
- Gather feedback on UX

**Week 3, Day 3-4: Team Rollout**
- Share setup guide with team
- Help developers configure enterprise settings
- Create runbook for common issues

**Week 3, Day 5: Organization Rollout**
- Announce to wider org
- Provide self-service docs
- Monitor for issues

#### 7.2 Migration Steps for Existing Users

1. **Clear existing tokens** (important! Old tokens are for public API):
```bash
rm -rf ~/.config/pr-agent/copilot
```

2. **Update configuration**:
```bash
# Option A: Environment variables
export PR_AGENT_USE_ENTERPRISE=true
export PR_AGENT_GITHUB_ENTERPRISE_URL="https://github.yourcompany.com"
export PR_AGENT_GITHUB_CLIENT_ID="<your-client-id>"

# Option B: Config file
pr-agent init-config  # Then edit ~/.config/pr-agent/config.yaml
```

3. **Re-authenticate**:
```bash
pr-agent create
# Follow enterprise device flow prompts
```

#### 7.3 Enforce Enterprise Mode

**Option 1: Remove public fallback** (recommended for security)

After migration complete, remove public client ID fallback:
```python
# src/copilot_auth.py
# REMOVE these defaults entirely
# DEFAULT_CLIENT_ID = "Iv1.b507a08c87ecfe98"

# Make client_id required
def __init__(
    self,
    token_dir: Optional[str] = None,
    client_id: str,  # REQUIRED, no default
    ...
):
    if not client_id:
        raise CopilotAuthError(
            "GitHub client ID is required. "
            "For enterprise: set PR_AGENT_GITHUB_CLIENT_ID. "
            "See docs/ENTERPRISE_SETUP.md"
        )
```

**Option 2: Add warning** (interim approach)
```python
if not self.client_id or self.client_id == DEFAULT_CLIENT_ID:
    import warnings
    warnings.warn(
        "Using public GitHub Copilot API. "
        "For enterprise, configure PR_AGENT_GITHUB_CLIENT_ID. "
        "See docs/ENTERPRISE_SETUP.md",
        SecurityWarning
    )
```

### Phase 8: Monitoring & Compliance (Ongoing)

#### 8.1 Add Telemetry/Logging

Add logging to track which endpoints are being used:

```python
# src/copilot_auth.py
import logging

logger = logging.getLogger(__name__)

def __init__(self, ...):
    # ... existing code ...

    if "github.com" in self.device_code_url:
        logger.warning(
            "Using public GitHub endpoints. "
            "For enterprise, configure enterprise URLs."
        )
    else:
        logger.info(f"Using enterprise endpoints: {self.device_code_url}")
```

#### 8.2 Network Monitoring

Recommend to security team:
- Monitor for outbound requests to `api.githubcopilot.com` (should be zero after migration)
- Whitelist only enterprise Copilot endpoints
- Block public Copilot API at firewall level (optional, for enforcement)

## Summary of Changes

### Files to Modify
1. `src/config.py` - Add enterprise config fields
2. `src/copilot_auth.py` - Make endpoints configurable
3. `src/llm_client.py` - Add SSL verification support
4. `src/cli.py` - Wire config through to auth & client
5. `README.md` - Add enterprise setup section
6. `CLAUDE.md` - Add security notes

### New Files to Create
1. `docs/ENTERPRISE_SETUP.md` - Detailed setup guide
2. `tests/test_enterprise_config.py` - Enterprise config tests
3. `examples/enterprise_config.yaml` - Example enterprise config

### Critical Security Notes
1. **Do NOT commit real enterprise client IDs to git**
2. **Clear public tokens before switching** (`rm -rf ~/.config/pr-agent/copilot`)
3. **Verify network calls** go to enterprise endpoints before rollout
4. **Consider removing public fallback** after migration for enforcement

## Timeline

- **Week 1**: Implementation (Phases 1-4)
- **Week 2**: Documentation, testing, validation (Phases 5-6)
- **Week 3**: Rollout and migration (Phase 7)
- **Ongoing**: Monitoring and compliance (Phase 8)

## Questions to Ask Security Team

Before starting implementation, get answers to:

1. What is our GitHub Enterprise URL?
2. What is the enterprise OAuth app client ID we should use?
3. What is the enterprise Copilot API endpoint?
4. Are there proxy/VPN requirements?
5. Do we use self-signed certificates (GHES)?
6. What is the timeline for migration? (Should we enforce enterprise-only immediately?)
7. Should we block public Copilot API at network level?

## Next Steps

1. **Immediate**: Share this plan with security team for review
2. **Get answers**: Collect required enterprise endpoints and credentials
3. **Week 1**: Begin implementation (start with Phase 1)
4. **Week 2**: Test with enterprise endpoints
5. **Week 3**: Coordinate migration with team
