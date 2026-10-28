#!/bin/bash
# Construit les images GreenTaxo pour linux/amd64 et les pousse sur le registre Harbor.
#
# Usage :
#   REGISTRY=<hôte-du-registre>/<projet-harbor> ./build-and-push.sh [tag]
#
# Exemple :
#   REGISTRY=registry.exemple.fr/greentaxo ./build-and-push.sh
#
# Prérequis : docker login <hôte-du-registre>
set -euo pipefail

: "${REGISTRY:?Définir REGISTRY, ex. REGISTRY=registry.exemple.fr/greentaxo}"
TAG="${1:-$(git rev-parse --short HEAD)}"
PLATFORM="linux/amd64"   # les nœuds du cluster sont en x86_64 (indispensable depuis un Mac Apple Silicon)

cd "$(dirname "$0")"

echo "==> Backend (API + worker Celery) : ${REGISTRY}/greentaxo-backend:${TAG}"
docker buildx build --platform "$PLATFORM" \
  -t "${REGISTRY}/greentaxo-backend:${TAG}" \
  -t "${REGISTRY}/greentaxo-backend:latest" \
  --push backend

echo "==> Frontend : ${REGISTRY}/greentaxo-frontend:${TAG}"
docker buildx build --platform "$PLATFORM" --target prod \
  -t "${REGISTRY}/greentaxo-frontend:${TAG}" \
  -t "${REGISTRY}/greentaxo-frontend:latest" \
  --push frontend

echo "==> Images poussées avec le tag ${TAG}"
