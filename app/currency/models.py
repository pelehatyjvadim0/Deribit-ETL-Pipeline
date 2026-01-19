from sqlalchemy.orm import Mapped, mapped_column, MappedAsDataclass, DeclarativeBase
from sqlalchemy import Numeric, BigInteger, String, Float, DateTime
from decimal import Decimal
from app.core.models import BaseModel

class CurrencyTick(BaseModel):
    __tablename__ = 'ticks'
    
    id: Mapped[int] = mapped_column(primary_key=True, init = False)
    ticker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    # Numeric = Decimal, 1 аргумент цифр всего, второй - цифр после запятой
    price: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8), nullable = False)
    timestamp: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)