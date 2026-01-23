from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette import status

from app.modules.users.models.user import User
from app.notifications.interfaces import EmailSenderInterface
from app.utils.interfaces import JWTAuthManagerInterface


class UserService:
    """
    Authentication service.
    Contains business logic for authentication and token handling.
    """

    def __init__(
        self,
        db: AsyncSession,
        jwt_manager: JWTAuthManagerInterface,
        login_time_days: int,
        email_sender: EmailSenderInterface | None = None,
        base_url: str = "http://localhost:8000",
    ):
        self._db = db
        self._jwt_manager = jwt_manager
        self._login_time_days = login_time_days
        self._email_sender = email_sender
        self._base_url = base_url


    async def _get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self._db.execute(stmt)
        return result.scalars().first()


    async def _get_user_by_id(self, user_id: int) -> User:
            result = await self._db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            return user


    async def activate_user_by_admin(self, user_id: int) -> None:
        user = await self._db.get(User, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.is_active:
            return

        user.is_active = True
        await self._db.commit()


    async def change_user_group(self, user_id: int, group_id: int) -> None:
        user = await self._db.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.group_id = group_id
        await self._db.commit()