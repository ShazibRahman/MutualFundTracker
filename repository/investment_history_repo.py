from sqlmodel import Session, select
from typing import List, Literal, Optional
from datetime import date
from sqlalchemy import Tuple, asc, desc, func
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

    def find_by_mfid(
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

    def delete_by_id(self, record_id: int) -> bool:
        with Session(engine) as session:
            obj = session.get(InvestmentHistory, record_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    def get_aggregated_data_by_date(self):
        with Session(engine) as session:
            statement = (
                select(
                    InvestmentHistory.date,
                    func.sum(InvestmentHistory.invested_amount).label("total_invested_amount"),
                    func.sum(InvestmentHistory.current_amount).label("total_current_amount"),
                    func.sum(InvestmentHistory.day_change).label("total_day_change")
                )
                .group_by(InvestmentHistory.date)
                .order_by(InvestmentHistory.date)
            )
            results = session.exec(statement).all()
            return [dict(row._mapping) for row in results]
        
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
