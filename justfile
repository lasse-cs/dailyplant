# Show available commands
default:
	just --list

# Run the linters on all files
lint:
	uv run pre-commit run --all-files

# Format the python files
format-py *args:
	uv run ruff format {{args}}

# Format the js files
format-js *args:
	npm run format -- {{args}}

# Format all files
format: format-py format-js

# Run the Django development server and Vite via Honcho
dev:
	uv run honcho start

# Run any Django management command
manage *args:
	uv run src/manage.py {{args}}

# Open the Django shell to run python commands in the django environment
shell:
	@just manage shell

# Apply migrations
migrate *args:
	@just manage migrate {{args}}

# Create migrations
makemigrations *args:
	@just manage makemigrations {{args}}

# Run tests, except end-to-end tests
test *args:
  uv run pytest {{args}}

# Run end-to-end tests
e2e *args:
	uv run pytest --ds dailyplant.settings.e2e -m e2e {{args}}

import? ".justfile.local"