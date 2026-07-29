# Book Catalog API

A RESTful Book Catalog API built with Django and Django REST Framework, containerized with Docker, deployed to Kubernetes via Helm, and automated end-to-end with GitHub Actions. Built as the capstone project for CCT Dublin's Diploma in DevOps.

## Project overview

The API manages a catalog of books with full CRUD support. Each book stores:

- **Title**
- **Author**
- **ISBN** (validated as ISBN-10 or ISBN-13, unique per book)
- **Published date** (cannot be in the future)

**Tech stack:**

| Layer | Technology |
|---|---|
| API | Django 4.2 (LTS) + Django REST Framework |
| Database | PostgreSQL 16 |
| Containerization | Docker + docker-compose |
| Orchestration | Kubernetes (kind, locally) |
| Packaging | Helm chart |
| Deployment model | GitOps via ArgoCD |
| CI/CD | GitHub Actions |
| Registry | GitHub Container Registry (GHCR) |

## API usage examples

Base URL locally: `http://localhost:8000/api/` (via docker-compose) or `http://bookcatalog.local/api/` (via the Kubernetes Ingress).

**Create a book**
```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Clean Code","author":"Robert C. Martin","isbn":"9780132350884","published_date":"2008-08-01"}'
```
```json
{"id":1,"title":"Clean Code","author":"Robert C. Martin","isbn":"9780132350884","published_date":"2008-08-01","created_at":"2026-07-27T05:32:09.569357Z","updated_at":"2026-07-27T05:32:09.569370Z"}
```

**List books** (paginated, 10 per page)
```bash
curl http://localhost:8000/api/books/
```
```json
{"count":1,"next":null,"previous":null,"results":[{"id":1,"title":"Clean Code", "...": "..."}]}
```

**Retrieve a single book**
```bash
curl http://localhost:8000/api/books/1/
```

**Update a book (full)**
```bash
curl -X PUT http://localhost:8000/api/books/1/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Clean Code (2nd Ed)","author":"Robert C. Martin","isbn":"9780132350884","published_date":"2008-08-01"}'
```

**Partially update a book**
```bash
curl -X PATCH http://localhost:8000/api/books/1/ -H "Content-Type: application/json" -d '{"author":"Uncle Bob"}'
```

**Delete a book**
```bash
curl -X DELETE http://localhost:8000/api/books/1/
```

Books can also be searched and ordered:
```bash
curl "http://localhost:8000/api/books/?search=clean&ordering=-published_date"
```

## Local build and run instructions

### Option A — Docker Compose (recommended, matches production config)

```bash
git clone git@github.com:BarraHarrison/CCT-DevOps-Capstone.git
cd CCT-DevOps-Capstone
cp .env.example .env   # adjust values if needed
docker compose up --build
```

This starts a PostgreSQL container and the Django app (via Gunicorn), running migrations automatically on startup. The API is available at `http://localhost:8000/api/books/`.

### Option B — Plain Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export DB_ENGINE=sqlite DJANGO_SECRET_KEY=dev-key DJANGO_DEBUG=True
python manage.py migrate
python manage.py runserver
```

Using `DB_ENGINE=sqlite` avoids needing a local PostgreSQL install; unset it (or set `DB_ENGINE=postgres` with `DB_HOST`/`DB_USER`/etc.) to run against real Postgres.

### Running tests

```bash
export DB_ENGINE=sqlite DJANGO_SECRET_KEY=test-key DJANGO_DEBUG=True
python manage.py test books
```

10 unit tests cover the `Book` model (creation, ISBN uniqueness) and the full CRUD API (list, create, validation failures for bad ISBNs/future dates, retrieve, update, partial update, delete).

## CI/CD pipeline explanation

Defined in [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml), triggered on every push to `main` (and on pull requests, for the test stage only):

1. **`test`** — runs on a GitHub-hosted runner. Installs dependencies from `requirements.txt` and runs the full Django test suite against an in-memory SQLite database.
2. **`build-and-push`** — runs only on pushes to `main`, after tests pass. Builds the Docker image from the `Dockerfile` and pushes it to GitHub Container Registry, tagged both `:latest` and with the commit SHA.
3. **`deploy-application`** — runs only on pushes to `main`, after the image is pushed. Updates `image.tag` in [`environments/production/values.yaml`](environments/production/values.yaml) to the new commit SHA using [`fjogeleit/yaml-update-action`](https://github.com/fjogeleit/yaml-update-action), and commits that change back to `main` with `[skip ci]` (so it doesn't re-trigger the pipeline).

**Deployment is GitOps-driven, not push-driven.** Earlier in this project, the pipeline deployed directly by running `helm upgrade --install` from a self-hosted GitHub Actions runner (since the target `kind` cluster is local and unreachable from GitHub-hosted runners). This has been replaced with [ArgoCD](#argocd-gitops-deployment), which runs *inside* the cluster and continuously watches this repository. Now the pipeline's only job is to update the image tag in Git — ArgoCD detects that change and deploys it automatically. This means the `deploy-application` job runs on a normal GitHub-hosted runner, and no self-hosted runner or direct cluster access from CI is required at all.

**Why GHCR over Docker Hub?** GHCR integrates directly with GitHub's built-in `GITHUB_TOKEN` for authentication — no extra secrets to manage — and packages pushed from a public repository are public by default, which simplifies the cluster's image pulls.

## Kubernetes and Helm setup instructions

### Prerequisites

```bash
brew install kind kubectl helm
```

### 1. Create the local cluster

```bash
kind create cluster --name bookcatalog --config kind-config.yaml
```

`kind-config.yaml` maps ports 80/443 to localhost so the Ingress controller is reachable directly.

### 2. Install the NGINX Ingress controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=120s
```

