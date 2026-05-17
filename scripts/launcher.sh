#!/bin/bash
set -e

SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Fetching source"
git fetch origin main
git reset --hard origin/main

echo "Starting deployment"
exec "$SCRIPT_DIR/deploy.sh"