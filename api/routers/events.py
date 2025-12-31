from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from db.session import get_session
from models.models import User, Event
from loguru import logger
from api.security import get_current_user, get_admin_user

router = APIRouter(prefix="/events", tags=["events"])

# --- User Endpoints ---

@router.get("", response_model=List[Event])
def list_events(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user),
    limit: int = 100
):
    logger.info(f"Listing events for user: {current_user.email}")
    level = current_user.level
    query = select(Event)
    if level is not None:
        query = query.where(Event.min_level <= level)
    
    events = session.exec(query.limit(limit)).all()
    logger.success(f"Retrieved {len(events)} events")
    return events

@router.post("/{event_id}/register")
def register_for_event(event_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info(f"User {current_user.id} attempting to register for event {event_id}")
    user = current_user
    event = session.get(Event, event_id)
    
    if not user or not event:
        logger.warning(f"Registration failed: User {user_id} or Event {event_id} not found")
        raise HTTPException(status_code=404, detail="User or Event not found")
    
    if len(event.participants) >= event.max_slots:
        logger.warning(f"Registration failed: Event {event_id} is full")
        raise HTTPException(status_code=400, detail="Event is full")
    
    if event in user.events:
        logger.info(f"User {user_id} already registered for event {event_id}")
        raise HTTPException(status_code=400, detail="User is already registered for this event")
        
    user.events.append(event)
    session.add(user)
    session.commit()
    
    logger.success(f"User {user_id} registered for event {event_id} ({event.name})")
    return {"status": "success", "event": event.name}

@router.delete("/{event_id}/unregister")
def unregister_from_event(event_id: int, user_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = current_user
    event = session.get(Event, event_id)
    
    if not user or not event:
        raise HTTPException(status_code=404, detail="User or Event not found")
    
    if event in user.events:
        user.events.remove(event)
        session.add(user)
        session.commit()
        return {"message": "Unregistered from event"}
    
    return {"message": "User was not registered for this event"}


@router.get("/{event_id}/get_users", response_model=List[User])
def get_users(event_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    event = session.get(Event, event_id)
    if not event:
            raise HTTPException(status_code=404, detail="Event not found")
    return event.participants






# --- Admin Endpoints ---

@router.post("/", response_model=Event)
def create_event(event: Event, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Creating new event: {event.name}")
    event.id = None
    session.add(event)
    session.commit()
    session.refresh(event)
    logger.success(f"Event created with ID: {event.id}")
    return event

@router.delete("/{event_id}")
def delete_event(event_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to delete event ID: {event_id}")
    event = session.get(Event, event_id)
    if not event:
        logger.warning(f"Event ID {event_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Event not found")
    session.delete(event)
    session.commit()
    logger.success(f"Event ID {event_id} deleted successfully")
    return {"message": "Event deleted successfully"}


@router.patch("/{event_id}")
def update_event(event_id: int, event_data: Event, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to update event ID: {event_id}")
    db_event = session.get(Event, event_id)
    if not db_event:
        session.close()
        logger.warning(f"Event ID {event_id} not found for update")
        raise HTTPException(status_code=404, detail="Event not found")
    
    data = event_data.dict(exclude_unset=True)
    for key, value in data.items():
        if key=='max_slots':
            if len(db_event.participants) > value:
                logger.warning(f"Event ID {event_id} update failed: Event has too many participants")
                raise HTTPException(status_code=400, detail="Event has too many participants")
                
        if key != "id":
            setattr(db_event, key, value)
            
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    logger.success(f"Event ID {event_id} updated successfully")
    return db_event


