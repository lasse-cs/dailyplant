# Show available commands
default:
	just --list

# Run the linters on all files
lint:
	uv run pre-commit run --all-files

# Run the Django dev server and Vite via Honcho
dev:
	uv run honcho start

# Run any Django management command
manage *args:
	uv run src/manage.py {{args}}

# Open the Django shell
shell:
	@just manage shell

# Apply migrations
migrate *args:
	@just manage migrate {{args}}

# Create migrations
makemigrations *args:
	@just manage makemigrations {{args}}

# Run tests
test *args:
  uv run pytest {{args}}

e2e *args:
	uv run pytest --ds dailyplant.settings.e2e -m e2e {{args}}

import? ".justfile.local"