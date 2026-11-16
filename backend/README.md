# Bridge API

FastAPI + async SQLAlchemy. Local development defaults to SQLite; PostgreSQL and the original Alembic migration chain are retained.

Use the [root setup guide](../README.md) for environment generation and combined startup. Run `npm test` from the project root for isolated integration tests. Interactive API contracts are at `/docs` on the backend server.

`app.bootstrap` creates missing SQLite tables only. PostgreSQL uses `python -m alembic upgrade head`. Do not use bootstrap as a migration strategy for existing SQLite schemas.

See [Architecture](../docs/ARCHITECTURE.md) for API routes, authorization, privacy semantics, schema additions, and integration limits. `CLAUDE.md` and this folder's database-only `docker-compose.yaml` came from the supplied backend; the root README and root compose file describe the integrated application.
