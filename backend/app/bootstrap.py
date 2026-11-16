"""Create a fresh SQLite development database. PostgreSQL uses Alembic."""
import asyncio
from app.core import engine, settings
from app.models import Base
from app.sqlite_upgrade import add_photo_columns, add_account_and_delivery_columns

async def main():
    if settings.db_driver != "sqlite+aiosqlite":
        raise SystemExit("For PostgreSQL run: python -m alembic upgrade head")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.run_sync(add_photo_columns)
        await connection.run_sync(add_account_and_delivery_columns)
    await engine.dispose()
    print("Local database ready. Existing records were preserved.")

if __name__ == "__main__":
    asyncio.run(main())
