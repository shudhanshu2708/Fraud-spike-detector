
from fastapi import  APIRouter , Depends , HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.redis_client import redis_client
from app.auth.security import hash_password , verify_password , create_access_token
from app.auth.security import store_refresh_token , create_refresh_token
from app.schemas.auth import UserSignup , UserLogin , TokenResponse , RefreshRequest 


router = APIRouter()



@router.post("/signup" , response_model=TokenResponse)
def sign_up(user_data: UserSignup , db: Session = Depends(get_db)):

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
    

@router.post("/refresh")
def refresh( data: RefreshRequest):
    email = redis_client.get(f"refresh_token:{data.refresh_token}")

    if not email:
        raise HTTPException(status_code=401 , detail="Invalid or expired refresh token")

    redis_client.delete(f"refresh_token:{data.refresh_token}")
    access_token = create_access_token( data={"sub" : email})
    refresh_token = create_refresh_token()
    store_refresh_token(email , refresh_token)
    return TokenResponse(access_token=access_token , refresh_token=refresh_token)


    #refresh_token = refresh_token : {token}
    


@router.post("/logout")
def log_out():
    return {"logout" : "okk"}

@router.get("/me")
def me():
    return {"me": "okk"}

@router.post("/change-passowrd")
def change_password():
    return {"changepassword" : "okk"}

@router.post("/logout-all")
def logout_all():
    return {"all device log out" : "okk"}