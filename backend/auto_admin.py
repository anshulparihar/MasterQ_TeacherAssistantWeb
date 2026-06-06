import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def make():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.email == 'admin@test.com'))
        if not result.scalars().first():
            db.add(User(email='admin@test.com', full_name='Admin', hashed_password=hash_password('password123'), is_admin=True))
            await db.commit()
            print("Admin created")
        else:
            print("Admin exists")

asyncio.run(make())
