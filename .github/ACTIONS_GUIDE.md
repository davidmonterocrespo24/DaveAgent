# GitHub Actions CI/CD Setup Guide

## Workflows Created

### 1. Code Quality (`code-quality.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Checks:**
- **Flake8**: Python linting for syntax errors and code style
- **Black**: Code formatting verification
- **MyPy**: Static type checking
- **Bandit**: Security vulnerability scanning

**Status Badge:**
```markdown
![Code Quality](https://github.com/davidmonterocrespo24/DaveAgent/workflows/Code%20Quality/badge.svg)
```

### 2. Tests (`tests.yml`)

Runs on every push and pull request.

**Features:**
- Tests on Python 3.10, 3.11, and 3.12
- Tests on Ubuntu, Windows, and macOS
- Coverage report with Codecov integration
- Uses pytest with coverage plugin

**Status Badge:**
```markdown
![Tests](https://github.com/davidmonterocrespo24/DaveAgent/workflows/Tests/badge.svg)
```

### 3. Publish to PyPI (`publish.yml`)

Automatically publishes to PyPI when you create a new GitHub Release.

**Triggers:**
- Runs when a new release is published on GitHub

**Requirements:**
- PyPI API token stored in GitHub Secrets as `PYPI_API_TOKEN`

**Status Badge:**
```markdown
![Publish](https://github.com/davidmonterocrespo24/DaveAgent/workflows/Publish%20to%20PyPI/badge.svg)
```

### 4. Documentation (`docs.yml`)

Automatically updates GitHub Wiki when documentation changes.

**Triggers:**
- Pushes to `main` branch that modify files in `docs/` or `README.md`

**Features:**
- Auto-syncs `docs/DaveAgent.wiki/*.md` to GitHub Wiki
- No manual wiki updates needed

---

## Setup Instructions

### 1. Add PyPI API Token to GitHub Secrets

For the automated PyPI publishing to work:

1. Go to: https://github.com/davidmonterocrespo24/DaveAgent/settings/secrets/actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Your PyPI token (the one starting with `pypi-...`)
5. Click "Add secret"

### 2. Add Status Badges to README.md

Add these badges at the top of your README.md:

```markdown
# CodeAgent

![Code Quality](https://github.com/davidmonterocrespo24/DaveAgent/workflows/Code%20Quality/badge.svg)
![Tests](https://github.com/davidmonterocrespo24/DaveAgent/workflows/Tests/badge.svg)
![PyPI](https://img.shields.io/pypi/v/daveagent-cli)
![Python](https://img.shields.io/pypi/pyversions/daveagent-cli)
![License](https://img.shields.io/github/license/davidmonterocrespo24/DaveAgent)
```

### 3. Enable Actions (if needed)

1. Go to: https://github.com/davidmonterocrespo24/DaveAgent/actions
2. If prompted, click "I understand my workflows, go ahead and enable them"

### 4. Configure Codecov (Optional)

For test coverage reporting:

1. Go to: https://codecov.io/
2. Sign in with GitHub
3. Add your repository
4. Copy the Codecov token
5. Add it to GitHub Secrets as `CODECOV_TOKEN`

---

## How to Use

### Running Code Quality Checks Locally

Before pushing code, run these checks locally:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run flake8
flake8 src --max-complexity=10 --max-line-length=100

# Check formatting
black --check --line-length 100 src

# Fix formatting
black --line-length 100 src

# Type check
mypy src --ignore-missing-imports

# Security check
bandit -r src -ll
```

### Running Tests Locally

```bash
# Run all tests
pytest test/ -v

# Run with coverage
pytest test/ -v --cov=src --cov-report=term --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
```

### Publishing a New Version

The automated way (recommended):

1. Update version in `pyproject.toml` and `setup.py`
2. Commit and push changes
3. Create a new release on GitHub:
   - Go to: https://github.com/davidmonterocrespo24/DaveAgent/releases/new
   - Tag: `v1.0.1` (or your version)
   - Title: `v1.0.1 - Description`
   - Publish release
4. GitHub Actions will automatically build and publish to PyPI

### Updating Documentation

Just commit changes to `docs/DaveAgent.wiki/*.md` and push to `main`. The wiki will update automatically.

---

## Workflow Files Structure

```
.github/
└── workflows/
    ├── code-quality.yml    # Linting and formatting
    ├── tests.yml           # Unit tests
    ├── publish.yml         # PyPI publishing
    └── docs.yml            # Wiki auto-update
```

---

## Troubleshooting

### "Workflow not running"
- Check that the file is in `.github/workflows/`
- Verify the trigger conditions match your action
- Check Actions tab for error messages

### "PyPI publish failed"
- Verify `PYPI_API_TOKEN` secret is set correctly
- Check that the version number is new (not already published)
- Review the workflow run logs

### "Tests failing"
- Run tests locally first: `pytest test/ -v`
- Check Python version compatibility
- Review test output in Actions tab

---

## Next Steps

1. **Add the PyPI token to GitHub Secrets**
2. **Add status badges to README.md**
3. **Commit and push the workflow files**:
   ```bash
   git add .github/workflows/
   git commit -m "Add GitHub Actions CI/CD workflows"
   git push origin main
   ```
4. **Watch the first workflow run** in the Actions tab

---

**Created**: 2024-12-08
**Workflows**: 4 (Code Quality, Tests, Publish, Docs)
**Status**: Ready to use
