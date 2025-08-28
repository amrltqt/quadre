# Makefile — dockerized dashboard renderer (uv + Python 3.13)
# Usage: make help

# ---- Config ----
IMAGE       ?= dash-render-uv
TAG         ?= latest
PLATFORM    ?= linux/amd64
DOCKER      ?= docker

DATA        ?= $(PWD)/data.json# override: make run DATA=./my.json
OUT_DIR     ?= $(PWD)/out
OUT_FILE    ?= dashboard.png

RUN_ARGS    ?=                         # extra: e.g. --cpus=2 --memory=1g

# ---- Helpers ----
define _print
	@printf "▶ %s\n" "$(1)"
endef

# ---- Targets ----
.PHONY: help
help: ## Affiche cette aide
	@awk 'BEGIN{FS":.*##"; printf "\nCibles:\n"} /^[a-zA-Z0-9_-]+:.*##/{printf "  \033[36m%-15s\033[0m %s\n",$$1,$$2}' $(MAKEFILE_LIST)
	@printf "\nVars utiles (override avec VAR=val):\n  IMAGE TAG PLATFORM DATA OUT_DIR OUT_FILE RUN_ARGS\n\n"

.PHONY: build
build: ## Build image (buildx)
	$(call _print,Build $(IMAGE):$(TAG) for $(PLATFORM))
	$(DOCKER) buildx build --platform $(PLATFORM) -t $(IMAGE):$(TAG) --progress=plain .

.PHONY: run
run: ## Exécute le rendu: lit $(DATA) et écrit $(OUT_DIR)/$(OUT_FILE)
	@test -f "$(DATA)" || (echo "Erreur: DATA n'existe pas -> $(DATA)"; exit 1)
	@mkdir -p "$(OUT_DIR)"
	$(call _print,Run $(IMAGE):$(TAG))
	$(DOCKER) run --rm $(RUN_ARGS) \
		-v "$(abspath $(DATA))":/data.json:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		$(IMAGE):$(TAG) /data.json /out/$(OUT_FILE)
	$(call _print,OK -> $(OUT_DIR)/$(OUT_FILE))

.PHONY: shell
shell: ## Shell interactif dans le conteneur
	$(DOCKER) run --rm -it $(RUN_ARGS) \
		-v "$(abspath $(DATA))":/data.json:ro \
		-v "$(abspath $(OUT_DIR))":/out \
		--entrypoint /bin/bash \
		$(IMAGE):$(TAG)

.PHONY: clean
clean: ## Supprime l’artefact local
	@rm -f "$(OUT_DIR)/$(OUT_FILE)" || true
	$(call _print,nettoyé)

.PHONY: rebuild
rebuild: ## Build sans cache
	$(call _print,Rebuild no-cache)
	$(DOCKER) buildx build --no-cache --platform $(PLATFORM) -t $(IMAGE):$(TAG) --progress=plain .

.PHONY: fmt
fmt: ## Format Dockerfile avec docker buildx bake (dry-run) pour valider la syntaxe
	$(call _print,Validation Dockerfile)
	@$(DOCKER) buildx bake --print >/dev/null || true
