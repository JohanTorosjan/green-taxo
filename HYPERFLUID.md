# Déploiement de GreenTaxo sur Hyperfluid

Ce guide décrit le passage de la VM Docker Compose à la plateforme Hyperfluid
du mésocentre. Le `docker-compose.yml` reste utilisable pour le développement local.

## Architecture cible

| Sur la VM (compose)  | Sur Hyperfluid                     | Image / service                 | Port | URL publique |
|----------------------|------------------------------------|---------------------------------|------|--------------|
| `db` (Postgres 15)   | **PostgreSQL managé**              | service managé                  | —    | non          |
| `redis`              | **Cache compatible Redis**         | service managé                  | —    | non          |
| `backend`            | Conteneur CaaS `greentaxo-api`     | `greentaxo-backend`             | 8000 | oui          |
| `celery-worker`      | Conteneur CaaS `greentaxo-worker`  | `greentaxo-backend` (autre cmd) | —    | non          |
| `frontend`           | Conteneur CaaS `greentaxo-front`   | `greentaxo-frontend`            | 8080 | oui          |
| `celery-flower`      | facultatif, non déployé            | —                               | —    | —            |

Les documents uploadés sont stockés dans Postgres (colonnes `BYTEA`) : la
migration des données se résume à un dump de la base.

## 1. Construire et pousser les images

Récupérer l'hôte du registre et le nom du projet dans l'interface Harbor
(page du projet, commande « push »), puis :

```bash
docker login <hôte-du-registre>
REGISTRY=<hôte-du-registre>/<projet> ./build-and-push.sh
```

Le script construit pour `linux/amd64` : c'est indispensable depuis un Mac
Apple Silicon, sinon les images ne démarreront pas sur le cluster.

## 2. Créer les services managés

1. **PostgreSQL** : version 15 ou plus. Noter l'hôte, le port, l'utilisateur,
   le mot de passe et le nom de la base.
2. **Cache Redis** : la plus petite taille suffit (128 Mo), Redis ne sert que de
   file d'attente pour Celery. Noter l'URL de connexion.

## 3. Secrets

À stocker dans le coffre à secrets et à injecter dans les conteneurs :

| Variable         | Valeur                                                              |
|------------------|---------------------------------------------------------------------|
| `DATABASE_URL`   | `postgresql://<user>:<mot-de-passe>@<hôte>:<port>/<base>`           |
| `REDIS_URL`      | `redis://[:<mot-de-passe>@]<hôte>:<port>/0`                         |
| `SECRET_KEY`     | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`     |
| `MISTRAL_API_KEY`| clé de l'API Mistral                                                |

## 4. Créer les conteneurs

### `greentaxo-api`
- Image : `greentaxo-backend:<tag>`, port **8000**, URL publique activée.
- Variables : `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `MISTRAL_API_KEY`,
  `DEBUG=false`, `CORS_ORIGINS=https://<url-du-frontend>`
  (à renseigner une fois l'URL du frontend connue ; `*` en attendant).
- Test : `https://<url-api>/health` doit répondre `"database": "connected"`.

### `greentaxo-worker`
- Même image `greentaxo-backend:<tag>`, **pas d'URL publique**.
- Commande : `celery -A app.celery_app worker --loglevel=info --concurrency=2`
- Variables : `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `MISTRAL_API_KEY`, `DEBUG=false`.

### `greentaxo-front`
- Image : `greentaxo-frontend:<tag>`, port **8080**, URL publique activée.
- Variable : `API_HOST=https://<url-api>` (sans `/` final).
  L'URL est injectée au démarrage du conteneur : changer d'API ne demande
  qu'un redémarrage, pas un nouveau build.

## 5. Migrer les données depuis la VM

Sur la VM, couper le worker pour figer les analyses en cours, puis exporter :

```bash
cd ~/greentaxo
docker compose stop celery-worker
docker compose exec -T db pg_dump -U greentaxo -d greentaxo_db -Fc > ~/greentaxo.dump
```

Restaurer dans le PostgreSQL managé, depuis une machine qui peut joindre la base
(la VM si le réseau le permet, sinon un conteneur temporaire lancé avec l'image
`greentaxo-backend`, qui contient `pg_restore`) :

```bash
pg_restore --no-owner --no-acl -d "$DATABASE_URL" greentaxo.dump
```

Le dump contient le schéma : ne pas exécuter `init.sql` séparément.

## 6. Vérifications

- [ ] `/health` de l'API : base connectée
- [ ] Connexion au frontend avec un compte existant
- [ ] Liste des documents et des analyses identique à la VM
- [ ] Upload d'un document : la tâche apparaît dans les logs du worker, l'analyse se termine
- [ ] Exports du dashboard admin

Après la migration, les utilisateurs devront se reconnecter une fois :
les jetons sont désormais signés avec `SECRET_KEY`.

## 7. Bascule

1. Pointer le domaine public vers les nouvelles URL, si un domaine personnalisé est utilisé.
2. Mettre à jour `CORS_ORIGINS` et `API_HOST` avec les URL définitives.
3. Garder la VM éteinte mais intacte quelques semaines, puis la supprimer.

## Changements apportés au code pour ce déploiement

- `backend/dockerfile` : plus de `--reload`, utilisateur non-root, en-têtes de proxy.
- `backend/app/auth_config.py` : la clé JWT est lue depuis `SECRET_KEY`.
- `backend/app/config.py` : `CORS_ORIGINS` configurable, `DEBUG` à `false` par défaut.
- `frontend/dockerfile` : étapes `dev` (compose local), `build` et `prod` (nginx non-root sur 8080).
- `frontend/docker/40-inject-api-host.sh` : injection de `API_HOST` au démarrage.
