from typing import Literal, Optional, Sequence
from datetime import date

from sqlmodel import Session, select
from sqlalchemy import asc, desc

from models import OrderHistory
from .db import engine

OrderType = Literal["asc", "desc"]


class OrderHistoryRepository:
    @staticmethod
    def save(record: OrderHistory) -> OrderHistory:
        with Session(engine) as session:
            session.add(record)
            session.commit()
            session.refresh(record)
            session.flush()
            return record

    @staticmethod
    def find_by_mfid_and_date(mfid: str, entry_date: date) -> Optional[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.mfid == mfid, OrderHistory.nav_date == entry_date
            )
            return session.exec(statement).first()

    @staticmethod
    def find_all() -> Sequence[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory)
            return session.exec(statement).all()

    @staticmethod
    def find_by_mfid(
        mfid: str, order_by: str = "nav_date", direction: OrderType = "asc"
    ) -> Sequence[OrderHistory]:
        with Session(engine) as session:
            order_column = getattr(OrderHistory, order_by)
            order_func = asc if direction == "asc" else desc
            statement = (
                select(OrderHistory)
                .where(OrderHistory.mfid == mfid)
                .order_by(order_func(order_column))
            )
            return session.exec(statement).all()

    @staticmethod
    def delete_by_id(record_id: int) -> bool:
        with Session(engine) as session:
            obj = session.get(OrderHistory, record_id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    @staticmethod
    def find_first_by_mfid(
        mfid: str, order_by: str = "nav_date", direction: OrderType = "asc"
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

    @staticmethod
    def find_first_by_mfid_order_by_date(
        mfid: str, order_by: str = "nav_date", direction: OrderType = "asc"
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

    @staticmethod
    def find_first_by_mfid_order_by_updated_at_desc(
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

    @staticmethod
    def find_first_by_mfid_order_by_updated_at_asc(
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

    @staticmethod
    def find_all_by_date(nav_date: date) -> Sequence[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(OrderHistory.nav_date == nav_date)
            return session.exec(statement).all()

    @staticmethod
    def find_all_by_nav_is_null() -> Sequence[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(OrderHistory.nav.is_(None))
            return session.exec(statement).all()

    @staticmethod
    def find_all_consumed_is(consumed: bool = False) -> Sequence[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(OrderHistory.consumed.is_(consumed))
            return session.exec(statement).all()

    @staticmethod
    def find_all_by_mfid_and_consumed(
        mfid: str, consumed: bool = False
    ) -> Sequence[OrderHistory]:
        with Session(engine) as session:
            statement = select(OrderHistory).where(
                OrderHistory.mfid == mfid, OrderHistory.consumed.is_(consumed)
            )
            return session.exec(statement).all()

    @staticmethod
    def find_all_by_consumed(consumed: bool = False) -> Sequence[OrderHistory]:
        with Session(engine) as session:
            consumed_value = int(consumed)  # Converts True -> 1, False -> 0

            statement = select(OrderHistory).where(
                OrderHistory.consumed == consumed_value
            )
            return session.exec(statement).all()

    @staticmethod
    def find_first_by_mfid_order_by(
        mfid: str, order_by: str = "nav_date", direction: OrderType = "asc"
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
