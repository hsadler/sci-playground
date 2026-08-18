.DEFAULT_GOAL := help
.PHONY: help install setup-git-filter run lab notebook test test-all lint fmt check nb-strip clean-cache

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-17s\033[0m %s\n", $$1, $$2}'

install:  ## Install everything, and set up the notebook git filter
	uv sync --all-groups
	$(MAKE) setup-git-filter

setup-git-filter:  ## Stop notebook outputs from being committed (once per clone)
	uv run nbstripout --install --attributes .gitattributes
	@echo
	@echo "Notebook outputs are now stripped from what git stores, so they can never"
	@echo "be committed. Your files keep their outputs for Jupyter."
	@echo "If 'git status' lists a notebook after you run it, 'make nb-refresh' clears it."

nb-refresh:  ## Clear notebooks that `git status` lists but `git diff` shows as empty
	@# Executing a notebook changes its size, so the size cached in the index no
	@# longer matches. Git re-filters, finds the content identical, but leaves the
	@# stale stat entry, and `git status` keeps reporting the file. This `add`
	@# refreshes that stat info; because the filtered content is unchanged it stages
	@# nothing. Purely cosmetic -- there was never anything to commit.
	git add -- '*.ipynb'
	@git status --short -- '*.ipynb'

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
	@# Ask git for the notebook list rather than shell-globbing: notebooks live in
	@# primer/, course/ and explorations/, and `*.ipynb` would only match the root.
	@files=$$(git ls-files '*.ipynb'); \
	if [ -n "$$files" ]; then uv run nbstripout $$files; else echo "no notebooks tracked"; fi

clean-cache:  ## Delete cached derived light curves (they will be rebuilt on demand)
	rm -rf data/cache
