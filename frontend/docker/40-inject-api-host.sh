#!/bin/sh
# Remplace le marqueur __API_HOST__ du build Ember par l'URL réelle de l'API,
# fournie via la variable d'environnement API_HOST du conteneur.
set -e

if [ -z "$API_HOST" ]; then
  echo "[inject-api-host] ERREUR : la variable API_HOST n'est pas définie" >&2
  exit 1
fi

# Retire un éventuel "/" final
API_HOST="${API_HOST%/}"

grep -rl "__API_HOST__" /usr/share/nginx/html --include='*.html' --include='*.js' 2>/dev/null \
  | while read -r f; do
      sed -i "s|__API_HOST__|${API_HOST}|g" "$f"
    done

echo "[inject-api-host] API_HOST = ${API_HOST}"
