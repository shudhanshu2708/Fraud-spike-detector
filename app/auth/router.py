
from fastapi import FastAPI , APIRouter

router = APIRouter()



@router.post("/signup")
def sign_up():
    return {"signup": "okk"}

@router.post("/login")
def login():
    return {"login":"okk"}

@router.post("/refresh")
def refresh():
    return {"refresh" : "okk"}
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