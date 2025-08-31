# Makefile — dockerized dashboard renderer (uv + Python 3.13)
# Usage: make help

# ---- Config ----
IMAGE       ?= dash-render-uv
TAG         ?= latest
PLATFORM    ?= linux/$(shell uname -m | sed 's/aarch64/arm64/;s/x86_64/amd64/')
DOCKER      ?= docker

# override: make run DATA=./my.json
DATA        ?= $(PWD)/data.json
OUT_DIR     ?= $(PWD)/out
OUT_FILE    ?= dashboard.png

# extra: e.g. --cpus=2 --memory=1g
RUN_ARGS    ?=

# ---- Helpers ----
define _print
	@printf "▶ %s\n" "$(1)"
endef


# ---- Positional JSON convenience ----
# Allow: `make run examples/file.json` or `make validate examples/file.json`
JSON_ARG := $(filter %.json,$(MAKECMDGOALS))
ifneq ($(JSON_ARG),)
DATA := $(JSON_ARG)
# Swallow the file goal so make doesn't error
 .PHONY: $(JSON_ARG)
$(JSON_ARG): ;
endif

# ---- Targets ----
.PHONY: help
help: ## Show this help
	@awk 'BEGIN{FS":.*##"; printf "\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*##/{printf "  \033[36m%-15s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)
	@printf "\nQuick usage:\n  make run examples/file.json\n  make validate examples/file.json\n\nUseful vars (override with VAR=value):\n  IMAGE TAG PLATFORM DATA OUT_DIR OUT_FILE RUN_ARGS\n\n" 


.PHONY: test
test: ## Run unit tests + validate all examples (set quadre_PIXELS=1 to include pixel tests)
	uv run pytest -q
	@echo "Validating all JSONs in examples/…"
	@set -e; for f in $(shell ls examples/*.json); do \
		$(MAKE) -s validate $$f || exit $$?; \
	done


.PHONY: clean
clean: ## Remove local artifact
	@rm -f "$(OUT_DIR)/$(OUT_FILE)" || true
	$(call _print,cleaned)

# ---- Packaging / Publishing (local, no Docker) ----
.PHONY: clean-dist
clean-dist: ## Remove dist/ artifacts
	rm -rf dist

.PHONY: build-dist
build: clean-dist ## Build wheel + sdist with uv (ephemeral build tool)
	$(call _print,Build wheel + sdist)
	uv run --with build python -m build
	$(call _print,OK -> dist/)

.PHONY: publish
publish: build-dist ## Upload to PyPI (set TWINE_PASSWORD=<token>)
	$(call _print,Upload to PyPI)
	uv run --with twine python -m twine upload dist/*


# ---- Local run/validate (no Docker) ----
.PHONY: run
run: ## Render $(DATA) to $(OUT_DIR)/$(OUT_FILE) using uv
	@mkdir -p "$(OUT_DIR)"
	uv run -m quadre.cli render "$(DATA)" "$(OUT_DIR)/$(OUT_FILE)"
	$(call _print,Wrote $(OUT_DIR)/$(OUT_FILE))

.PHONY: validate
validate: ## Validate $(DATA) JSON via uv (schema + warnings)
	uv run -m quadre.cli validate "$(DATA)"
