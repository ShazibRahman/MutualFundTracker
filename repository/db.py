from pathlib import Path
from sqlmodel import create_engine, SQLModel
from models import InvestmentHistory  # make sure this is defined before creating table

target_metadata = SQLModel.metadata
db_path = Path(__file__).parent / "investment.db"
DATABASE_URL = f"sqlite:///{db_path.as_posix()}"
engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
