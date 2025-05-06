# utils/db.py

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from decouple import config

# ——— Database Configuration ——————————————————————————
# Load your DATABASE_URL from environment (.env)
DATABASE_URL = config("DATABASE_URL")

# ——— Engine Creation ————————————————————————————
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True  # Ensures connections are alive before use
)

# ——— Session Factory ———————————————————————————
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# ——— Utility Functions ———————————————————————————

def test_connection() -> None:
    """
    Execute a simple SELECT 1 to verify DB connectivity.
    Raises an exception if the connection or query fails.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ DB connection OK")
    except Exception as e:
        print(f"❌ DB connection failed: {e}")
        raise


def list_tables(schema: str = "public") -> list[str]:
    """
    Return a list of table names in the given schema.
    """
    insp = inspect(engine)
    return insp.get_table_names(schema=schema)


def print_schema(schema: str = "public") -> None:
    """
    Print all tables and their columns/types in the given schema.
    """
    insp = inspect(engine)
    tables = insp.get_table_names(schema=schema)
    print("🔍 Tables in schema:", schema)
    for tbl in tables:
        print(f"\n• {tbl}")
        cols = insp.get_columns(tbl, schema=schema)
        for c in cols:
            name = c.get("name")
            typ = c.get("type")
            nullable = c.get("nullable", False)
            print(f"   – {name} ({typ}){' NULL' if nullable else ''}")
