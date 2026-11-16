"""Small additive SQLite upgrade for existing local development databases."""
from sqlalchemy import inspect, text


def add_photo_columns(connection):
    inspector = inspect(connection)
    for table in ("captures", "messages"):
        if table in inspector.get_table_names() and "photo_data" not in {column["name"] for column in inspector.get_columns(table)}:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN photo_data TEXT"))


def add_account_and_delivery_columns(connection):
    inspector = inspect(connection)
    tables = set(inspector.get_table_names())
    if "users" in tables and "email_verified_at" not in {column["name"] for column in inspector.get_columns("users")}:
        connection.execute(text("ALTER TABLE users ADD COLUMN email_verified_at DATETIME"))
        connection.execute(text("UPDATE users SET email_verified_at = CURRENT_TIMESTAMP"))
    if "user_preferences" in tables and "notification_email_enabled" not in {column["name"] for column in inspector.get_columns("user_preferences")}:
        connection.execute(text("ALTER TABLE user_preferences ADD COLUMN notification_email_enabled BOOLEAN NOT NULL DEFAULT 0"))
    if "reminders" in tables:
        fields = {column["name"] for column in inspector.get_columns("reminders")}
        if "delivery_status" not in fields:
            connection.execute(text("ALTER TABLE reminders ADD COLUMN delivery_status VARCHAR(24) NOT NULL DEFAULT 'pending'"))
        if "delivered_at" not in fields:
            connection.execute(text("ALTER TABLE reminders ADD COLUMN delivered_at DATETIME"))
