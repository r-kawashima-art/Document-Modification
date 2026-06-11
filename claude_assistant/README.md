# Claude Slack Agent for Document Automation

A Slack integration agent that receives document generation requests from Slack and forwards them to Claude Cowork for processing.

## Features

- Listen for `@Claude Assistant` mentions in Slack
- Forward document generation requests to Claude Cowork
- Automatic status tracking (todo → done)
- Support for local and Google Drive file storage
- Batch document generation with partial failure handling

## Installation

```bash
uv sync
```

## Configuration

See `settings/example_config.json` for configuration template.

## Testing

```bash
# All tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/

# With coverage
uv run pytest --cov=src
```

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Format code
uv run black src tests

# Type checking
uv run mypy src

# Lint
uv run ruff check src
```
