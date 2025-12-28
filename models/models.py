from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


# --- Link Tables ---

class UserClassLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    class_id: int = Field(foreign_key="class.id", primary_key=True)

class UserEventLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    event_id: int = Field(foreign_key="event.id", primary_key=True)

class UserTeamLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)

# --- Main Models ---

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    level: float
    is_admin: bool = Field(default=False)
    classes_to_recover: int = Field(default=0)
    
    classes: List["Class"] = Relationship(back_populates="students", link_model=UserClassLink)
    events: List["Event"] = Relationship(back_populates="participants", link_model=UserEventLink)
    teams: List["Team"] = Relationship(back_populates="members", link_model=UserTeamLink)

class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str
    date: datetime
    min_level: float
    max_slots: int
    price: float
    participants: List[User] = Relationship(back_populates="events", link_model=UserEventLink)

class Class(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    coach_id: int
    schedule: datetime
    level_required: float
    max_students: int
    
    students: List[User] = Relationship(back_populates="classes", link_model=UserClassLink)

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    competition_name: str    
    members: List[User] = Relationship(back_populates="teams", link_model=UserTeamLink)
    matches: List[Match] = Relationship(back_populates="team")



class Match(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")
    date: datetime
    opponent_name: Optional[str] = None
    score: Optional[str] = None
    
    team: Optional[Team] = Relationship(back_populates="matches")

class Announcement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    images: str #Assign a bucket in S3 so every image in that bucket is associated with this announcement
    author_id: int = Field(foreign_key="user.id")
