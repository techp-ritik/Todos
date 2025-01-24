from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Field, create_engine, Session, select
from app import setting
from typing import Annotated
from contextlib import asynccontextmanager
from app.auth import EXPIRY_TIME, authenticate_user, create_access_token, current_user, validate_refresh_token, create_refresh_token
from app.db import get_session, create_tables
from app.models import Todo, Todo_Create, Todo_Edit, Token, User
from app.router import user


@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Creating Tables')
    create_tables()
    print("Tables Created")
    yield


app: FastAPI = FastAPI(
    lifespan=lifespan, title="dailyDo Todo App", version='1.0.0')

app.include_router(router=user.user_router)

@app.get('/')
async def root():
    return {"message": "Welcome to dailyDo todo app"}


# login . username, password
@app.post('/token', response_model=Token)
async def login(form_data:Annotated[OAuth2PasswordRequestForm, Depends()],
                session:Annotated[Session, Depends(get_session)]):
    user = authenticate_user (form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    expire_time = timedelta(minutes=EXPIRY_TIME)
    access_token = create_access_token({"sub":form_data.username}, expire_time)

    refresh_expire_time = timedelta(days=7)
    refresh_token = create_refresh_token({"sub":user.email}, refresh_expire_time)

    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)




@app.post('/todos/', response_model=dict)
async def create_todo(
    current_user: Annotated[User, Depends(current_user)],
    todo: Todo_Create,
    session: Annotated[Session, Depends(get_session)]
):
    new_todo = Todo(content=todo.content, user_id=current_user.id)

    session.add(new_todo)
    session.commit()
    session.refresh(new_todo)

    return {
        "success": True,
        "message": "Todo successfully created",
        "todo": new_todo,
        "username": current_user.username,
        "timestamp": datetime.utcnow()  # Assuming you're using `datetime` from the `datetime` module
    }



@app.get('/todos/', response_model=dict)
async def get_all(
    current_user: Annotated[User, Depends(current_user)],
    session: Annotated[Session, Depends(get_session)]
):
    todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()

    if todos:
        return {"username": current_user.username, "todos": todos}
    else:
        raise HTTPException(status_code=404, detail="No Task found")


@app.get('/todos/{id}', response_model=dict)
async def get_single_todo(id: int, 
                          current_user:Annotated[User, Depends(current_user)],
                          session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    matched_todo = next((todo for todo in user_todos if todo.id == id),None)

    if matched_todo:
        return {
                "todos" : matched_todo,
                "username" : current_user.username
                }
    else:
        raise HTTPException(status_code=404, detail="No Task found")

@app.put('/todos/{id}')
async def edit_todo(id: int, 
                    todo: Todo_Edit,
                    current_user:Annotated[User, Depends(current_user)], 
                    session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    existing_todo = next((todo for todo in user_todos if todo.id == id),None)

    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException(status_code=404, detail="No task found")


@app.delete('/todos/{id}')
async def delete_todo(id: int,
                      current_user:Annotated[User, Depends(current_user)],
                      session: Annotated[Session, Depends(get_session)]):
    
    user_todos = session.exec(select(Todo).where(Todo.user_id == current_user.id)).all()
    todo = next((todo for todo in user_todos if todo.id == id),None)
    
    if todo:
        session.delete(todo)
        session.commit()
        # session.refresh(todo)
        return {"message": "Task successfully deleted"}
    else:
        raise HTTPException(status_code=404, detail="No task found")
