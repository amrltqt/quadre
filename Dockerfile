FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install high-quality fonts inside the image for consistent rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    fonts-inter \
    fonts-noto-core \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

# No font environment override required; renderer auto-selects high-quality fonts (Inter → Noto → DejaVu)

WORKDIR /app

# ajouter ton script
COPY . /app

# installe les deps dans .venv avec uv
RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "-m", "nada.main"]
