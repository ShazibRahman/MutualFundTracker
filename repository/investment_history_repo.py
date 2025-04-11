from sqlmodel import Session, select
from typing import List, Literal, Optional
from datetime import date
from sqlalchemy import asc, desc, func
from models import InvestmentHistory
from .db import engine

OrderType = Literal["asc", "desc"]

class InvestmentHistoryRepository:

    def save(self, record: InvestmentHistory) -> InvestmentHistory:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def find_by_mfid_and_date(self, mfid: str, entry_date: date) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.mfid == mfid,
                InvestmentHistory.date == entry_date
            )
            return session.exec(statement).first()

    def find_all_by_mfid(
        self,
        mfid: str,
        order_by: str = "date",
        direction: OrderType = "asc"
    ) -> List[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).all()
        

    def find_by_mfid_and_date_range(
        self,
        mfid: str,
        start_date: date,
        end_date: date,
        order_by: str = "date",
        direction: OrderType = "asc"
    ) -> List[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(InvestmentHistory)
                .where(
                    InvestmentHistory.mfid == mfid,
                    InvestmentHistory.date >= start_date,
                    InvestmentHistory.date <= end_date
                )
                .order_by(order_func(order_column))
            )
            return session.exec(statement).all() 

    def find_all(self) -> List[InvestmentHistory]:
        with Session(engine) as session:
            return session.exec(select(InvestmentHistory)).all()

        
    def find_first_by_mfid_order_by_date_desc(self, mfid: str) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, "date")
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(desc(order_column))
                .limit(1)
            )
            result = session.exec(statement).first()
            return result
        
    def find_first_by_mfid_order_by_updated_at_desc(self, mfid: str) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, "updated_at")
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(desc(order_column))
                .limit(1)
            )
            result = session.exec(statement).first()
            return result
        
    def find_first_by_mfid_order_by_date_asc(self, mfid: str) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, "date")
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(asc(order_column))
                .limit(1)
            )
            result = session.exec(statement).first()
            return result
    
    def find_by_mfid_and_date(self, mfid: str, entry_date: date) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.mfid == mfid,
                InvestmentHistory.date == entry_date
            )
            return session.exec(statement).first()
        
    def find_all_by_date(self, entry_date: date) -> List[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.date == entry_date
            )
            return session.exec(statement).all()
        

    def find_all_distinct_mfids_and_name(self) -> List[dict[str, str]]:
        with Session(engine) as session:
            statement = (
                select(
                    InvestmentHistory.mfid,
                    InvestmentHistory.mfname
                )
                .distinct()
            )
            results = session.exec(statement).all()
            
            # list of dict
            return [dict(row._mapping) for row in results]
        

    def find_first_by_mfid_order_by(
            self,
            mfid: str,
            order_by: str = "nav_date",
            direction: OrderType = "asc"
    ) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).first()
        

    def find_first_by_mfid_order_by(
            self,
            mfid: str,
            order_by: str = "date",
            direction: OrderType = "asc"
    ) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).first()
        
    def find_latest_records_for_all_mfids(self) -> List[InvestmentHistory]:
        """Fetch the latest record for each MFID."""
        with Session(engine) as session:
            subquery = (
                select(
                    InvestmentHistory.mfid,
                    func.max(InvestmentHistory.date).label("latest_date")
                )
                .group_by(InvestmentHistory.mfid)
                .subquery()
            )

            statement = (
                select(InvestmentHistory)
                .join(
                    subquery,
                    (InvestmentHistory.mfid == subquery.c.mfid) &
                    (InvestmentHistory.date == subquery.c.latest_date)
                )
            )

            return session.exec(statement).all()