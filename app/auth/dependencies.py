from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.user import User


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    error = HTTPException(
        status_code=401,
        detail="Invalid token",
    )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        email = payload.get("sub")

    except JWTError:
        raise error

    if email is None:
        raise error

    user = db.query(User).filter(
        User.email == email
    ).first()

    if user is None:
        raise error

    return user

def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required",
        )

    return current_user