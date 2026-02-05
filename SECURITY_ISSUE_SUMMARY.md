# Security Issue Summary: Data Leakage via Public Copilot API

## 🚨 CRITICAL ISSUE

**All company source code, diffs, and commit messages are currently being sent to public GitHub Copilot APIs instead of enterprise endpoints.**

## Current Flow (INSECURE)

```
┌─────────────────┐
│   Developer     │
│   runs          │
│   pr-agent      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  pr-agent (Local)                                       │
│  ┌───────────────────────────────────────────────┐     │
│  │ Hardcoded Public Values:                      │     │
│  │ • Client ID: Iv1.b507a08c87ecfe98             │     │
│  │ • OAuth: https://github.com/login/...         │     │
│  │ • API: https://api.githubcopilot.com          │     │
│  └───────────────────────────────────────────────┘     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      │ Sends company code/diffs
                      ▼
         ┌────────────────────────────┐
         │  PUBLIC INTERNET           │
         │  ┌──────────────────────┐  │
         │  │ github.com           │  │ ❌ Public OAuth
         │  └──────────────────────┘  │
         │  ┌──────────────────────┐  │
         │  │ api.github.com       │  │ ❌ Public API
         │  └──────────────────────┘  │
         │  ┌──────────────────────┐  │
         │  │ api.githubcopilot.com│  │ ❌ Public Copilot
         │  └──────────────────────┘  │
         └────────────────────────────┘

⚠️  DATA LEAKAGE RISKS:
    • Company source code exposed to public Copilot
    • Proprietary algorithms/business logic visible
    • Customer data in code comments leaked
    • Potential training data for public models
    • Compliance violations (GDPR, SOC2, etc.)
```

## Proposed Solution (SECURE)

```
┌─────────────────┐
│   Developer     │
│   runs          │
│   pr-agent      │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  pr-agent (Local) with Enterprise Config                │
│  ┌────────────────────────────────────────────────┐     │
│  │ Configurable Values:                           │     │
│  │ • Client ID: <ENTERPRISE_CLIENT_ID>            │     │
│  │ • OAuth: https://github.yourcompany.com/...    │     │
│  │ • API: https://copilot.yourcompany.com         │     │
│  └────────────────────────────────────────────────┘     │
└─────────────────────┬────────────────────────────────────┘
                      │
                      │ Company code stays within
                      │ enterprise boundary
                      ▼
         ┌────────────────────────────────┐
         │  ENTERPRISE INFRASTRUCTURE     │
         │  ┌──────────────────────────┐  │
         │  │ github.yourcompany.com   │  │ ✅ Enterprise OAuth
         │  └──────────────────────────┘  │
         │  ┌──────────────────────────┐  │
         │  │ Enterprise GitHub API    │  │ ✅ Enterprise API
         │  └──────────────────────────┘  │
         │  ┌──────────────────────────┐  │
         │  │ Enterprise Copilot API   │  │ ✅ Enterprise Copilot
         │  │ (Isolated, Compliant)    │  │
         │  └──────────────────────────┘  │
         └────────────────────────────────┘
                      │
                      ▼
              ┌─────────────┐
              │  If needed: │
              │  GitHub     │  ✅ Controlled via enterprise
              │  Public     │     with compliance guarantees
              └─────────────┘

✅  SECURITY IMPROVEMENTS:
    • All data stays within enterprise boundary
    • Copilot Business/Enterprise compliance guarantees
    • No training on company code (per enterprise agreement)
    • Audit trail for compliance
    • Data residency controls
```

## What Needs to Change

### Current Code (INSECURE)
```python
# src/copilot_auth.py:18
GITHUB_CLIENT_ID = "Iv1.b507a08c87ecfe98"  # ❌ PUBLIC
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"  # ❌ PUBLIC
GITHUB_COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"  # ❌ PUBLIC

# src/config.py:27
copilot_api_base: str = "https://api.githubcopilot.com"  # ❌ PUBLIC
```

