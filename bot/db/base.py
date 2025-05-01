from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import glv
# Движок
engine = create_async_engine(glv.config["DB_URL"], echo=True)

# Сессия
async_session_maker = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

Base = declarative_base()