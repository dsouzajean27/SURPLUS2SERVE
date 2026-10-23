"""Tiny auto-migration: adds columns that newer versions of the models have but an existing
database table lacks (Base.metadata.create_all() only creates missing *tables*).
Safe to run on every start-up. Use Alembic if this project ever outgrows it."""
from sqlalchemy import inspect, text


def ensure_columns(engine, base) -> None:
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    for table in base.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue  # create_all() just made it with every column
        have = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in have:
                continue
            ddl_type = col.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl_type} NULL"))