### Proposed Code (SECURE)
```python
# Make endpoints configurable via environment/config
GITHUB_CLIENT_ID = os.getenv("PR_AGENT_GITHUB_CLIENT_ID") or DEFAULT_PUBLIC_ID
GITHUB_DEVICE_CODE_URL = os.getenv("PR_AGENT_OAUTH_DEVICE_URL") or DEFAULT_PUBLIC_URL
GITHUB_COPILOT_TOKEN_URL = os.getenv("PR_AGENT_COPILOT_TOKEN_URL") or DEFAULT_PUBLIC_URL

# Warn if using public
if is_using_public_endpoints():
    logger.warning("⚠️  Using PUBLIC Copilot API. Configure enterprise endpoints!")

# Or better: REQUIRE enterprise config, fail if not provided
if not GITHUB_CLIENT_ID.startswith("Iv1.enterprise"):
    raise SecurityError("Enterprise client ID required. See docs/ENTERPRISE_SETUP.md")
```

## Impact Assessment

### Who is Affected?
- **All users** of pr-agent within the company
- Any repository using this tool
- Any PR created with this tool

### What Data Has Been Exposed?
Potentially all of:
- Source code diffs
- Commit messages
- File names and structure
- Branch names (often contain ticket IDs)
- PR descriptions (generated from above)

### Since When?
- First commit of pr-agent: ~3 weeks ago based on git log
- Every PR created since then

## Immediate Actions Required

### 1. **URGENT: Audit Recent Usage**
```bash
# Find all PRs created with pr-agent
gh pr list --search "Co-Authored-By: Claude Sonnet" --limit 1000

# Review for sensitive data exposure
```

### 2. **STOP Current Usage**
- Inform team to stop using pr-agent until fixed
- Or: Emergency patch with env vars (see Quick Fix below)

### 3. **Get Enterprise Credentials**
Contact platform/security team for:
- Enterprise GitHub URL
- Enterprise OAuth app client ID
- Enterprise Copilot API endpoints

### 4. **Deploy Fix**
Follow `SECURITY_FIX_PLAN.md` - 3 week timeline

## Quick Emergency Fix (Interim Solution)

If you have enterprise details NOW, you can use environment variables immediately:

```bash
# Add to ~/.bashrc or ~/.zshrc
export PR_AGENT_USE_ENTERPRISE=true
export PR_AGENT_GITHUB_CLIENT_ID="<ASK_PLATFORM_TEAM>"
export PR_AGENT_GITHUB_ENTERPRISE_URL="https://github.yourcompany.com"
export PR_AGENT_COPILOT_API_BASE="<ASK_PLATFORM_TEAM>"

# Requires code changes to read these env vars (see SECURITY_FIX_PLAN.md Phase 1-2)
```

**Note:** Code changes still required to actually use these env vars. Current code ignores them.

## Compliance Implications

Potential violations:
- **GDPR**: If code contains EU customer data
- **SOC2**: Data handling controls
- **HIPAA**: If healthcare-related code
- **PCI-DSS**: If payment processing code
- **Internal policies**: Code confidentiality agreements

## Recommended Communication

### To Security Team
> "We discovered that our pr-agent tool is currently using public GitHub Copilot APIs instead of our enterprise endpoints. This means company source code has been sent to public APIs for the past 3 weeks. We need enterprise OAuth credentials and API endpoints to fix this ASAP. We have a 3-week fix plan ready to implement."

### To Engineering Team
> "URGENT: Please stop using pr-agent until further notice. We're implementing enterprise Copilot endpoints to ensure code stays within our infrastructure. Expected fix: 3 weeks. We'll notify you when it's safe to resume use."

### To Leadership
> "We identified a data leakage risk in our PR automation tool. Company code was being sent to public APIs. We've scoped the impact, created a fix plan, and are coordinating with security team. No evidence of breach, but we're treating as high priority. Fix timeline: 3 weeks."

## Questions?

See `SECURITY_FIX_PLAN.md` for:
- Detailed implementation plan
- Configuration examples
- Testing strategy
- Rollout plan

## Priority: 🔴 CRITICAL

**Do not delay.** Every PR created with current setup sends company code to public APIs.
