from sqlalchemy import Column, Integer, String, Boolean,Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base;
import uuid

class User(Base):
    __tablename__ = "usersdata"

    id = Column(Integer, primary_key=True, index=True);
    username = Column(String(50), index=True, nullable=False);
    user_id = Column(String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()));
    email = Column(String(100), unique=True, index=True, nullable=False);
    hashed_password = Column(String(255), nullable=False);
    role = Column(String(20), nullable=False, index=True);
    is_active = Column(Boolean, default=True); 
    is_verfied = Column(Boolean, default=False);
    verification_token = Column(String(255), nullable=True)
    verification_token_expiry = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),unique=True, nullable=False)
    project_key = Column(String(50), unique=True, nullable=False,default=lambda:str(uuid.uuid4()))
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())    