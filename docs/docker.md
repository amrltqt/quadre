# Docker Usage

The Makefile wraps a Docker image based on `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`.

Build and run
```bash
make build
make run examples/declarative_featured.json
```

Useful targets
- `make validate examples/file.json`: validate JSON in the container
- `make run DATA=... OUT_FILE=...`: render with custom input/output
- `make run-dev DATA=...`: run with live source mounted (CWD=/work)
- `make shell-dev`: interactive shell with code mounted
- `make shell`: shell in the built image (no code mount)
- `make clean`: remove local output artifact

Variables
- `IMAGE`, `TAG`, `PLATFORM` control image name and platform
- `DATA`, `OUT_DIR`, `OUT_FILE` control input/output
- `RUN_ARGS` passes extra flags to `docker run`

