from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date
from sqlalchemy import UniqueConstraint

class InvestmentHistory(SQLModel, table=True):
    __tablename__ = "investment_history"
    __table_args__ = (
        UniqueConstraint("mfid", "date", name="uix_mfid_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mfid: str
    mfname: Optional[str] = None  # ✅ Make nullable
    date: date
    invested_amount: float
    current_amount: float
    day_change: Optional[float] = None
    nav: Optional[float] = None



class OrderHistory(SQLModel, table=True):
    __tablename__ = "order_history"
    __table_args__ = (
        UniqueConstraint("mfid", "nav_date", name="uix_mfid_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    mfid: str
    mfname: str
    nav_date: Optional[date] = None
    amount: float
    unit: float
    nav: Optional[float] = None