from typing import List, Literal, Optional, Sequence
from datetime import date

from sqlmodel import Session, select
from sqlalchemy import asc, desc, func

from models import InvestmentHistory
from .db import engine

OrderType = Literal["asc", "desc"]

class InvestmentHistoryRepository:

    @staticmethod
    def save(record: InvestmentHistory) -> InvestmentHistory:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            session.flush()
            return record
    @staticmethod
    def find_by_mfid_and_date(mfid: str, entry_date: date) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.mfid == mfid,
                InvestmentHistory.date == entry_date
            )

            return session.exec(statement).first()
    @staticmethod
    def find_all_by_mfid(
            mfid: str,
        order_by: str = "date",
        direction: OrderType = "asc"
    ) -> Sequence[InvestmentHistory]:
        with Session(engine) as session:
            order_column = getattr(InvestmentHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(InvestmentHistory)
                .where(InvestmentHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).all()
        
    @staticmethod
    def find_by_mfid_and_date_range(
        mfid: str,
        start_date: date,
        end_date: date,
        order_by: str = "date",
        direction: OrderType = "asc"
    ) -> Sequence[InvestmentHistory]:
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
    @staticmethod
    def find_all() -> Sequence[InvestmentHistory]:
        with Session(engine) as session:
            return session.exec(select(InvestmentHistory)).all()


    @staticmethod
    def find_first_by_mfid_order_by_date_desc(mfid: str) -> Optional[InvestmentHistory]:
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

    @staticmethod
    def find_first_by_mfid_order_by_updated_at_desc(mfid: str) -> Optional[InvestmentHistory]:
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
    @staticmethod
    def find_first_by_mfid_order_by_date_asc(mfid: str) -> Optional[InvestmentHistory]:
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
    @staticmethod
    def find_by_mfid_and_date(mfid: str, entry_date: date) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.mfid == mfid,
                InvestmentHistory.date == entry_date
            )
            return session.exec(statement).first()
    @staticmethod
    def find_all_by_date(entry_date: date) -> Sequence[InvestmentHistory]:
        with Session(engine) as session:
            statement = select(InvestmentHistory).where(
                InvestmentHistory.date == entry_date
            )
            return session.exec(statement).all()
        
    @staticmethod
    def find_all_distinct_mfids_and_name() -> List[dict[str, str]]:
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
        

    @staticmethod
    def find_first_by_mfid_order_by(
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
    @staticmethod
    def find_latest_records_for_all_mfids() -> Sequence[InvestmentHistory]:
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
    @staticmethod
    def find_second_latest_by_mfid(
            mfid: str
) -> Optional[InvestmentHistory]:
        with Session(engine) as session:
            # Subquery to filter and order records by date in descending order
            subquery = (
                select(InvestmentHistory)
                .where(
                    InvestmentHistory.mfid == mfid,
                )
                .order_by(desc(InvestmentHistory.date))  # Order by date descending
                .offset(1)  # Skip the first record (latest)
                .limit(1)   # Fetch only the second record
            )

            # Execute the query and return the result
            result = session.exec(subquery).first()
            return result