from sqlmodel import Column, DateTime, SQLModel, Field,func
from typing import Optional
from datetime import datetime
from sqlalchemy import UniqueConstraint

class Units(SQLModel, table=True):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("mfid", name="unique_mfid"),)


    id: Optional[int] = Field(default=None, primary_key=True)
    mfid: str = Field(index=True)

    total_units: float = Field(default=0.0)

    total_invested: float = Field(default=0.0)  


    created_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=True)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    )

    

 