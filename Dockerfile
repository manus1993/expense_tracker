FROM python:3.11.9-slim-bullseye

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables for uv
ENV UV_SYSTEM_PYTHON=1

# Set working directory
WORKDIR /app

# Copy all application files
COPY . .

# Install the project and its dependencies
RUN uv pip install --system --no-cache .

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]