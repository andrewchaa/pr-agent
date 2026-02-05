# PR Agent

Automated GitHub pull request creation using GitHub Copilot (Claude Haiku 4.5).

PR Agent is a CLI tool that analyzes your code changes and generates intelligent, comprehensive PR descriptions using Claude Haiku 4.5 via GitHub Copilot. It extracts ticket numbers from branch names, prompts you for context, and creates well-structured pull requests on GitHub.

## Features

- **Claude Haiku 4.5 via GitHub Copilot**: Uses enterprise-grade LLM (requires Copilot subscription)
- **Intelligent PR Descriptions**: Generates comprehensive PR descriptions based on code changes
- **Smart Ticket Extraction**: AI-powered extraction handles any branch naming convention (regex → AI → manual fallback)
- **Auto-Detect Base Branch**: Automatically detects default branch (main, master, develop) - no configuration needed
- **Git Integration**: Analyzes diffs, changed files, and commit messages
- **GitHub CLI**: Seamlessly creates PRs using `gh` command
- **Customizable Templates**: Configure PR sections to match your workflow
- **Preview Mode**: Review generated content before creating PR
- **Draft PR Support**: Create draft PRs for work-in-progress

## Prerequisites

Before using PR Agent, ensure you have:

1. **Python 3.10+** installed
2. **GitHub Copilot subscription** (individual or enterprise)
3. **GitHub account** - You'll authenticate via OAuth device flow on first run

**Note**: No manual token setup needed! The tool handles authentication automatically.

## Installation

```bash
# Clone or navigate to the pr-agent directory
cd /Users/youngho.chaa/github/pr-agent

# Install in development mode
pip install -e .

# Or install for production
pip install .
```

## Quick Start

1. Make some code changes in a git repository
2. **Commit your changes** to a feature branch (preferably with a ticket number in the name)
   ```bash
   git add .
   git commit -m "Your commit message"
   # Optional: push your changes
   git push -u origin your-branch-name
   ```
3. Run PR Agent:
   ```bash
   pr-agent create
   ```
4. **First run only**: Authenticate with GitHub Copilot
   - Visit the URL shown (e.g., `github.com/login/device`)
   - Enter the device code displayed
   - Authorize the application
   - Token is cached for future use
5. Answer the prompt about your change purpose
6. Review the generated PR preview
7. Confirm to create the PR

**Note:** You must commit your changes BEFORE running pr-agent. The tool analyzes committed changes, not uncommitted files.

## Usage

### Basic Usage

Create a PR with default settings:

```bash
pr-agent create
```

### Specify Base Branch

```bash
pr-agent create --base-branch develop
```

### Preview Without Creating

```bash
pr-agent create --dry-run
```

### Create Draft PR

```bash
pr-agent create --draft
```

### Typical Workflow

PR Agent works with **committed changes only**. Here are two common workflows:

**Workflow 1: Commit first, then create PR**
```bash
# 1. Make your changes
vim myfile.py

# 2. Commit them
git add .
git commit -m "Implement new feature"

# 3. Run pr-agent (it will push if needed)
pr-agent create
```

**Workflow 2: Commit and push, then create PR**
```bash
# 1. Make changes and commit
git add .
git commit -m "Fix bug in processor"

# 2. Push to remote
git push -u origin my-feature-branch

# 3. Run pr-agent
pr-agent create
# ✓ Works! PR Agent analyzes your committed changes
```

**What doesn't work:**
```bash
# ✗ This won't work - changes not committed
vim myfile.py
pr-agent create
# Error: No commits found
```

### Open PR in Browser

```bash
pr-agent create --web
```

### Use Custom Model

The model is configured to use Claude Haiku 4.5 via GitHub Copilot and cannot be changed at runtime.

### Use Custom Config File

```bash
pr-agent create --config ~/my-config.yaml
```

## Configuration

PR Agent supports configuration through multiple sources (in order of precedence):

1. **Command-line arguments** (highest priority)
2. **Config file**: `~/.config/pr-agent/config.yaml`
3. **Environment variables**
4. **Defaults** (lowest priority)

### Create Default Config File

```bash
pr-agent init-config
```

This creates `~/.config/pr-agent/config.yaml` with default settings.

### Configuration Options

```yaml
# Model settings
model: "claude-haiku-4.5"
copilot_api_base: "https://api.githubcopilot.com"
copilot_timeout: 60

# Authentication (optional)
# Token directory for cached credentials (default: ~/.config/pr-agent/copilot)
# copilot_token_dir: "/custom/path/to/tokens"

# Git settings
default_base_branch: "main"
ticket_pattern: "STAR-(\\d+)"

# LLM settings
max_diff_tokens: 8000
```

### Environment Variables

Configuration options can be set via environment variables with the `PR_AGENT_` prefix:

```bash
export PR_AGENT_BASE_BRANCH="develop"
export PR_AGENT_COPILOT_TOKEN_DIR="/custom/path"
```

## Branch Naming Convention

PR Agent uses **intelligent ticket extraction** with a two-step approach:

### Extraction Methods

1. **Regex Pattern Matching** (fast) - Tries pattern matching first
2. **AI Extraction** (flexible) - If regex fails, uses LLM to intelligently extract the ticket
3. **Manual Input** (fallback) - Prompts you to enter the ticket number

### Supported Branch Name Formats

PR Agent handles virtually any branch naming convention! Examples:

**Standard formats:**
- `feature/STAR-12345-add-feature`
- `STAR-999-bugfix`
- `bugfix/STAR-456-fix-memory-leak`

**Variations the AI can handle:**
- `star-422270-test` (lowercase)
- `feature_star_123_something` (underscores)
- `bugfix-with-star-789-somewhere` (ticket in middle)
- `star123feature` (no separators)
- `my-feature-with-STAR-999` (any position)

