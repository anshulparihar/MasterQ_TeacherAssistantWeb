import asyncio
import getpass
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def create_admin():
    print("\n--- MasterQ Admin Creation ---")
    email = input("Enter admin email: ").strip()
    password = getpass.getpass("Enter admin password: ")
    confirm = getpass.getpass("Confirm admin password: ")

    if password != confirm:
        print("Error: Passwords do not match.")
        return
    
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long.")
        return

    async with AsyncSessionLocal() as db:
        async with db.begin():
            # Check if user already exists
            # (In SQLAlchemy 2.0 async, this requires execute, but for a simple script we can use direct execute)
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.email == email))
            existing_user = result.scalars().first()

            if existing_user:
                print(f"Error: User with email '{email}' already exists.")
                return

            # Create new admin user
            hashed_password = get_password_hash(password)
            new_admin = User(
                email=email,
                hashed_password=hashed_password,
                role="admin"
            )
            db.add(new_admin)
        
        # Commit happens automatically with db.begin() if no exception is raised
        print(f"\nSuccess! Admin user '{email}' created successfully.")

if __name__ == "__main__":
    asyncio.run(create_admin())
