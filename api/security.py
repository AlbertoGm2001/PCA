import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from db.session import get_session
from models.models import User
from loguru import logger

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-it-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

#ALgorithm to hash passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#This schema will specify the endpoints that in order to use the endpoint,
#the request must include a token obtained from the auth/login endpoint 
#
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    #Method that hashes password to compare it with its stored hash
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    
    #Method that hashes password to store it in the database
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    #Method that creates an access token
    #Expires is the part of the token that specifies when the token expires
    #If no expires_delta is provided, the token will expire in 15 minutes
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    #The flow is the following, the requests includes a token, which is decoded.
    #From the decoding of the token, an email is obtained, which is used to query the database
    #If the user is not found, a 401 error is raised
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise credentials_exception
    return user

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        logger.warning(f"Unauthorized admin access attempt by user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges"
        )
    return current_user
