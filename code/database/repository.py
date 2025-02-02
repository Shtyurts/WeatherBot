# database/repository.py
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Place

class UserRepository:
    @staticmethod
    async def get_or_create(session: AsyncSession, telegram_id: int) -> User:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            await session.commit()
        return user

class PlaceRepository:
    @staticmethod
    async def create(
        session: AsyncSession, 
        user_id: int, 
        name: str, 
        lat: float, 
        lon: float
    ) -> Place:
        place = Place(name=name, lat=lat, lon=lon, user_id=user_id)
        session.add(place)
        await session.commit()
        return place

    @staticmethod
    async def get_all(session: AsyncSession, user_id: int) -> list[Place]:
        result = await session.execute(
            select(Place).where(Place.user_id == user_id)
        )
        return result.scalars().all()

    @staticmethod
    async def delete(session: AsyncSession, place_id: int, user_id: int) -> bool:
        result = await session.execute(
            delete(Place)
            .where(Place.id == place_id, Place.user_id == user_id)
        )
        await session.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def delete(session: AsyncSession, place_id: int, user_id: int) -> bool:
        result = await session.execute(
            delete(Place)
            .where(Place.id == place_id, Place.user_id == user_id)
        )
        await session.commit()
        return result.rowcount > 0