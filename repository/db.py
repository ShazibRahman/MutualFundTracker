from pathlib import Path

from sqlmodel import create_engine, SQLModel

db_path = Path(__file__).parent / "investment.db"
DATABASE_URL = f"sqlite:///{db_path.as_posix()}"
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create the database and tables."""
    SQLModel.metadata.create_all(engine)
