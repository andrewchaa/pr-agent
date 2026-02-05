# Security Fix Checklist

## Immediate Actions (Today)

### For You (Developer)
- [ ] **Stop using pr-agent** until enterprise endpoints configured
- [ ] **Review this document** with security team
- [ ] **Share** `SECURITY_ISSUE_SUMMARY.md` with security team
- [ ] **Share** `SECURITY_FIX_PLAN.md` with platform/engineering team
- [ ] **Audit recent PRs** for sensitive data exposure:
  ```bash
  gh pr list --search "Co-Authored-By: Claude Sonnet" --limit 100
  ```

### For Security Team
- [ ] **Assess impact**: Review what data may have been exposed
- [ ] **Provide enterprise credentials**:
  - [ ] Enterprise GitHub URL
  - [ ] Enterprise OAuth app client ID (or create one)
  - [ ] Enterprise Copilot API endpoint
  - [ ] Token exchange endpoint
- [ ] **Consider**: Block public Copilot API at firewall (optional, for enforcement)
- [ ] **Document incident** for compliance audit trail

## Required Information from Platform Team

Need these before implementation can start:

### Enterprise GitHub Details
- [ ] GitHub Enterprise type: □ Cloud  □ Server
- [ ] Enterprise URL: `_______________________________`
- [ ] Copilot tier: □ Business  □ Enterprise

### OAuth Application
- [ ] Create OAuth app in enterprise GitHub:
  - App name: `PR Agent`
  - Homepage URL: `https://github.com/yourcompany/pr-agent`
  - Callback URL: `http://127.0.0.1` (for device flow)
  - Scopes: `read:user`, `copilot`
