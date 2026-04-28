from sqlalchemy import Column, Integer, String, Boolean,Text, DateTime, ForeignKey;
from database import Base;


class User(Base):
    __tablename__ = "usersdata"

    id = Column(Integer, primary_key=True, index=True);
    username = Column(String(50), unique=True, index=True, nullable=False);
    email = Column(String(100), unique=True, index=True, nullable=False);
    password = Column(String(255), nullable=False);
    role = Column(String(20), nullable=False, index=True);
    is_active = Column(Boolean, default=False); 
    is_verfied = Column(Boolean, default=False);
    created_at = Column(DateTime, nullable=True);