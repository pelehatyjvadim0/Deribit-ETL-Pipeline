from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, mapped_column
from sqlalchemy import Numeric, BigInteger, String, Float, DateTime
from decimal import Decimal

class BaseModel(MappedAsDataclass, DeclarativeBase):
    pass

class CurrencyTick(BaseModel):
    __tablename__ = 'ticks'
    
    id: Mapped[int] = mapped_column(primary_key=True, init = False)
    ticker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8), nullable = False)
    timestamp: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)