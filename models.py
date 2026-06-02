from sqlalchemy import Column, Integer, String, Boolean,Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
    profile_pic = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    projects = relationship(
        "Project",
        back_populates="owner"
    )
    developer_and_testers = relationship(
        "registeredDeveloperandtester", 
        back_populates="admin"
    )

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255),unique=True, nullable=False)
    project_key = Column(String(50), unique=True, nullable=False,default=lambda:str(uuid.uuid4()))
    description = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    owner_id = Column(String(50), ForeignKey("usersdata.user_id"))
    owner = relationship("User", back_populates="projects") 

class Bug(Base):
    __tablename__ = "bugs"

    bug_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="OPEN")
    priority = Column(String(50), default="MEDIUM")
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    project_id = Column(Integer, ForeignKey("projects.id")) 
    reporter_id = Column( Integer, ForeignKey("usersdata.id"),  nullable=False)
    assignee_id = Column(Integer, nullable=False)   
    screenshot_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)

class registeredDeveloperandtester(Base):
    __tablename__ = "developer_and_tester"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False);
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False);
    role= Column(String(50), nullable=False)
    employee_id = Column(String(50), unique=True, nullable=False)
    admin_id = Column(String(50), ForeignKey("usersdata.user_id"), nullable=False)
    admin = relationship("User",back_populates="developer_and_testers")
    profile_pic= Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

       