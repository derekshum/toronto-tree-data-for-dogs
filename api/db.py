import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine() -> Engine:
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://localdb:local@localhost:5434/localdb"
    )
    return create_engine(db_url)
