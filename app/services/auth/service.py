from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models import User
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, payload: UserRegister) -> UserOut:
    existing = await get_user_by_email(db, payload.email)
    if existing is not None:
        raise AuthError("email already registered", status_code=409)

    user = User(
        email=payload.email.lower(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


async def login_user(db: AsyncSession, payload: UserLogin) -> Token:
    user = await get_user_by_email(db, payload.email.lower())
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthError("invalid email or password", status_code=401)
    if not user.is_active:
        raise AuthError("account is disabled", status_code=403)

    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)
