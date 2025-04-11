
from models import Units
from sqlmodel import Session, select
from typing import Optional
from .db import engine


class UnitsRepository:
    def save(self, record: Units) -> Units:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    def find_by_mfid(self, mfid: str) -> Optional[Units]:
        with Session(engine) as session:
            statement = select(Units).where(
                Units.mfid == mfid
            )
            return session.exec(statement).first()
        
    def find_all_distinct_mfids(self) -> list[str]:
        """Fetch all distinct MFIDs from the database."""
        with Session(engine) as session:
            statement = select(Units.mfid).distinct()
            return session.exec(statement).all()
    
    def find_all(self) -> list:
        with Session(engine) as session:
            statement = select(Units)
            return session.exec(statement).all()
        