FROM python:3.12-alpine

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Enable bytecode compilation and disable cache for smaller image
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1

# Copy the package manifests
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (creates .venv automatically)
RUN uv sync --frozen --no-dev

# Copy the rest of the application code
COPY . .

# Expose the web server port
EXPOSE 8000

# Run the app via uv
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
