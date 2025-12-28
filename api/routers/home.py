from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db.session import get_session
from models.models import User, Announcement, Match
from loguru import logger
from api.security import get_current_user

router = APIRouter(prefix="/home", tags=["home"])

@router.get("/summary")
def get_home_summary(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    logger.info(f"Generating home summary for user ID: {current_user.id}")
    user = current_user

    # 1. Club Announcements
    announcements = session.exec(
        select(Announcement).order_by(Announcement.created_at.desc()).limit(5)
    ).all()
    
    # 2. Upcoming Events & Classes (from many-to-many relationships)
    summary = {
        "announcements": announcements,
        "upcoming_events": user.events[:5],
        "upcoming_classes": user.classes[:5],
        "recent_results": session.exec(
            select(Match).where(Match.team_id.in_([t.id for t in user.teams])).order_by(Match.date.desc()).limit(3)
        ).all()
    }
    logger.success(f"Home summary generated for user ID: {user_id}")
    return summary
