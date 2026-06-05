# Show available commands
default:
	just --list

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

import? ".justfile.local"