### 3. Add the local hostname

```bash
echo "127.0.0.1 bookcatalog.local" | sudo tee -a /etc/hosts
```

### 4. Deploy the application

In normal day-to-day use, you **don't** run `helm install`/`helm upgrade` manually — [ArgoCD](#argocd-gitops-deployment) (set up below) watches this repository and deploys automatically whenever `chart/bookcatalog/` or `environments/production/values.yaml` changes. The commands below are only needed to bootstrap the app once, before ArgoCD exists yet, or for local debugging outside the GitOps flow:

```bash
helm install bookcatalog ./chart/bookcatalog
# or, to upgrade an existing release:
helm upgrade --install bookcatalog ./chart/bookcatalog
```

Then visit `http://bookcatalog.local/api/books/`.

### Chart contents (`chart/bookcatalog/`)

- **Deployment** — runs the Django app (2 replicas by default) via Gunicorn. Includes an init container that waits for PostgreSQL to accept connections before starting, and readiness/liveness probes against `/api/books/`.
- **Service** — a `ClusterIP` Service exposing the app on port 80, routed to port 8000 in the pods. Selects pods by an `app.kubernetes.io/component: api` label specifically, so it never accidentally routes traffic to the bundled PostgreSQL pod (a bug encountered and fixed during development — see the report).
- **Ingress** — routes `bookcatalog.local` traffic to the Service via the NGINX ingress controller.
- **ConfigMap** — non-sensitive environment variables (`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_HOST`, `DB_NAME`, etc.).
- **Secret** — sensitive values (`DJANGO_SECRET_KEY`, `DB_PASSWORD`).
- **Bundled PostgreSQL** (`postgres.yaml`) — a self-contained Postgres Deployment, Service, and PersistentVolumeClaim, so the chart deploys a fully working stack with no external database dependency. In a production setting this would typically be swapped for an external managed database.

Validate the chart at any time with:
```bash
helm lint ./chart/bookcatalog
helm template ./chart/bookcatalog
```

## ArgoCD (GitOps deployment)

ArgoCD runs inside the same `kind` cluster and continuously syncs the cluster's state to match this repository — pushing a change to `main` is enough to deploy it, with no CI job needing direct cluster access.

### 1. Install ArgoCD

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm -n argocd install argocd argo/argo-cd -f ./argocd/values.yaml
```

`argocd/values.yaml` configures ArgoCD to run without TLS (no certificate available locally) and exposes its UI under `/argocd` on the same NGINX ingress controller already used by the app.

### 2. Log in

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

Visit `http://bookcatalog.local/argocd` (or `http://localhost/argocd`), and log in as `admin` with that password.

### 3. Connect this repository

In ArgoCD: **Settings → Repositories → Connect Repo → VIA HTTPS**, and provide a GitHub [fine-grained personal access token](https://github.com/settings/tokens?type=beta) (Contents: Read-only, scoped to just this repository) as the password.

### 4. Create the Application

**Settings → Applications → New App**, with:
- **General:** name `bookcatalog`, project `default`, sync policy **Automatic** (with Prune + Self Heal enabled)
- **Source:** this repository, revision `main`, path `chart/bookcatalog`
- **Destination:** the same (in-cluster) destination, namespace `default`
- **Helm → Values Files:** `../../environments/production/values.yaml`

That last path is relative to the chart directory (`chart/bookcatalog`), not the repo root — two levels up (`../../`) to reach the repo root, then into `environments/production/values.yaml`. Getting this wrong (e.g. leaving it as the default `values.yaml`) silently makes ArgoCD use the chart's own default values instead of the production overlay, with no visible error — worth double-checking directly against the live Application object if the deployed image tag doesn't match what's expected:

```bash
kubectl -n argocd get application bookcatalog -o jsonpath='{.spec.source.helm.valueFiles}'
```

### How a deploy actually happens

1. A push to `main` triggers the CI/CD pipeline (test → build & push image → update `environments/production/values.yaml` with the new image tag, committed by `github-actions[bot]`).
2. ArgoCD detects the new commit on its own (polling this repo) and starts a sync.
3. ArgoCD renders the Helm chart with the updated `values.yaml` and applies it to the cluster — new pods roll out with the new image, automatically.

## Project structure

```
CCT-DevOps-Capstone/
├── bookcatalog/                        # Django project settings, root URLs
├── books/                              # Django app: model, serializer, views, tests
├── chart/bookcatalog/                  # Helm chart
├── argocd/values.yaml                  # ArgoCD's own Helm install values
├── environments/production/values.yaml # Image tag override ArgoCD deploys from
├── .github/workflows/                  # CI/CD pipeline
├── Dockerfile
├── docker-compose.yml
├── kind-config.yaml
├── requirements.txt
└── manage.py
```
