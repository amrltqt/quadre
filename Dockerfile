FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# installer une fonte pour Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ajouter ton script
COPY . /app

# installe les deps dans .venv avec uv
RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "-m", "ezp.main"]