- [ ] Client ID: `_______________________________`
- [ ] Note: Do NOT need client secret (device flow doesn't use it)

### API Endpoints
- [ ] Enterprise API base: `_______________________________`
  - Default pattern: `https://github.yourcompany.com/api/v3`
- [ ] Device code URL: `_______________________________`
  - Default pattern: `https://github.yourcompany.com/login/device/code`
- [ ] Token URL: `_______________________________`
  - Default pattern: `https://github.yourcompany.com/login/oauth/access_token`
- [ ] Copilot token exchange URL: `_______________________________`
  - Default pattern: `https://github.yourcompany.com/api/v3/copilot_internal/v2/token`
- [ ] Copilot API base: `_______________________________`
  - May be same as public: `https://api.githubcopilot.com`
  - Or enterprise-specific: `https://copilot-proxy.yourcompany.com`

### Network/Security
- [ ] Proxy required? □ Yes  □ No
  - If yes, proxy URL: `_______________________________`
- [ ] VPN required? □ Yes  □ No
- [ ] SSL/TLS requirements:
  - [ ] Use system CA certificates (standard)
  - [ ] Use custom CA certificate (self-signed)
  - [ ] Disable SSL verification (not recommended)

## Week 1: Implementation

### Day 1-2: Configuration Layer
- [ ] Add enterprise config fields to `src/config.py`
- [ ] Add environment variable mappings
- [ ] Create `Config.for_enterprise()` helper method
- [ ] Update default config file template
- [ ] Write tests for config loading

### Day 3-4: Authentication Layer
- [ ] Refactor `src/copilot_auth.py` to accept config
- [ ] Remove hardcoded constants
- [ ] Make endpoints instance variables
- [ ] Add SSL verification control
- [ ] Update all methods to use instance variables

### Day 5: Client & CLI Updates
- [ ] Add SSL verification to `src/llm_client.py`
- [ ] Update CLI to pass config to authenticator
- [ ] Update CLI to pass config to LLM client
- [ ] Run existing tests to ensure backward compatibility
- [ ] Manual testing with mock endpoints

## Week 2: Documentation & Testing

### Day 1-2: Documentation
- [ ] Create `docs/ENTERPRISE_SETUP.md`
- [ ] Update `README.md` with enterprise section
- [ ] Update `CLAUDE.md` with security notes
- [ ] Create example enterprise config file
- [ ] Write migration guide for existing users

### Day 3-4: Testing
- [ ] Write enterprise config tests
- [ ] Write enterprise auth tests
- [ ] Test backward compatibility (public Copilot still works)
- [ ] Test with environment variables
- [ ] Test with config file
- [ ] Test SSL verification toggle

### Day 5: Pre-deployment Validation
- [ ] Code review
- [ ] Security review
- [ ] Test with real enterprise endpoints (if available)
- [ ] Verify no public API calls in network logs
- [ ] Update CHANGELOG

## Week 3: Rollout

### Day 1-2: Internal Testing
- [ ] Deploy to development environment
- [ ] Test with 2-3 volunteer developers
- [ ] Monitor network traffic
- [ ] Verify enterprise endpoints being used
- [ ] Gather feedback
- [ ] Fix any issues found

### Day 3: Team Rollout
- [ ] Announce to team via Slack/email
- [ ] Share setup guide
- [ ] Offer setup help (office hours?)
- [ ] Create FAQ from common questions
- [ ] Monitor for issues

### Day 4-5: Organization Rollout
- [ ] Broader announcement
- [ ] Self-service documentation available
- [ ] Monitor adoption
- [ ] Collect feedback
- [ ] Plan for mandatory migration (if needed)

## Post-Rollout (Ongoing)

### Monitoring
- [ ] Set up logging for endpoint usage
- [ ] Monitor for public API calls (should be zero)
- [ ] Track adoption rate
- [ ] Collect user feedback

### Compliance
- [ ] Document fix in compliance audit trail
- [ ] Update security documentation
- [ ] Review with legal (if needed for GDPR/SOC2)
- [ ] Schedule periodic audits

### Enforcement (Optional)
- [ ] Remove public Copilot fallback from code
- [ ] Make enterprise config required
- [ ] Block public Copilot API at firewall
- [ ] Update CI/CD to enforce enterprise config

## Success Criteria

Fix is complete when:
- [ ] No pr-agent network calls to `api.githubcopilot.com` (public)
- [ ] All calls go to enterprise endpoints
- [ ] At least 90% of active users migrated
- [ ] Documentation complete and accessible
- [ ] Security team sign-off obtained
- [ ] Compliance requirements met

## Rollback Plan

If issues discovered during rollout:
1. **Revert code changes** (git revert)
2. **Reinstall previous version** (pip install pr-agent==<previous>)
3. **Clear enterprise tokens** (rm -rf ~/.config/pr-agent/copilot)
4. **Communicate to team** about rollback
5. **Fix issues** before attempting again

## Communication Templates

### Kickoff Email (Send to Security Team)
```
Subject: URGENT: pr-agent data leakage issue - need enterprise Copilot credentials

Hi Security Team,

We've identified a data leakage issue in our pr-agent tool. It's currently
using public GitHub Copilot APIs, which means company source code has been
sent to public endpoints.

Impact: ~3 weeks of PR data
Risk: Medium-High (code exposure, compliance)
Fix timeline: 3 weeks

We need the following to implement the fix:
1. Enterprise OAuth app client ID
2. Enterprise Copilot API endpoints
3. Approval to proceed with migration plan

I've attached:
- SECURITY_ISSUE_SUMMARY.md (impact assessment)
- SECURITY_FIX_PLAN.md (detailed fix plan)
- SECURITY_CHECKLIST.md (this checklist)

Can we schedule a meeting this week to discuss?

Thanks,
[Your name]
```

### Team Announcement (After Fix Ready)
```
Subject: pr-agent now uses enterprise Copilot - action required

Hi team,

Good news! We've updated pr-agent to use our enterprise Copilot endpoints,
ensuring company code stays within our infrastructure.

ACTION REQUIRED:
1. Clear old tokens: rm -rf ~/.config/pr-agent/copilot
2. Update config: [link to setup guide]
3. Re-authenticate when you next use pr-agent

Setup guide: [link]
Need help? [link to support channel]

Thanks!
```

## Notes

- Keep this checklist updated as work progresses
- Check off items as completed
- Add notes on any blockers or issues
- Share progress weekly with stakeholders

---

**Priority**: 🔴 CRITICAL
**Owner**: [Your name]
**Security Contact**: [Security team contact]
**Target Completion**: [Date 3 weeks from now]
