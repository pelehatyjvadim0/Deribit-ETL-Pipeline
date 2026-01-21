import time
from typing import Annotated
from fastapi import Depends 

from app.core.database import new_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_current_time() -> int:
    return int(time.time())

CurrentTimeDep = Annotated[int, Depends(get_current_time)]

async def get_session():
    async with new_session() as session:
        yield session
        
SessionDep = Annotated[AsyncSession, Depends(get_session)]