**Note:**
- Regex extraction is **case-insensitive** and normalizes to uppercase (e.g., `star-123` → `STAR-123`)
- AI extraction is extremely flexible and can find tickets in unconventional branch names
- Default pattern: `STAR-(\d+)` (customizable in config)

The AI extraction means you don't need to follow strict branch naming rules!

## How It Works

1. **Validation**: Checks for git repo and GitHub CLI authentication
2. **Copilot Authentication**:
   - Checks for cached Copilot token
   - If not found, triggers OAuth device flow
   - User authorizes via browser
   - Token cached for ~2 hours
3. **Information Gathering**:
   - Extracts current branch name
   - Intelligently parses ticket number (regex → AI → manual)
   - Retrieves git diff and changed files
   - Prompts user for change purpose
4. **AI Generation**:
   - Generates PR title using ticket number and user intent
   - Analyzes code changes to answer template questions
   - Creates comprehensive PR description
5. **Review & Create**:
   - Shows preview of generated PR
   - Pushes branch if needed
   - Creates PR on GitHub

## Troubleshooting

### Error: Not in a git repository

Make sure you're running the command from within a git repository.

### Error: GitHub CLI not authenticated

Run `gh auth login` to authenticate with GitHub.

### Error: Copilot authentication failed

PR Agent uses OAuth device flow for authentication. If you see this error:

1. **First time users**: The device flow will trigger automatically
   ```bash
   pr-agent create
   # Follow the on-screen instructions
   ```

2. **Token expired**: Clear cached tokens and re-authenticate
   ```bash
   rm -rf ~/.config/pr-agent/copilot
   pr-agent create
   ```

3. **Verify Copilot subscription**:
   - Visit https://github.com/settings/copilot
   - Ensure you have an active subscription
   - Check that API access is enabled

4. **Device flow steps**:
   - Visit the URL shown (e.g., `github.com/login/device`)
   - Enter the 8-character code displayed
   - Click "Authorize"
   - Return to terminal to continue

### Error: Base branch 'main' not found

PR Agent **auto-detects** your repository's default branch. If you see this error:

1. **Let PR Agent detect it automatically** (recommended):
   ```bash
   pr-agent create
   # It will auto-detect: master, main, develop, etc.
   ```

2. **Manually specify the base branch**:
   ```bash
   pr-agent create --base-branch master
   ```

3. **Update your config file** to set a different default:
   ```yaml
   # ~/.config/pr-agent/config.yaml
   default_base_branch: "master"  # or develop, etc.
   ```

The error message will suggest available branches in your repository.

### Empty or poor quality PR descriptions

- Ensure your git diff contains meaningful changes
- Provide a clear description when prompted for change purpose
- Try increasing `max_diff_tokens` in config for complex changes

### PR creation fails

- Ensure your branch is up to date with the base branch
- Check that you have push permissions to the repository
- Verify GitHub CLI is properly authenticated with `gh auth status`

## Development

### Project Structure

```
pr-agent/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Module entry point
│   ├── cli.py                # Main CLI interface
│   ├── config.py             # Configuration management
│   ├── copilot_auth.py       # OAuth device flow authenticator
│   ├── git_operations.py     # Git interactions
│   ├── github_operations.py  # GitHub CLI wrapper
│   ├── llm_client.py         # GitHub Copilot API client
│   ├── pr_generator.py       # PR generation logic
│   ├── prompts.py            # LLM prompt templates
│   └── exceptions.py         # Custom exceptions
├── tests/                    # Test suite
├── examples/                 # Example configurations
└── pyproject.toml           # Project configuration
```

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

## Examples

### Example 1: Standard Branch Format

```bash
# On branch: feature/STAR-12345-add-oauth
$ pr-agent create

✓ Git repository detected
✓ GitHub CLI authenticated
✓ Copilot API key configured

Current branch: feature/STAR-12345-add-oauth

✓ Detected ticket number (regex): STAR-12345

What is the purpose of this change?
> Add OAuth 2.0 authentication flow for third-party integrations

[Generating PR description...]

PR Preview:
Title: STAR-12345: Add OAuth 2.0 authentication flow

Create this pull request? [Y/n]: y
✓ Pull request created successfully!
URL: https://github.com/org/repo/pull/123
```

### Example 1b: Unconventional Branch Name (AI Extraction)

```bash
# On branch: bugfix_with_star_422270_somewhere
$ pr-agent create

✓ Git repository detected
✓ GitHub CLI authenticated
✓ Copilot API key configured

Current branch: bugfix_with_star_422270_somewhere

Regex pattern didn't match. Trying AI extraction...
[Analyzing branch name with AI...]
✓ Detected ticket number (AI): STAR-422270

What is the purpose of this change?
> Fix memory leak in background processor

[Generating PR description...]
```

### Example 2: Bug Fix with Custom Base

```bash
$ pr-agent create --base-branch develop --draft

[Similar flow, creates draft PR against develop branch]
```

### Example 3: Dry Run

```bash
$ pr-agent create --dry-run

[Shows preview without creating PR]
Dry run mode - PR not created
```

## Advanced Usage

### Custom Ticket Patterns

For JIRA-style tickets:
```yaml
ticket_pattern: "([A-Z]+-\\d+)"
```

For Linear tickets:
```yaml
ticket_pattern: "(ENG-\\d+)"
```

### Repository-Specific Configuration

Create `.pr-agent.yaml` in your repository root for project-specific settings.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above

## Acknowledgments

- Built with [GitHub Copilot](https://github.com/features/copilot) for enterprise-grade LLM access
- Uses [Claude Haiku 4.5](https://www.anthropic.com/claude) by Anthropic
- Powered by [GitHub CLI](https://cli.github.com/)
