# Pre-commit Hooks Guide

This guide explains how to use pre-commit hooks to maintain code quality and consistency in this FastAPI project.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Available Hooks](#available-hooks)
- [Usage](#usage)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

**Pre-commit hooks** are automated scripts that run before each git commit to check your code for common issues. They help maintain code quality, enforce coding standards, and catch bugs early in the development process.

### Benefits

- **Automated Code Quality**: Automatically format code, sort imports, and catch common issues
- **Consistent Style**: Enforce consistent code style across the entire team
- **Early Bug Detection**: Catch potential bugs, security issues, and type errors before commit
- **Reduced Review Time**: Clean up minor issues automatically, so reviewers can focus on logic
- **Team Productivity**: Spend less time on style discussions and more time on features

### How It Works

1. You make changes to your code
2. You run `git commit`
3. Pre-commit hooks automatically run checks on staged files
4. If all checks pass, the commit proceeds
5. If any check fails, the commit is blocked and you see what needs to be fixed
6. Some hooks auto-fix issues (like formatting), others require manual fixes

## Installation

### 1. Install Dependencies

First, ensure all required packages are installed:

```bash
# Install all development dependencies (including pre-commit)
pip install -r requirements.txt
```

### 2. Install Pre-commit Hooks

Install the git hook scripts:

```bash
pre-commit install
```

This creates git hooks in `.git/hooks/` that will run automatically on `git commit`.

### 3. Verify Installation

Check that pre-commit is installed correctly:

```bash
pre-commit --version
```

You should see the version number (e.g., `pre-commit 3.5.0`).

## Available Hooks

This project uses the following pre-commit hooks:

### 1. **General File Checks** (pre-commit-hooks)

Standard checks for common issues:

- **check-added-large-files**: Prevents accidentally committing large files (>500KB)
- **check-case-conflict**: Detects files that would conflict on case-insensitive filesystems
- **check-merge-conflict**: Checks for unresolved merge conflict markers
- **debug-statements**: Detects leftover debugger imports and `breakpoint()` calls
- **check-json**: Validates JSON file syntax
- **check-toml**: Validates TOML file syntax (pyproject.toml, etc.)
- **check-yaml**: Validates YAML file syntax (docker-compose.yml, etc.)
- **detect-private-key**: Prevents committing private keys
- **end-of-file-fixer**: Ensures files end with a newline
- **trailing-whitespace**: Removes trailing whitespace
- **requirements-txt-fixer**: Sorts requirements.txt alphabetically
- **check-executables-have-shebangs**: Ensures executable scripts have shebang lines
- **check-shebang-scripts-are-executable**: Ensures scripts with shebangs are executable

### 2. **Black** - Code Formatting

Automatically formats Python code to be consistent and readable.

- Line length: 100 characters
- Formats code according to PEP 8 style guide
- Auto-fixes formatting issues

### 3. **isort** - Import Sorting

Automatically sorts and organizes Python imports.

- Compatible with Black formatting
- Separates standard library, third-party, and first-party imports
- Auto-fixes import order

### 4. **Ruff** - Linting

Fast Python linter that checks for common errors and code quality issues.

- Checks for unused imports, undefined names, and syntax errors
- Enforces code quality rules (pycodestyle, pyflakes, flake8-bugbear)
- Auto-fixes many issues when possible

### 5. **mypy** - Type Checking

Static type checker for Python to catch type-related bugs.

- Checks type hints for correctness
- Helps catch bugs before runtime
- Skips test files and alembic migrations

### 6. **Bandit** - Security Linting

Scans Python code for common security issues.

- Detects SQL injection vulnerabilities
- Checks for hardcoded passwords and secrets
- Identifies insecure cryptographic practices
- Skips test files (where security checks are less relevant)

### 7. **SQLFluff** - SQL Linting

Lints SQL files (primarily for Alembic migrations).

- Enforces PostgreSQL dialect
- Checks SQL syntax and style
- Only runs on `.sql` files in `alembic/versions/`

### 8. **Hadolint** - Dockerfile Linting

Lints Dockerfiles for best practices.

- Checks for common Docker anti-patterns
- Ensures efficient image builds
- Ignores some non-critical warnings

### 9. **yamllint** - YAML Linting

Lints YAML files for syntax and style issues.

- Validates docker-compose.yml and other YAML files
- Checks indentation and formatting
- Allows lines up to 120 characters

## Usage

### Automatic Checks on Commit

Pre-commit hooks run automatically when you commit:

```bash
git add .
git commit -m "Your commit message"

# Hooks run automatically here!
# If any fail, the commit is blocked
```

### Manual Run on All Files

Run all hooks on all files (useful for initial setup or after updating hooks):

```bash
pre-commit run --all-files
```

### Run Specific Hook

Run a single hook:

```bash
# Run only Black formatting
pre-commit run black --all-files

# Run only Ruff linting
pre-commit run ruff --all-files

# Run only mypy type checking
pre-commit run mypy --all-files
```

### Run on Specific Files

Run hooks on specific files:

```bash
pre-commit run --files app/models/user.py app/api/v1/users.py
```

### Skip Hooks (Not Recommended)

If you absolutely must skip hooks (use sparingly!):

```bash
git commit --no-verify -m "Emergency fix"
```

### Update Hooks

Update all pre-commit hooks to their latest versions:

```bash
pre-commit autoupdate
```

## Configuration

### Main Configuration File

Pre-commit hooks are configured in [.pre-commit-config.yaml](../.pre-commit-config.yaml) at the project root.

### Tool-Specific Configuration

Individual tools are configured in [pyproject.toml](../pyproject.toml):

```toml
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']

[tool.isort]
profile = "black"
line_length = 100

[tool.ruff]
line-length = 100
select = ["E", "W", "F", "I", "C", "B"]

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true

[tool.bandit]
exclude_dirs = ["tests", ".venv", "alembic"]
```

### Customizing Hooks

To customize hook behavior, edit `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/psf/black
  rev: 23.12.1
  hooks:
    - id: black
      args: ['--line-length=100']  # Modify arguments here
```

After modifying the config, reinstall hooks:

```bash
pre-commit install
```

## Troubleshooting

### Hook Fails with "command not found"

**Problem**: A hook fails because a command isn't found.

**Solution**: Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
pre-commit clean
pre-commit install
```

### Hooks Are Slow

**Problem**: Pre-commit hooks take a long time to run.

**Solution**:

1. Hooks only run on staged files by default (fast)
2. Use `--no-verify` for emergency commits (not recommended)
3. Consider disabling slower hooks (like mypy) if needed

### Black and Another Tool Conflict

**Problem**: Black reformats code, but another tool complains about it.

**Solution**: This shouldn't happen as isort uses `profile = "black"` for compatibility. If it does:

1. Check `.pre-commit-config.yaml` for conflicting rules
2. Ensure all tools have compatible line length settings (100)

### Mypy Fails on Valid Code

**Problem**: mypy reports errors on code that works fine.

**Solution**:

1. Add type hints where mypy expects them
2. Use `# type: ignore` comments for false positives
3. Update `pyproject.toml` mypy configuration if needed

### Can't Commit Due to Hook Failures

**Problem**: Hooks fail and you can't commit.

**Solution**:

1. **Read the error message** - it usually tells you exactly what's wrong
2. **Auto-fixable issues**: Some hooks (black, isort, ruff) auto-fix issues. Just run `git add .` and try committing again
3. **Manual fixes required**: For issues like type errors or security problems, fix the code manually
4. **Last resort**: Use `git commit --no-verify` (but fix the issues before pushing!)

### Hook Installation Fails

**Problem**: `pre-commit install` fails.

**Solution**:

```bash
# Ensure git is initialized
git init

# Ensure Python and pip are working
python --version
pip --version

# Reinstall pre-commit
pip install --upgrade pre-commit
pre-commit install --install-hooks
```

## Best Practices

### 1. Install Hooks Immediately

When cloning the repository, install hooks right away:

```bash
git clone <repository-url>
cd <repository>
pip install -r requirements.txt
pre-commit install
```

### 2. Run Hooks Before Committing

Even though hooks run automatically, you can run them manually to catch issues early:

```bash
pre-commit run --all-files
```

### 3. Commit Logical Units

Make small, focused commits. This makes hook failures easier to fix:

```bash
# Good: Small focused commits
git add app/models/user.py
git commit -m "Add email validation to User model"

# Less ideal: Large commits with many changes
git add .
git commit -m "Update everything"
```

### 4. Fix Issues, Don't Skip Hooks

Always fix the issues hooks identify rather than using `--no-verify`:

```bash
# Bad: Skipping hooks hides problems
git commit --no-verify -m "Quick fix"

# Good: Fix the issues
# (Let hooks run and fix what they identify)
git add .
git commit -m "Fix validation logic"
```

### 5. Update Hooks Regularly

Keep hooks up to date for the latest features and bug fixes:

```bash
# Run this monthly or when updating dependencies
pre-commit autoupdate
git add .pre-commit-config.yaml
git commit -m "Update pre-commit hooks"
```

### 6. Review Auto-fixed Changes

Some hooks (black, isort) auto-fix files. Review these changes before committing:

```bash
git add .
git commit -m "Add new feature"

# If hooks auto-fix files:
# 1. Review changes with: git diff
# 2. Stage auto-fixed files: git add .
# 3. Commit again: git commit -m "Add new feature"
```

### 7. Add Type Hints Gradually

mypy can be overwhelming if you're not used to type hints. Add them gradually:

```python
# Without type hints (mypy might skip or complain)
def get_user(user_id):
    return db.query(User).get(user_id)

# With type hints (mypy can verify correctness)
def get_user(user_id: UUID) -> User | None:
    return db.query(User).get(user_id)
```

### 8. Use Comments for Edge Cases

If you need to skip a specific check, document why:

```python
# Skip security check - this is demo code, not production
api_key = "hardcoded-key-for-testing"  # nosec B105

# Skip type check - third-party library has incorrect types
result = external_lib.process(data)  # type: ignore
```

### 9. Team Consistency

Ensure all team members have hooks installed:

```bash
# Add to your team's onboarding documentation
git clone <repository>
cd <repository>
pip install -r requirements.txt
pre-commit install  # Essential step!
```

### 10. CI Integration

Pre-commit hooks should also run in CI to catch issues from commits without hooks:

```yaml
# .github/workflows/ci.yml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

## Hook Reference

Quick command reference:

```bash
# Installation
pre-commit install                    # Install git hooks
pre-commit uninstall                  # Remove git hooks

# Running hooks
pre-commit run --all-files           # Run all hooks on all files
pre-commit run <hook-id>             # Run specific hook
pre-commit run --files <file>        # Run on specific files

# Maintenance
pre-commit autoupdate                # Update hook versions
pre-commit clean                     # Clean cached environments
pre-commit gc                        # Garbage collect old environments

# Debugging
pre-commit run --verbose             # Show detailed output
pre-commit run --show-diff-on-failure  # Show diffs when hooks fail

# Skip hooks (use sparingly!)
git commit --no-verify               # Skip all pre-commit hooks
```

## Hook Execution Order

Hooks run in this order (as configured in `.pre-commit-config.yaml`):

1. **General checks** (large files, merge conflicts, private keys, etc.)
2. **Black** (code formatting)
3. **isort** (import sorting)
4. **Ruff** (linting and quick fixes)
5. **mypy** (type checking)
6. **Bandit** (security scanning)
7. **SQLFluff** (SQL linting)
8. **Hadolint** (Dockerfile linting)
9. **yamllint** (YAML linting)

This order ensures that code is formatted before being linted, and critical issues are caught early.

## Additional Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Black Documentation](https://black.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- Project README: [../README.md](../README.md)
- Development Guide: [DEVELOPMENT.md](DEVELOPMENT.md)
