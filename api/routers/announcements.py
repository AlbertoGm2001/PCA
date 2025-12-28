from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from db.session import get_session
from models.models import Announcement
from loguru import logger
from api.security import get_current_user, get_admin_user, User

router = APIRouter(prefix="/announcements", tags=["announcements"])

@router.get("", response_model=List[Announcement])
def get_announcements(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info("Fetching all announcements")
    announcements = session.exec(select(Announcement).order_by(Announcement.created_at.desc())).all()
    logger.success(f"Retrieved {len(announcements)} announcements")
    return announcements

@router.post("")
def create_announcement(announcement: Announcement, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Creating new announcement: {announcement.title}")
    session.add(announcement)
    session.commit()
    session.refresh(announcement)
    logger.success(f"Announcement created with ID: {announcement.id}")
    return announcement

@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_admin_user)):
    logger.info(f"Attempting to delete announcement ID: {announcement_id}")
    announcement = session.get(Announcement, announcement_id)
    if not announcement:
        logger.warning(f"Announcement ID {announcement_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Announcement not found")
    session.delete(announcement)
    session.commit()
    logger.success(f"Announcement ID {announcement_id} deleted successfully")
    return {"message": "Announcement deleted"}
