from fastapi.security import OAuth2PasswordBearer 
from fastapi import Depends , HTTPException
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    error = HTTPException(status_code=401 , detail="Invalid token")

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email = payload.get("sub")
    except JWTError:
        raise error

    if email is None:
       raise error 

    user = db.query(User).filter(User.email == email).first()

    if user is None:
      raise error 

    return user