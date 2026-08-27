
from fastapi import  APIRouter , Depends , HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    store_refresh_token,
    create_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
)
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    TokenResponse,
    RefreshRequest,
    ChangePasswordRequest,
)


router = APIRouter()



@router.post(
        "/signup" ,
          response_model=TokenResponse,
)
def sign_up(
    user_data: UserSignup ,
    db: Session = Depends(get_db),
):

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400 , detail="Email already registered")

    hashed_pw = hash_password(user_data.password)

    new_user = User(email=user_data.email , password_hash=hashed_pw)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.email})
    refresh_token = create_refresh_token()
    store_refresh_token(new_user.email , refresh_token)
    
    return TokenResponse(access_token=access_token , refresh_token=refresh_token)
    
    
    

@router.post("/login")
def login( user_data: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if not existing_user:
        raise HTTPException(status_code=401 , detail="Invalid Credentials")

    if not verify_password(user_data.password, existing_user.password_hash):
        raise HTTPException(status_code=401 , detail="Invalid Credentials")

    access_token = create_access_token(data={"sub": existing_user.email})
    refresh_token = create_refresh_token()
    store_refresh_token(existing_user.email, refresh_token)
    return TokenResponse(access_token=access_token , refresh_token=refresh_token)
    

@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest):
    email = revoke_refresh_token(data.refresh_token)

    if not email:
        raise HTTPException(
            status_code=401,
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
def log_out(
    data: RefreshRequest,
    current_user: User = Depends(get_current_user),
):
    email = revoke_refresh_token(data.refresh_token)

    if email is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    if email != current_user.email:
        raise HTTPException(
            status_code=403,
            detail="Refresh token does not belong to current user",
        )

    return {"logout": "ok"}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
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
):
    if not verify_password(
        data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect",
        )

    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=400,
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
):
    revoked = revoke_all_refresh_tokens(
        current_user.email
    )

    return {
        "logout_all": "ok",
        "sessions_revoked": revoked,
    }