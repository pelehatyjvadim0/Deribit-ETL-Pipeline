from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from decimal import Decimal
import time
from enum import Enum

class CurrencyTicker(str, Enum):
    BTC_USD = "btc_usd"
    ETH_USD = "eth_usd"

class STickResponse(BaseModel):
    ticker: str
    price: Decimal
    timestamp: int
    
    model_config = ConfigDict(from_attributes=True)
    
class SPriceRequest(BaseModel):
    ticker: CurrencyTicker
    start_timestamp: int
    end_timestamp: int

    @field_validator("start_timestamp", "end_timestamp")
    @classmethod
    def validate_timestamp(cls, v: int):
        # 10**11 — это граница между секундами и миллисекундами
        # в 2026 году секунды - это ~1.7*10^9, миллисекунды - ~1.7*10^12
        if v < 10**11: 
            # Похоже на секунды, конвертируем в миллисекунды
            return v * 1000
        
        # Защита от слишком огромных чисел (больше 15 цифр/микросекнд)
        if v > 10**14:
            raise ValueError("Timestamp слишком длинный (возможно, это микросекунды)")
            
        return v
    
    @model_validator(mode='after')
    def check_logic(self) -> 'SPriceRequest':
        if self.end_timestamp < self.start_timestamp:
            raise ValueError('Конец периода не может быть раньше начала!')
        
        now_ms = int(time.time() * 1000)
        if self.start_timestamp > now_ms * 60000:
            raise ValueError('Вы пытаетесь запросить данные из будущего!')
        
        return self