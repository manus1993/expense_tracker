# Expense Tracker
Income / Outcome WebApp

## Overview



## Launch

This project now uses [UV](https://docs.astral.sh/uv/) for dependency management.

### Quick Start with cmd.sh

The project includes a convenient script for common development tasks:

```bash
# First time setup
./cmd.sh setup

# Start development server
./cmd.sh start

# Format code with ruff
./cmd.sh format

# Run quality checks (ruff + mypy)
./cmd.sh qa

# Run tests with coverage
./cmd.sh test

# Start production server
./cmd.sh start-prod
```

### Manual UV Commands

Create virtual environment and install dependencies:

```bash
uv sync
```

This command automatically:
- Creates a virtual environment (if one doesn't exist)
- Installs all project dependencies from `pyproject.toml`
- Installs development dependencies

Run the development server:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or run any command in the UV environment:

```bash
uv run python -m app.main
```
