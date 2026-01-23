# Base Branch Auto-Detection - Implementation Summary

## Problem
User got error: `Base branch 'main' not found` because their repository uses `master` instead of `main`.

## Solution Implemented

### 1. Automatic Base Branch Detection (git_operations.py)

Added three new methods:

#### `get_default_branch()` 
Intelligently detects the repository's default branch:
1. First tries to read from `origin/HEAD` (most reliable)
2. Falls back to checking common branch names: `main`, `master`, `develop`, `development`
3. Returns the first one found

#### `branch_exists(branch_name)`
Checks if a branch exists locally or remotely:
- Searches local branches
- Searches remote branches (origin/*)
- Returns True/False

#### `get_available_branches()`
Returns a sorted list of all available branches (local + remote)

### 2. Improved Error Messages (git_operations.py)

Enhanced `get_diff()` to provide helpful suggestions when base branch not found:

**Before:**
```
Error: Base branch 'main' not found. Please specify a valid base branch.
```

**After:**
```
Base branch 'main' not found.

Try one of these instead: master, develop
Example: pr-agent create --base-branch master
```

Or if no common branches exist:
```
Base branch 'main' not found.

Available branches: feature-1, feature-2, bugfix-1 (and 5 more)
```

### 3. Auto-Detection in CLI (cli.py)

Added logic in the `create` command to:
1. Auto-detect base branch after initialization
2. Show informative message when auto-detected branch differs from config
3. Automatically use detected branch if config default doesn't exist

**Example output:**
```bash
✓ Git repository detected
✓ GitHub CLI authenticated
✓ Ollama service available
✓ Model 'qwen2.5:3b' available

Auto-detected base branch: master (instead of default 'main')

Current branch: star-422270-test
```

Or with warning:
```bash
Base branch 'main' not found. Using 'master' instead.
```

### 4. Documentation Updates (README.md)

- Added **Auto-Detect Base Branch** to features list
- New troubleshooting section: "Error: Base branch 'main' not found"
- Three solutions provided:
  1. Let PR Agent auto-detect (recommended)
  2. Manually specify with `--base-branch`
  3. Update config file

## How It Works

### Detection Flow

```
User runs: pr-agent create
          ↓
   Load config (default: "main")
          ↓
   Initialize git operations
          ↓
   Try auto-detection:
   1. Check origin/HEAD
   2. Try: main → master → develop
          ↓
   Branch found? 
          ↓
   ✓ YES: Use detected branch
          Auto-detected: master
          ↓
   Continue with PR creation
```

### Fallback Strategy

1. **Config specified**: Use `default_base_branch` from config
2. **CLI flag**: Use `--base-branch` argument (overrides everything)
3. **Auto-detect**: Try to find default branch automatically
4. **Error**: Show helpful message with available branches

## User Experience

### Scenario 1: Repository uses `master`

**Before fix:**
```bash
$ pr-agent create
Error: Base branch 'main' not found.
# User has to figure out the right branch
```

**After fix:**
```bash
$ pr-agent create
Auto-detected base branch: master (instead of default 'main')
✓ Detected ticket number (regex): STAR-422270
# Just works!
```

### Scenario 2: Repository uses `develop`

**After fix:**
```bash
$ pr-agent create
Auto-detected base branch: develop (instead of default 'main')
✓ Detected ticket number (regex): STAR-422270
# Just works!
```

### Scenario 3: Weird base branch

If auto-detection fails, user gets helpful error:
```bash
$ pr-agent create
Error: Base branch 'main' not found.

Available branches: production, staging, feature-1
Example: pr-agent create --base-branch production
```

## Benefits

1. **Zero Configuration**: Works out-of-the-box for most repositories
2. **Smart Fallbacks**: Tries multiple methods to find the right branch
3. **Clear Feedback**: User knows what's happening
4. **Helpful Errors**: Suggests solutions when auto-detection fails
5. **Respects User Choice**: Manual `--base-branch` flag always takes precedence

## Testing

Run the test script:
```bash
python test_base_branch_detection.py
```

Example output:
```
Base Branch Detection Test
============================================================

✓ Initialized in git repository

1. Auto-detecting default branch...
   ✓ Detected: master

2. Checking common branches:
   ✓ main: exists
   ✓ master: exists
   ✗ develop: not found

3. Available branches in repository:
   - main
   - master

4. Testing error message with non-existent branch:
   Error message preview:
   | Base branch 'nonexistent-branch' not found.
   | 
   | Try one of these instead: main, master
   | Example: pr-agent create --base-branch main
```

## Edge Cases Handled

✅ Repository with `main` only
✅ Repository with `master` only  
✅ Repository with `develop` as default
✅ Repository with custom default branch
✅ Repository without any common branches (shows available)
✅ User explicitly sets `--base-branch` (respects user choice)
✅ Config file sets different default (uses config if valid)

## Future Enhancements

- Remember user's last successful base branch per repository
- Support for GitLab/Bitbucket default branch conventions
- Interactive selection from available branches
