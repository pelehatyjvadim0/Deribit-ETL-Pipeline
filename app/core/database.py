from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL)

new_session = async_sessionmaker(bind=engine, expire_on_commit=False)