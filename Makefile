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

.PHONY: build
build: ## Build image (buildx)
	$(call _print,Build $(IMAGE):$(TAG) for $(PLATFORM))
	$(DOCKER) buildx build --platform $(PLATFORM) -t $(IMAGE):$(TAG) --progress=plain .

.PHONY: rebuild
rebuild: ## No-cache build
	$(call _print,Rebuild no-cache)
	$(DOCKER) buildx build --no-cache --platform $(PLATFORM) -t $(IMAGE):$(TAG) --progress=plain .

.PHONY: validate
validate: ## Validate JSON with quadre-validate (mounted code, Python image)
	@test -f "$(DATA)" || (echo "Error: DATA does not exist -> $(DATA)"; exit 1)
	$(call _print,Validate $(DATA))
	$(DOCKER) run --rm --platform $(PLATFORM) $(RUN_ARGS) \
		--entrypoint /app/.venv/bin/python \
		-e PYTHONPATH=/work \
		-v "$(abspath $(PWD))":/work:ro \
		-v "$(abspath $(DATA))":/data.json:ro \
		$(IMAGE):$(TAG) -m quadre.validator /data.json
	$(call _print,Validation OK)

.PHONY: run
run: validate ## Render: reads $(DATA) and writes $(OUT_DIR)/$(OUT_FILE)
	@test -f "$(DATA)" || (echo "Error: DATA does not exist -> $(DATA)"; exit 1)
	@mkdir -p "$(OUT_DIR)"
	$(call _print,Run $(IMAGE):$(TAG))
	$(DOCKER) run --rm --platform $(PLATFORM) $(RUN_ARGS) \
		-v "$(abspath $(DATA))":/data.json:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		$(IMAGE):$(TAG) /data.json /out/$(OUT_FILE)
	$(call _print,OK -> $(OUT_DIR)/$(OUT_FILE))

.PHONY: run-checked
run-checked: run ## Alias: validate then render

.PHONY: run-dev
run-dev: ## Run with live code (mount full repo, use it as CWD)
	@test -f "$(DATA)" || (echo "Error: DATA does not exist -> $(DATA)"; exit 1)
	@mkdir -p "$(OUT_DIR)"
	$(call _print,Run DEV (mounted repo) $(IMAGE):$(TAG))
	$(DOCKER) run --rm -w /work --platform $(PLATFORM) $(RUN_ARGS) \
		-e PYTHONPATH=/work \
		-v "$(abspath $(PWD))":/work:ro \
		-v "$(abspath $(DATA))":/data.json:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		$(IMAGE):$(TAG) /data.json /out/$(OUT_FILE)
	$(call _print,OK -> $(OUT_DIR)/$(OUT_FILE))

.PHONY: shell-dev
shell-dev: ## Interactive shell with live code mounted (CWD=/work)
	$(DOCKER) run --rm -it -w /work --platform $(PLATFORM) $(RUN_ARGS) \
		-e PYTHONPATH=/work \
		-v "$(abspath $(PWD))":/work:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		--entrypoint /bin/bash \
		$(IMAGE):$(TAG)

.PHONY: test
test: ## Run unit tests + validate all examples (set quadre_PIXELS=1 to include pixel tests)
	uv run pytest -q
	@echo "Validating all JSONs in examples/…"
	@set -e; for f in $(shell ls examples/*.json); do \
		$(MAKE) -s validate $$f || exit $$?; \
	done


.PHONY: shell
shell: ## Interactive shell in the container (built image)
	$(DOCKER) run --rm -it --platform $(PLATFORM) $(RUN_ARGS) \
		-v "$(abspath $(DATA))":/data.json:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		--entrypoint /bin/bash \
		$(IMAGE):$(TAG)

.PHONY: clean
clean: ## Remove local artifact
	@rm -f "$(OUT_DIR)/$(OUT_FILE)" || true
	$(call _print,cleaned)
