# Filesystem Backend

Django REST API providing a virtual filesystem — nodes (files and folders) stored in a database with a mirrored structure on disk.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- `make`

## First-time setup

**1. Copy the environment file**

```bash
cp .env.dist .env
```

Edit `.env` if you need to change ports, database credentials, or any other values before starting.

**2. Initialise the project**

```bash
make init
```

This will:
- Start all containers in detached mode
- Wait for the database to become ready
- Run `makemigrations` and `migrate`
- Prompt you to create a superuser

The API is then available at `http://localhost:8100`.

---

## Daily workflow

| Command     | Description                                                |
|-------------|------------------------------------------------------------|
| `make up`   | Start containers (foreground)                              |
| `make down` | Stop and remove containers                                 |
| `make bash` | Open a shell inside the `web` container                    |
| `make init` | Run only once to initialize the project for the first time |

---

## Database

| Command | Description |
|---|---|
| `make migrate` | Run all pending migrations |
| `make migrate app=<app>` | Run migrations for a specific app |
| `make migrations` | Create new migrations (all apps) |
| `make migrations app=<app>` | Create new migrations for a specific app |
| `make db-flush` | Flush all data from the database |

---

## Dependencies

To install Python dependencies inside the container (and locally):

```bash
make requirements
```

---

## Tests

Before running tests for the first time, grant the database user permission to create the test database:

```bash
docker compose exec db mysql -u root -p<DATABASE_ROOT_PASSWORD> \
  -e "GRANT ALL PRIVILEGES ON \`test_<DATABASE_NAME>\`.* TO '<DATABASE_USER>'@'%'; FLUSH PRIVILEGES;"
```

With the default `.env` values this becomes:

```bash
docker compose exec db mysql -u root -proot \
  -e "GRANT ALL PRIVILEGES ON \`test_django_skeleton\`.* TO 'skeleton_user'@'%'; FLUSH PRIVILEGES;"
```

Then run the test suite:

```bash
make test
```

Tests use `skeleton.settings.testing` and run against a temporary `test_<DATABASE_NAME>` database that Django creates and destroys automatically.

---

## Starting a new app

```bash
make startapp app=<app_name>
```

---

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Settings module to load | `skeleton.settings.local` |
| `DATABASE_HOST` | MySQL host | `db` |
| `DATABASE_NAME` | Database name | `django_skeleton` |
| `DATABASE_USER` | Database user | `skeleton_user` |
| `DATABASE_PASS` | Database password | `Test1234.` |
| `DATABASE_PORT` | Database port | `3306` |
| `DATABASE_ROOT_PASSWORD` | MySQL root password (used for test setup) | `root` |
| `BACKEND_URL` | URL the API is served on | `http://localhost:8100` |
| `FORWARD_WEB_PORT` | Host port mapped to the web container | `8100` |
| `FORWARD_DB_PORT` | Host port mapped to MySQL | `3308` |
| `DEBUG` | Django debug mode | `true` |