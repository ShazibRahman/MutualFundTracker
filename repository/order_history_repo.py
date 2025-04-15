from models import OrderHistory
from sqlmodel import Session, select
from typing import List, Literal, Optional
from datetime import date
from sqlalchemy import asc, desc, func
from .db import engine

OrderType = Literal["asc", "desc"]

class OrderHistoryRepository:
    def save(self, record: OrderHistory) -> OrderHistory:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
    
    def find_by_mfid_and_date(self, mfid: str, entry_date: date) -> Optional[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.mfid == mfid,
                OrderHistory.nav_date == entry_date
            )
            return session.exec(statement).first()
            

    
    def find_all(self) -> List[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory)
            return session.exec(statement).all()
        
    def find_by_mfid(
        self,
        mfid: str,
        order_by: str = "nav_date",
        direction: OrderType = "asc"
    ) -> List[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).all()
        

    def delete_by_id(self, record_id: int) -> bool:
        with Session(engine) as session:
            obj = session.get(OrderHistory, record_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False
        

    def find_first_by_mfid(
        self,
        mfid: str,
        order_by: str = "nav_date",
        direction: OrderType = "asc"
    ) -> Optional[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).first()


    def find_first_by_mfid_order_by_date(
        self,
        mfid: str,
        order_by: str = "nav_date",
        direction: OrderType = "asc"
    ) -> Optional[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).first()
        
    def find_first_by_mfid_order_by_updated_at_desc(
        self,
        mfid: str,
    ) -> Optional[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, "updated_at")
           
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(desc(order_column))
            )
            return session.exec(statement).first()
        

    def find_first_by_mfid_order_by_updated_at_asc(
        self,
        mfid: str,
    ) -> Optional[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, "updated_at")
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(asc(order_column))
            )
            return session.exec(statement).first()
        
    def find_all_by_date(self, nav_date: date) -> List[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.nav_date == nav_date
            )
            return session.exec(statement).all()
        
    def find_all_by_nav_is_null(
        self,
    ) -> List[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.nav.is_(None)
            )
            return session.exec(statement).all()
        

    def find_all_by_mfid_and_consumed(
        self,
        mfid: str,
        consumed: bool = False
    ) -> List[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.mfid == mfid,
                OrderHistory.consumed.is_(consumed)
            )
            return session.exec(statement).all()
        
    def find_all_by_consumed(
        self,
        consumed: bool = False
    ) -> List[OrderHistory]:
        with Session(engine) as session:
            consumed_value = int(consumed)  # Converts True -> 1, False -> 0

            statement = select(OrderHistory).where(
                OrderHistory.consumed == consumed_value
            )
            return session.exec(statement).all()

    def find_first_by_mfid_order_by(
            self,
            mfid: str,
            order_by: str = "nav_date",
            direction: OrderType = "asc"
    ) -> Optional[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).first(
    )