from fastapi import APIRouter, Depends, HTTPException, status, Form
from ..auth import create_access_token

router = APIRouter()

@router.post("/token")
def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    if username != "admin" or password != "password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer"}
