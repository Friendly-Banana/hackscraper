FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# install dependencies
COPY pyproject.toml uv.lock /app/
RUN uv sync --locked --no-dev --extra cpu

# copy the project
COPY . /app

CMD uv run --no-sync py4web run apps --port=${PORT:-8000} --host=0.0.0.0 --server rocket --watch off --dashboard_mode none