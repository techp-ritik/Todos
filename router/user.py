from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from bcrypt import hashpw, gensalt
from app.db import get_session
from app.models import Register_User, User

user_router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

def hash_password(password: str) -> str:
    """Hashes the user's password securely."""
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")

def get_user_from_db(session: Session, username: str, email: str):
    """Check if a user already exists in the database."""
    return session.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

@user_router.post("/register")
async def register_user(
    new_user: Annotated[Register_User, Depends()],
    session: Annotated[Session, Depends(get_session)]
):
    """Register a new user by adding their credentials to the database."""
    # Check if the user already exists
    db_user = get_user_from_db(session, new_user.username, new_user.email)
    if db_user:
        raise HTTPException(
            status_code=409, detail="User with these credentials already exists"
        )

    # Hash the password
    hashed_password = hash_password(new_user.password)

    # Create and store the user in the database
    user = User(
        username=new_user.username,
        email=new_user.email,
        password=hashed_password,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"message": f"User '{user.username}' successfully registered"}
