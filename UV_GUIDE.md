# Using UV with Agentic Playground

This project uses [UV](https://github.com/astral-sh/uv) for fast, reliable Python package management.

## What is UV?

UV is an extremely fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip and pip-tools.

## Quick Start

### Install Dependencies

```bash
# Install all dependencies (including dev dependencies)
uv sync

# Install only production dependencies
uv sync --no-dev
```

### Running Python Scripts

```bash
# Run any Python script with UV
uv run python script.py

# Run a module
uv run python -m agentic_playground.examples.simple_conversation

# Run pytest
uv run pytest

# Run with specific arguments
uv run python verify_setup.py
```

### Managing Dependencies

```bash
# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Update all dependencies
uv sync --upgrade
```

### Working with the Virtual Environment

UV automatically creates a `.venv` directory. To activate it manually:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

However, you usually don't need to activate it - just use `uv run`!

### Common Commands

```bash
# Install dependencies
uv sync

# Run the setup verification
uv run python verify_setup.py

# Run tests
uv run pytest tests/ -v

# Run an example
uv run python -m agentic_playground.examples.debate

# Format code with black
uv run black agentic_playground/

# Lint code with ruff
uv run ruff check agentic_playground/

# Run a Python REPL with dependencies available
uv run python
```

## Project Structure

The project configuration is in `pyproject.toml`, which includes:

- **dependencies**: Required packages for running the project
- **dev dependencies**: Packages needed for development (testing, formatting, etc.)
- **project metadata**: Name, version, description, etc.

## Benefits of UV

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Better dependency resolution
3. **Simplicity**: No need to manually manage virtual environments
4. **Modern**: Uses pyproject.toml standard
5. **Caching**: Smart caching for faster repeated installs

## Troubleshooting

### "uv: command not found"

Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Dependencies not found

Run:
```bash
uv sync
```

### Virtual environment issues

Delete `.venv` and reinstall:
```bash
rm -rf .venv
uv sync
```

## Example Workflow

```bash
# Clone the repo and set up
cd agentic-playground
uv sync

# Verify everything works
uv run python verify_setup.py

# Run tests
uv run pytest

# Try an example
uv run python -m agentic_playground.examples.simple_conversation

# Start developing
uv run python my_custom_agent.py
```

## Why UV over pip/poetry/pipenv?

- **Faster**: Orders of magnitude faster than alternatives
- **Simpler**: Fewer commands, less configuration
- **Modern**: Built for the current Python packaging ecosystem
- **Reliable**: Written in Rust with strong dependency resolution
- **Standard**: Uses pyproject.toml like modern Python projects

For more information, visit: https://github.com/astral-sh/uv
