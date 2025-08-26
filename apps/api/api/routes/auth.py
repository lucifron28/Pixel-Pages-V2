import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    revoke_all_user_tokens,
    revoke_refresh_token,
    store_refresh_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from ..database import get_database_session
from ..dependencies import get_current_user, verify_refresh_token_cookie
from ..models import User
from ..schemas import (
    MessageResponse,
    TokenRefreshResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_database_session)
):
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)


@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_database_session)
):
    stmt = select(User).where(User.email == user_credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    await store_refresh_token(db, refresh_token, user.id)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # 30 days in seconds
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax"
    )
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    payload: dict = Depends(verify_refresh_token_cookie),
    db: AsyncSession = Depends(get_database_session)
):
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    
    stmt = select(User).where(User.id == user_uuid)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return TokenRefreshResponse(access_token=access_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    payload: dict = Depends(verify_refresh_token_cookie),
    db: AsyncSession = Depends(get_database_session)
):
    refresh_token = payload.get("jti")  # JWT ID
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    # NOTE: In a more sophisticated setup, add the access token
    # to a blacklist, but for simplicity, we're just revoking the refresh token
    
    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    response: Response,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    revoked_count = await revoke_all_user_tokens(db, current_user.id)
    
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return MessageResponse(message=f"Logged out from all devices. Revoked {revoked_count} tokens.")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: UserResponse = Depends(get_current_user)
):
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    old_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
):
    stmt = select(User).where(User.id == current_user.id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    
    await revoke_all_user_tokens(db, user.id)
    
    return MessageResponse(message="Password changed successfully. Please log in again.")
