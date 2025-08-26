"""Authentication utilities and JWT token management."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import Boolean, DateTime, String, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())  # JWT ID for token revocation
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            return None
        
        if datetime.now(timezone.utc) > datetime.fromtimestamp(exp, tz=timezone.utc):
            return None
        
        return payload
    
    except JWTError:
        return None


async def store_refresh_token(
    db: AsyncSession, 
    token: str, 
    user_id: uuid.UUID
) -> RefreshToken:
    """Store a refresh token in the database."""
    # Decode token to get expiration
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    
    refresh_token_record = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    db.add(refresh_token_record)
    await db.commit()
    await db.refresh(refresh_token_record)
    
    return refresh_token_record


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[dict]:
    payload = verify_token(token, token_type="refresh")
    if not payload:
        return None
    
    stmt = select(RefreshToken).where(
        RefreshToken.token == token,
        RefreshToken.is_revoked == False  # noqa: E712
    )
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()
    
    if not token_record:
        return None
    
    now = datetime.now(timezone.utc)
    if token_record.expires_at.replace(tzinfo=timezone.utc) < now:
        return None
    
    return payload


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    stmt = select(RefreshToken).where(RefreshToken.token == token)
    result = await db.execute(stmt)
    token_record = result.scalar_one_or_none()
    
    if token_record:
        token_record.is_revoked = True
        await db.commit()
        return True
    
    return False


async def revoke_all_user_tokens(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = select(RefreshToken).where(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False  # noqa: E712
    )
    result = await db.execute(stmt)
    tokens = result.scalars().all()
    
    count = 0
    for token in tokens:
        token.is_revoked = True
        count += 1
    
    await db.commit()
    return count


async def cleanup_expired_tokens(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    stmt = select(RefreshToken).where(RefreshToken.expires_at < now)
    result = await db.execute(stmt)
    expired_tokens = result.scalars().all()
    
    count = len(expired_tokens)
    for token in expired_tokens:
        await db.delete(token)
    
    await db.commit()
    return count
