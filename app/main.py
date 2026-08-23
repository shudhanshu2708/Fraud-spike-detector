from fastapi import FastAPI
from app.database import Base , engine
from app.models.user import User
from app.auth.router import router as auth_router
from app.config import settings
#print(settings.database_url)

app = FastAPI(title="Vendly", version="0.1.0")

Base.metadata.create_all(bind=engine)
app.include_router(auth_router, prefix="/auth" , tags=["auth"])

@app.get("/health")
def health_check():
    return {"status": "okk"}


