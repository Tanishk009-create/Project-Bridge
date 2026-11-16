from collections.abc import AsyncIterator
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router as api_v1_router
from app.core import engine, settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Additive local upgrade: preserve existing accounts and writing. PostgreSQL uses Alembic.
    if settings.db_driver == "sqlite+aiosqlite":
        from app.models import AITurn, ReflectionSource, Reminder, AccountToken, PreviewSchedule
        from app.sqlite_upgrade import add_photo_columns, add_account_and_delivery_columns
        async with engine.begin() as connection:
            await connection.run_sync(lambda sync: AITurn.__table__.create(sync, checkfirst=True))
            await connection.run_sync(lambda sync: ReflectionSource.__table__.create(sync, checkfirst=True))
            await connection.run_sync(lambda sync: Reminder.__table__.create(sync, checkfirst=True))
            await connection.run_sync(lambda sync: AccountToken.__table__.create(sync, checkfirst=True))
            await connection.run_sync(lambda sync: PreviewSchedule.__table__.create(sync, checkfirst=True))
            await connection.run_sync(add_photo_columns)
            await connection.run_sync(add_account_and_delivery_columns)
    from app.services.scheduler import scheduler_loop
    task = asyncio.create_task(scheduler_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    await engine.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins,
                   allow_credentials=True, allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
                   allow_headers=["Content-Type"])


@app.middleware("http")
async def protect_cookie_mutations(request: Request, call_next):
    if request.method in {"POST", "PATCH", "DELETE", "PUT"}:
        origin = request.headers.get("origin")
        if origin and origin not in settings.allowed_origins:
            return JSONResponse({"detail": "Origin is not allowed"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

app.include_router(api_v1_router, prefix=settings.api_v1_prefix)
