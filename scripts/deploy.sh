#!/bin/bash
set -e

echo "Docker Build"
docker compose -f compose.yaml -f compose.proxy.yaml build django
docker compose -f compose.yaml -f compose.proxy.yaml build nginx

echo "Recreate containers"
docker compose -f compose.yaml -f compose.proxy.yaml down && docker compose -f compose.yaml -f compose.proxy.yaml up -d

if [ "${MIGRATE:-0}" = 1 ]; then
    echo "Running migrations"
    sleep 5
    docker compose -f compose.yaml -f compose.proxy.yaml exec django python manage.py migrate --noinput
fi

echo "Deployment complete!"