from __future__ import annotations

import os
from typing import AsyncGenerator

from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./smartchain.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class SKU(Base):
    __tablename__ = "skus"
    id = Column(String, primary_key=True)
    name = Column(String)
    current_stock = Column(Integer)
    current_price = Column(Float)
    days_on_hand = Column(Integer)
    sell_through = Column(Float)

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String, ForeignKey("skus.id"))
    sold_on = Column(Date)
    quantity = Column(Integer)

async_session_maker = AsyncSessionLocal

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

