from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from db.session import get_session
from models.models import User
from loguru import logger
from api.security import get_password_hash, get_admin_user, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[User])
def list_users(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_admin_user),
    limit: int = 100
):
    logger.info(f"Listing users with limit={limit}")
    users = session.exec(select(User).limit(limit)).all()
    logger.success(f"Retrieved {len(users)} users")
    return users

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching user ID: {user_id}")
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"User ID {user_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.success(f"User ID {user_id} retrieved")
    return user

@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(user: User, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to create user with email: {user.email}")
    # Check if email already exists
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        logger.warning(f"Create user failed: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user.id = None
    # Use password as is from the User object (plain text at this point in the request)
    user.hashed_password = get_password_hash(user.hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.success(f"User created with ID: {user.id}")
    return user

@router.patch("/{user_id}", response_model=User)
def update_user(user_id: int, user_data: dict, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to update user ID: {user_id}")
    db_user = session.get(User, user_id)
    if not db_user:
        logger.warning(f"User ID {user_id} not found for update")
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_data.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    logger.success(f"User ID {user_id} updated successfully")
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to delete user ID: {user_id}")
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"User ID {user_id} not found for deletion")
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    logger.success(f"User ID {user_id} deleted successfully")
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/add_recovery_classes")
def add_recovery_classes(user_id: int, amount: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Adding {amount} recovery classes to user ID: {user_id}")
    user = session.get(User, user_id)
    if not user:
        logger.warning(f"User ID {user_id} not found for adding recovery classes")
        raise HTTPException(status_code=404, detail="User not found")
    
    user.classes_to_recover += amount
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.success(f"Added {amount} classes to user {user_id}. New balance: {user.classes_to_recover}")
    return {"status": "success", "new_balance": user.classes_to_recover}
