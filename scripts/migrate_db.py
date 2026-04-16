#!/usr/bin/env python3
"""Create Cloud SQL tables. Run once after terraform apply."""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from app.database import Base
from app import models  # noqa: F401 - registers models

DATABASE_URL = os.environ["DATABASE_URL"]


async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created")


if __name__ == "__main__":
    asyncio.run(migrate())
