# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Run the CLI
pr-agent create
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cli.py

# Run with coverage
pytest --cov=pr_agent
```

### Code Quality
```bash
# Format code
black pr_agent/

# Lint code
ruff check pr_agent/
```

### Prerequisites for Testing
Ensure these are running/available before testing:
- Ollama service: `ollama serve`
- Model pulled: `ollama pull qwen2.5:3b`
- GitHub CLI authenticated: `gh auth login`

## Architecture

### Core Workflow
PR creation follows this pipeline:
1. **Validation** (cli.py) - Check git repo, GitHub auth, Ollama, model
2. **Ticket Extraction** (cli.py) - Three-tier: regex → AI → manual
3. **Content Generation** (pr_generator.py) - LLM generates title + description sections
4. **GitHub Integration** (github_operations.py) - Push branch + create PR via `gh` CLI

### Component Responsibilities

**cli.py** - Main orchestrator
- Command parsing and user interaction
- Prerequisites validation
- Workflow coordination
- Uses Rich for terminal UI

**config.py** - Multi-source configuration
- Priority: CLI args → config file → env vars → defaults
- Default config: `~/.config/pr-agent/config.yaml`
- Supports repository-specific `.pr-agent.yaml`

**git_operations.py** - Git interactions via GitPython
- Diff and commit retrieval
- Ticket extraction from branch names (regex-based)
- Auto-detect default branch (checks `origin/HEAD`, then common names)
- Validates commits exist (not just diffs)

**github_operations.py** - GitHub CLI wrapper
- All GitHub operations via `gh` command
- Creates PRs with title, body, base branch
- Pushes branches to remote
- Checks authentication status

**llm_client.py** - Ollama API client
- Generates PR content via Ollama REST API
- AI-powered ticket extraction from branch names
- Configurable temperature (0.1 for extraction, 0.7 for creative)
- Context truncation for large diffs (default: 8000 tokens)

**pr_generator.py** - PR content generation
- Generates title (ticket + user intent)
- Generates description sections dynamically based on template
- Retrieves git context (files, commits, diffs)
- Handles empty diffs gracefully
- Maps template sections to appropriate generation methods

**template_parser.py** - PR template parsing
- Reads `.github/pull_request_template.md` from repository
- Parses markdown headers (## or ###) to extract section questions
- Falls back to default sections if template doesn't exist
- Supports multiple template locations (.github, docs)

**prompts.py** - LLM prompt engineering
- All prompt templates for title, sections, ticket extraction
- Controls LLM output format and quality

**exceptions.py** - Custom exception hierarchy
- PRAgentError → GitError/GitHubError/LLMError/ConfigError
- Specific exceptions for validation failures

### Key Design Patterns

**Ticket Extraction (Three-Tier)**
1. Regex pattern matching (fast, case-insensitive, normalizes to uppercase)
2. AI extraction via LLM (flexible, handles unconventional names)
3. Manual user input (fallback)

**Base Branch Auto-Detection**
1. Check `origin/HEAD` symbolic ref
2. Try common names: main → master → develop
3. Use config default
4. Show helpful suggestions on error

**Committed Changes Support**
- Counts commits between branches (not just diff)
- Works with already-pushed commits
- Validates commits exist before proceeding

**Dynamic PR Template Loading**
- Automatically reads `.github/pull_request_template.md` from repository at runtime
- Parses markdown headers (## or ###) to extract section questions
- Falls back to default sections if template doesn't exist
- Supports variable number of sections (not limited to 3)
- Maps sections to generation methods via keywords (why, impact) or position

## Configuration

Configuration sources (highest to lowest priority):
1. CLI arguments
2. Config file (`~/.config/pr-agent/config.yaml`)
3. Environment variables (`PR_AGENT_*`)
4. Hardcoded defaults

Key configurable options:
- `model` - Ollama model name (default: qwen2.5:3b)
- `ollama_base_url` - Ollama API URL
- `default_base_branch` - Base branch for PRs (default: main)
- `ticket_pattern` - Regex for ticket extraction (default: STAR-(\d+))
- `max_diff_tokens` - Token limit for diffs (default: 8000)

Note: PR description sections are now loaded dynamically from `.github/pull_request_template.md` in each repository. The `template.sections` configuration option has been removed.

## Important Behaviors

**Commits Required**
PR Agent requires committed changes. It analyzes commits, not uncommitted files. Always validate commits exist before generating PRs.

**Empty Diff Handling**
The tool handles already-pushed commits by checking commit count instead of relying solely on diffs. Use `allow_empty=True` when retrieving diffs.

**Branch Naming**
Ticket extraction is extremely flexible:
- Regex: case-insensitive, normalizes to uppercase
- AI: handles any format (underscores, middle of name, no separators)
- Manual: always available as fallback

**PR Template Parsing**
PR Agent automatically reads and parses repository-specific PR templates:
- Checks `.github/pull_request_template.md` (and other common locations)
- Extracts section headers from markdown (## or ### level)
- Falls back to default sections if no template exists
- Supports any number of sections (not limited to 3)

**Error Messages**
Provide helpful suggestions when validation fails (e.g., suggest available branches when base branch not found).

## Testing Notes

When writing tests:
- Mock external dependencies (Ollama API, GitHub CLI, git operations)
- Test three-tier ticket extraction flow
- Test base branch auto-detection logic
- Test committed changes validation
- Test configuration precedence
- Test PR template parsing with various markdown formats
- Test fallback to defaults when template doesn't exist
- Test dynamic section generation with variable section counts
