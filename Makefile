.PHONY: upgrade

# Main upgrade command as requested by user
upgrade:
	@chmod +x scripts/release.sh
	@./scripts/release.sh $(VERSION)

# Aliases and other helpers
release: upgrade

install:
	pip install -e ".[dev]"

test:
	pytest

lint:
	ruff check .
	black --check .
	isort --check-only .
	mypy covert/

format:
	black .
	isort .
