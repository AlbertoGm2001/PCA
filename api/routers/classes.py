from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from db.session import get_session
from models.models import User, Class
from loguru import logger
from api.security import get_current_user, get_admin_user

router = APIRouter(prefix="/classes", tags=["classes"])

# --- User Endpoints ---

@router.get("", response_model=List[Class])
def list_classes(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    logger.info(f"Listing classes for user: {current_user.email}")
    
    if current_user.classes_to_recover <= 0:
        logger.info(f"User {current_user.id} has no recovery classes available")
        return []

    query = select(Class)
    level = current_user.level
    if level is not None: 
        query = query.where(Class.level_required <= level)
    
    classes = session.exec(query.limit(limit)).all()
    logger.success(f"Retrieved {len(classes)} classes")
    return classes

@router.post("/{class_id}/register")
def register_for_class(class_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.id} attempting to register for class {class_id}")
    user = current_user
    lesson = session.get(Class, class_id)
    
    if not user or not lesson:
        logger.warning(f"Registration failed: User {user_id} or Class {class_id} not found")
        raise HTTPException(status_code=404, detail="User or Class not found")
    
    if user.classes_to_recover <= 0:
        logger.warning(f"Registration failed: User {user_id} has no classes to recover")
        raise HTTPException(status_code=400, detail="User has no classes to recover")

    if len(lesson.students) >= lesson.max_students:
        logger.warning(f"Registration failed: Class {class_id} is full")
        raise HTTPException(status_code=400, detail="Class is full")
    
    if lesson in user.classes:
        logger.warning(f"Registration failed: User {user_id} is already registered for class {class_id}")
        raise HTTPException(status_code=400, detail="User is already registered for this class")

    else:
        user.classes.append(lesson)
        user.classes_to_recover -= 1
        session.add(user)
        session.commit()
    
    logger.success(f"User {user_id} registered for class {class_id}. Remaining credits: {user.classes_to_recover}")
    return {"status": "success", "class": class_id, "remaining_credits": user.classes_to_recover}

@router.delete("/{class_id}/unregister")
def unregister_from_class(class_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.id} attempting to unregister from class {class_id}")
    user = current_user
    lesson = session.get(Class, class_id)
    
    if not user or not lesson:
        logger.warning(f"Unregistration failed: User {user_id} or Class {class_id} not found")
        raise HTTPException(status_code=404, detail="User or Class not found")
    
    if lesson in user.classes:
        user.classes.remove(lesson)
        user.classes_to_recover += 1
        session.add(user)
        session.commit()
        logger.success(f"User {user_id} unregistered from class {class_id}. New credits: {user.classes_to_recover}")
        return {"message": "Unregistered from class", "new_credits": user.classes_to_recover}
    
    logger.info(f"User {user_id} was not registered for class {class_id}")
    return {"message": "User was not registered for this class"}

# --- Admin Endpoints ---

@router.post("/", response_model=Class)
def create_class(lesson: Class, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info("Creating new class")
    # Clear ID to let database handle it
    lesson.id = None
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    logger.success(f"Class created with ID: {lesson.id}")
    return lesson

@router.delete("/{class_id}")
def delete_class(class_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to delete class ID: {class_id}")
    lesson = session.get(Class, class_id)
    if not lesson:
        logger.warning(f"Class ID {class_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Class not found")
    session.delete(lesson)
    session.commit()
    logger.success(f"Class ID {class_id} deleted successfully")
    return {"message": "Class deleted successfully"}

 
@router.patch("/{class_id}")
def update_class(class_id: int, lesson_data: Class, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to update class ID: {class_id}")
    db_lesson = session.get(Class, class_id)
    if not db_lesson:
        logger.warning(f"Class ID {class_id} not found for update")
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Update fields from the class data
    data = lesson_data.dict(exclude_unset=True)
    for key, value in data.items():
        if key != "id":
            setattr(db_lesson, key, value)
        
    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)
    logger.success(f"Class ID {class_id} updated successfully")
    return db_lesson

@router.get("/{class_id}/class_users",response_model=List[User])
def get_class_users(class_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    lesson = session.get(Class, class_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Class not found")
    return lesson.students