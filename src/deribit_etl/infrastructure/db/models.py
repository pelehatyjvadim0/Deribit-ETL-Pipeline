"""SQLAlchemy mappings for stored quotes."""

from decimal import Decimal

from sqlalchemy import BigInteger, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base for Deribit ETL tables."""


class TickRecord(Base):
    """Persisted market-price observation."""

    __tablename__ = "ticks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
