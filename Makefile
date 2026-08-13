.DEFAULT_GOAL := help
.PHONY: help install setup-git-filter run lab notebook test test-all lint fmt check nb-strip clean-cache

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-17s\033[0m %s\n", $$1, $$2}'

install: setup-git-filter  ## Install everything, and set up the notebook git filter
	uv sync --all-groups

setup-git-filter:  ## Stop notebook outputs from showing up as git changes (once per clone)
	uv sync --all-groups
	uv run nbstripout --install --attributes .gitattributes
	@echo
	@echo "Notebook outputs are now stripped from what git stores."
	@echo "Your files keep their outputs; running a notebook no longer makes a diff."

run: lab  ## Alias for `lab`

lab:  ## Launch JupyterLab
	uv run jupyter lab

notebook:  ## Launch the classic notebook interface
	uv run jupyter notebook

test:  ## Run the test suite (offline only)
	uv run pytest -m "not network"

test-all:  ## Run every test, including ones that hit the MAST archive
	uv run pytest

lint:  ## Check formatting and lint rules
	uv run ruff check src tests
	uv run ruff format --check src tests

fmt:  ## Auto-format and auto-fix
	uv run ruff format src tests
	uv run ruff check --fix src tests

check: lint test  ## Lint then test — run this before committing

# Do NOT also run `nbdime config-git --enable`: it claims *.ipynb diff= in
# .gitattributes too, and the two would fight. For a one-off semantic comparison
# use nbdime directly instead: uv run nbdiff a.ipynb b.ipynb

nb-strip:  ## Also strip outputs from the files on disk (the filter only affects git)
	uv run nbstripout *.ipynb

clean-cache:  ## Delete cached derived light curves (they will be rebuilt on demand)
	rm -rf data/cache
