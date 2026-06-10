# Onboarding Guide

Welcome to the Filesystem Backend project. This document walks you through everything you need to understand, run, and contribute to the codebase.

---

## Table of contents

1. [What this project does](#1-what-this-project-does)
2. [Tech stack](#2-tech-stack)
3. [Repository layout](#3-repository-layout)
4. [Local setup](#4-local-setup)
5. [Configuration](#5-configuration)
6. [Settings hierarchy](#6-settings-hierarchy)
7. [Data model](#7-data-model)
8. [API endpoints](#8-api-endpoints)
9. [Filesystem sync](#9-filesystem-sync)
10. [Adding a new feature](#10-adding-a-new-feature)
11. [Running tests](#11-running-tests)
12. [Common tasks reference](#12-common-tasks-reference)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. What this project does

This is a Django REST API that models a **virtual filesystem** — files and folders are represented as `Node` records in a MySQL database and are simultaneously mirrored as real files and directories on disk. Any create or delete operation on a node is automatically reflected on the physical filesystem through Django signals.

---

## 2. Tech stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | Django 5.2 + Django REST Framework 3.15 |
| Database | MySQL 8.0 |
| API schema | drf-spectacular (OpenAPI 3) |
| Containerisation | Docker / Docker Compose |
| Task queue | Celery (installed, not yet wired to filesystem) |
| ASGI server | Daphne + Uvicorn |

---

## 3. Repository layout

```
.
├── core/                        # Shared utilities (custom exceptions, etc.)
│   └── exception.py             # BadRequestApiException (HTTP 400)
│
├── filesystem/                  # Main application
│   ├── models.py                # Node model (self-referential tree)
│   ├── serializers.py           # NodeCreateSerializer, NodeSerializer, NodeListSerializer
│   ├── views.py                 # NodesViewSet, NodeListView, BulkDeleteView
│   ├── urls.py                  # URL routing for the filesystem app
│   ├── signals.py               # Disk sync on create / delete
│   ├── repositories.py          # Raw SQL helpers (recursive CTE path query)
│   ├── utils.py                 # build_node_path helper
│   ├── docs.py                  # drf-spectacular schema decorators
│   └── tests.py                 # Functional test suite
│
├── skeleton/                    # Django project package
│   ├── settings/
│   │   ├── base.py              # Shared settings (all environments inherit this)
│   │   ├── local.py             # Local development overrides
│   │   └── testing.py           # Test-run overrides
│   ├── urls.py                  # Root URL config
│   └── wsgi.py / asgi.py
│
├── docs/                        # Project documentation
├── .env.dist                    # Environment variable template
├── docker-compose.yaml
├── Makefile                     # Developer shortcuts
└── requirements.txt
```

---

## 4. Local setup

### Prerequisites

- Docker and Docker Compose
- `make`

### Step-by-step

**1. Clone the repository**

```bash
git clone <repo-url>
cd filesystem-be
```

**2. Create your `.env` file**

```bash
cp .env.dist .env
```

The defaults in `.env.dist` work for local Docker development — you do not need to change anything to get started.

**3. Initialise the project**

```bash
make init
```

This command:
- Starts all Docker containers in detached mode
- Waits for MySQL to be ready
- Runs `makemigrations` and `migrate`
- Prompts you to create a Django superuser

**4. Verify it is running**

- API root: `http://localhost:8100/api/`
- Interactive API docs (Swagger): `http://localhost:8100/api/docs`
- OpenAPI schema (JSON): `http://localhost:8100/schema`

---

## 5. Configuration

All configuration lives in `.env`. The file is read by both Docker Compose and Django (via `python-dotenv`).

| Variable | Purpose | Default |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Which settings module to load | `skeleton.settings.local` |
| `DATABASE_NAME` | MySQL database name | `django_skeleton` |
| `DATABASE_USER` | MySQL user | `skeleton_user` |
| `DATABASE_PASS` | MySQL password | `Test1234.` |
| `DATABASE_HOST` | MySQL host (service name inside Docker) | `db` |
| `DATABASE_PORT` | MySQL port | `3306` |
| `DATABASE_ROOT_PASSWORD` | MySQL root password (needed for test setup) | `root` |
| `BACKEND_URL` | Public URL of the API | `http://localhost:8100` |
| `FORWARD_WEB_PORT` | Host port for the API | `8100` |
| `FORWARD_DB_PORT` | Host port for MySQL (for GUI tools) | `3308` |
| `DEBUG` | Django debug mode | `true` |

> **Never commit `.env` to version control.** It is git-ignored. Always use `.env.dist` as the source of truth for required variables.

---

## 6. Settings hierarchy

```
skeleton/settings/base.py      ← all shared settings live here
        └── local.py           ← local dev (DJANGO_SETTINGS_MODULE=skeleton.settings.local)
        └── testing.py         ← used by make test
```

`local.py` and `testing.py` both do `from .base import *` and then override what they need. Add environment-specific overrides only in those files, not in `base.py`.

---

## 7. Data model

### `Node` (`filesystem/models.py`)

The single model that represents both files and folders.

| Field | Type | Notes |
|---|---|---|
| `id` | BigAutoField | Primary key |
| `original_name` | CharField | Human-readable name, indexed |
| `name` | CharField (unique, nullable) | System-generated name for `FILE` nodes only |
| `type` | CharField | `FOLDER` or `FILE` (see `NodeTypes`) |
| `parent` | ForeignKey(self) | `null` for root-level nodes; `CASCADE` delete |
| `created_at` | DateTimeField | Auto-set on insert |
| `updated_at` | DateTimeField | Auto-set on update |

**Tree structure:** nodes form an arbitrary-depth tree. A root node has `parent = null`. Deleting a parent cascades to all descendants.

**Uniqueness rule:** `original_name` must be unique within its parent scope — i.e. two nodes cannot share a name under the same parent (enforced in `NodeCreateSerializer.validate`).

---

## 8. API endpoints

Base path: `/api/`

| Method | Path | Description |
|---|---|---|
| `POST` | `nodes/` | Create a node (file or folder) |
| `GET` | `nodes/<id>/` | Retrieve a node with its children |
| `DELETE` | `nodes/<id>/` | Delete a node |
| `GET` | `nodes/list/` | List nodes with optional filters |
| `POST` | `nodes/bulk-delete/` | Delete multiple nodes by id |

### Create — `POST /api/nodes/`

Request body:
```json
{
  "original_name": "documents",
  "type": "FOLDER",
  "parent": null
}
```

- `parent` is the integer id of the parent node, or `null` for a root-level node.
- Returns `201` with the full `NodeSerializer` representation.
- Returns `400` if a node with the same name already exists at that location.
- Returns `404` if the specified parent does not exist.

### Retrieve — `GET /api/nodes/<id>/`

Returns the node and its **direct children** (one level only).

### Delete — `DELETE /api/nodes/<id>/`

- Deleting a **non-empty folder** without confirmation returns `500` with a prompt.
- To confirm, add `?confirm=true`: `DELETE /api/nodes/<id>/?confirm=true`
- Cascade-deletes all descendants.

### List — `GET /api/nodes/list/`

Query parameters:

| Parameter | Type | Description |
|---|---|---|
| `parent` | integer | Return only direct children of this node id |
| `search` | string | Filter by `original_name` prefix (startswith) |

Responses are paginated (`limit` / `offset`).

### Bulk delete — `POST /api/nodes/bulk-delete/`

Request body:
```json
{ "ids": [1, 2, 3] }
```

Returns `207 Multi-Status` on success. Returns `400` if `ids` is missing or empty.

---

## 9. Filesystem sync

Node create and delete operations are automatically mirrored to disk via **Django signals** in `filesystem/signals.py`.

| Signal | Trigger | Disk action |
|---|---|---|
| `post_save` (create only) | New node saved | `os.mkdir` for folders, `open()` touch for files |
| `pre_delete` | Before node deleted | `shutil.rmtree` for folders, `os.remove` for files |

**Why `pre_delete`?** The physical path is constructed by walking the node's ancestor chain through a recursive SQL CTE (`NodeRepository.find_node_parent_chain`). The node must still exist in the database when this query runs. Using `post_delete` would mean the row is already gone and the CTE would return an empty result, leaving orphaned files on disk.

The physical root of the filesystem is controlled by `settings.FILE_SYSTEM_ROOT` (defaults to `<project_root>/root/`).

### Path computation

`NodeRepository.find_node_parent_chain` runs a single recursive CTE that traverses the parent chain from the target node up to the root, then orders the result by depth descending. The result is joined with `/` to produce the full relative path (e.g. `documents/reports/q1.pdf`).

---

## 10. Adding a new feature

### Adding a new endpoint

1. Add the view to `filesystem/views.py`.
2. Add drf-spectacular schema metadata to `filesystem/docs.py`.
3. Register the URL in `filesystem/urls.py`.
4. Add functional tests in `filesystem/tests.py`.

### Adding a new model

1. Create the model in the relevant `models.py`.
2. Generate a migration: `make migrations app=filesystem`.
3. Apply it: `make migrate`.

### Adding a new app

```bash
make startapp app=<name>
```

Register it in `INSTALLED_APPS` in `skeleton/settings/base.py`.

---

## 11. Running tests

### One-time setup

The test runner creates a temporary database named `test_<DATABASE_NAME>`. Grant the MySQL user permission to create it:

```bash
docker compose exec db mysql -u root -proot \
  -e "GRANT ALL PRIVILEGES ON \`test_django_skeleton\`.* TO 'skeleton_user'@'%'; FLUSH PRIVILEGES;"
```

### Run the suite

```bash
make test
```

This runs `filesystem.tests` with `skeleton.settings.testing`.

### Test design notes

- All tests extend `BaseNodeTest`, which mocks every filesystem signal call (`os.mkdir`, `shutil.rmtree`, etc.) so tests never touch disk and do not require `FILE_SYSTEM_ROOT` to exist.
- `_make_folder` / `_make_file` helpers create DB fixtures directly, bypassing the API.
- Each test class is scoped to one view (`NodesViewSetCreateTests`, `NodesViewSetRetrieveTests`, `NodesViewSetDestroyTests`, `NodeListViewTests`, `BulkDeleteViewTests`).

---

## 12. Common tasks reference

| Task | Command |
|---|---|
| Start containers | `make up` |
| Stop containers | `make down` |
| Open a shell in the web container | `make bash` |
| Run all migrations | `make migrate` |
| Run migrations for one app | `make migrate app=filesystem` |
| Generate new migrations | `make migrations` |
| Flush the database | `make db-flush` |
| Install dependencies | `make requirements` |
| Run tests | `make test` |
| Start a new Django app | `make startapp app=<name>` |

---

## 13. Troubleshooting

**`Access denied … to database 'test_django_skeleton'`**  
The MySQL user lacks the `CREATE` privilege on the test database. Run the grant command in [section 11](#11-running-tests).

**`AttributeError: module 'skeleton.settings' has no attribute '…'`**  
Something is importing `from skeleton import settings` (the raw package) instead of Django's settings proxy. Use `from django.conf import settings` everywhere.

**`Manager object is not subscriptable`**  
A queryset method is being called on `Model.objects` (the manager) directly instead of on a queryset. Call `.all()` or `.filter()` first to get a queryset before subscripting or iterating.

**Container starts but migrations fail**  
MySQL may still be initialising. `make init` waits 15 seconds, but on slower machines you may need to re-run `make migrate` after the database is fully ready.

**Port conflicts**  
If `8100` (API) or `3308` (MySQL) are already in use, override them in `.env`:
```
FORWARD_WEB_PORT=8200
FORWARD_DB_PORT=3309
```
