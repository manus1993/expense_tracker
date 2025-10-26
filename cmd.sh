#!/bin/bash
set -e  # Exit on error

# Load environment variables if .env.sh exists
if [ -f ".env.sh" ]; then
    source .env.sh
fi

if [ "$1" == "setup" ]; then
    echo "Setting up development environment..."
    uv sync
    echo "✅ Setup complete! Virtual environment created and dependencies installed."
elif [ "$1" == "format" ]; then
    echo "Formatting code..."
    uv run ruff format app
    uv run ruff check --fix app
    echo "✅ Code formatted successfully."
elif [ "$1" == "qa" ]; then
    echo "Running quality assurance checks..."
    uv run ruff check app
    uv run ruff format --check app
    uv run mypy app
    echo "✅ All QA checks passed."
elif [ "$1" == "test" ]; then
    echo "Running tests with coverage..."
    uv run coverage run --source ./app -m pytest --disable-warnings --junit-xml=pytest-report.xml
    uv run coverage xml
    uv run coverage html
    echo "✅ Tests completed. Coverage reports generated."
elif [ "$1" == "start" ]; then
    echo "Starting FastAPI development server..."
    uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
elif [ "$1" == "tag-deploy" ]; then
    if [ $# -ne 2 ]; then
        echo "No tag supplied, expected format: \`./cmd.sh tag-deploy v1.0.0\`"
        exit 1
    fi

    echo "Deploying version $2..."
    echo $2 > ./app/version.txt
    git add ./app/version.txt
    git commit -m "$2"
    git push

    git tag $2
    git push origin $2
    echo "✅ Version $2 deployed successfully."
else
    echo "Unknown command: $1"
    echo ""
    echo "Available commands:"
    echo "  setup      - Set up development environment with UV"
    echo "  format     - Format code with ruff"
    echo "  qa         - Run quality assurance checks (ruff + mypy)"
    echo "  test       - Run tests with coverage reporting"
    echo "  start      - Start FastAPI development server"
    echo "  tag-deploy - Create and deploy a new version tag"
    exit 1
fi
