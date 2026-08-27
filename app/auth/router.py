from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_all_refresh_tokens,
    revoke_refresh_token,
    store_refresh_token,
    verify_password,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    RefreshRequest,
    TokenResponse,
    UserLogin,
    UserSignup,
)
from app.services.rate_limiting import check_rate_limit


router = APIRouter()


@router.post(
    "/signup",
    response_model=TokenResponse,
)
def sign_up(
    request: Request,
    user_data: UserSignup,
    db: Session = Depends(get_db),
) -> TokenResponse:
    check_rate_limit(
        request=request,
        limit=5,
        window_seconds=60,
        key_suffix="signup",
    )

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(
        data={"sub": new_user.email}
    )
    refresh_token = create_refresh_token()

    store_refresh_token(
        new_user.email,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db),
) -> TokenResponse:
    check_rate_limit(
        request=request,
        limit=10,
        window_seconds=60,
        key_suffix="login",
    )

    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user or not verify_password(
        user_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
        )

    access_token = create_access_token(
        data={"sub": user.email}
    )
    refresh_token = create_refresh_token()

    store_refresh_token(
        user.email,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    request: Request,
    data: RefreshRequest,
) -> TokenResponse:
    check_rate_limit(
        request=request,
        limit=20,
        window_seconds=60,
        key_suffix="refresh",
    )

    email = revoke_refresh_token(data.refresh_token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(
        data={"sub": email}
    )
    refresh_token = create_refresh_token()

    store_refresh_token(
        email,
        refresh_token,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
def logout(
    data: RefreshRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    email = revoke_refresh_token(data.refresh_token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Refresh token does not belong to current user",
        )

    return {"logout": "ok"}


@router.get("/me")
def me(
    current_user: User = Depends(get_current_user),
) -> dict:
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at,
    }


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not verify_password(
        data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different",
        )

    current_user.password_hash = hash_password(
        data.new_password
    )

    db.commit()

    revoke_all_refresh_tokens(
        current_user.email
    )

    return {
        "message": "Password changed successfully"
    }


@router.post("/logout-all")
def logout_all(
    current_user: User = Depends(get_current_user),
) -> dict[str, int | str]:
    revoked = revoke_all_refresh_tokens(
        current_user.email
    )

    return {
        "logout_all": "ok",
        "sessions_revoked": revoked,
    }