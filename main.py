from fastapi import FastAPI, Depends, HTTPException, Request, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from datetime import time, timedelta
from time import perf_counter
from sqlalchemy.orm import Session
from database import get_db, APILogDB
import crud
from auth import (
   create_access_token, get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from fastapi.middleware.cors import CORSMiddleware
from models import User, UserCreate, ApiLog
from starlette.concurrency import iterate_in_threadpool
from starlette.background import BackgroundTask
from background import write_log
from typing import Optional, List
import datetime as dt


app = FastAPI(title="Authentication Demo", version="1.0.0")
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Specify domains as needed, '*' allows all domains
        allow_credentials=True,
        allow_methods=["*"],  # Or specify methods like ["GET", "POST"]
        allow_headers=["*"],  # Or specify headers as needed
    )



@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Authentication Demo"}


@app.middleware("http")
async def middleware(request: Request, call_next):
    try:
        req_body = await request.json()
    except Exception:
        req_body = None

    start_time = perf_counter()
    response = await call_next(request)
    process_time = perf_counter() - start_time

    res_body = [section async for section in response.body_iterator]
    response.body_iterator = iterate_in_threadpool(iter(res_body))
    res_body = res_body[0].decode()

    # Add the background task to the response object to queue the job
    response.background = BackgroundTask(write_log, request, response, req_body, res_body, process_time)
    return response


@app.post("/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = crud.create_user(db=db, user=user)
    return User(
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        disabled=not new_user.is_active,
    )

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token."""
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@app.get("/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    return {"message": f"Hello {current_user.full_name}, this is a protected route!"}


@app.get("/logs/", response_model=List[ApiLog])
def get_api_logs(
    start_date: Optional[dt.datetime] = Query(
        None, description="Filter logs from this date (ISO 8601 format)"
    ),
    end_date: Optional[dt.datetime] = Query(
        None, description="Filter logs up to this date (ISO 8601 format)"
    ),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(APILogDB)

    # Apply date filters if provided
    if start_date:
        # Use >= for the start date
        query = query.filter(APILogDB.created_at >= start_date)

    if end_date:
        # Use <= for the end date to include the entire end day
        query = query.filter(APILogDB.created_at <= end_date)
        
    # Optional: Add ordering (newest first)
    query = query.order_by(APILogDB.created_at.desc())

    logs = query.all()
    return logs