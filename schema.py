from datetime import datetime

from fastapi import UploadFile
from pydantic import BaseModel;
from typing import Optional





# create a user api
class UserBase(BaseModel):
    username: str
    email: str
    role: str
    
   
# create hash password for user   
class UserCreate(UserBase):
    hashed_password: str

class User(UserBase):
    id: int
    user_id: str
    created_at: datetime
    is_active: Optional[bool] = True
    is_verfied: bool=False
    profile_pic: Optional[str] = None

    
    class Config:
        from_attributes = True

#update user by id
class UserUpdate(BaseModel):
    username: str
    email: str
    role: str        


# update user role by id
class Updaterole(BaseModel):
    role: str        





class TokenData(BaseModel):
    username: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    

class LoginRequest(BaseModel):
    email: str
    password: str

#create a project api
class ProjectBase(BaseModel):
    project_name: str
    description: Optional[str] = None
   


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
    user_id:str
    project_key: str
    status: Optional[str] = "ACTIVE"
    is_active: Optional[bool] = True
    created_at: datetime


    class Config:
        from_attributes = True    


class BugCreate(BaseModel):
    title: str
    description: str
    priority: str
    project_id: int
    assignee_id: int
    screenshot_url: Optional[str] = None
    video_url: Optional[str] = None

class BugResponse(BaseModel):
    bug_id: int
    title: str
    description: str
    priority: str
    status: str
    created_at: datetime
    project_id: int
    reporter_id: int
    assignee_id: int

    class Config:
        from_attributes = True        
       
class DeveloperTesterCreate(BaseModel):
    username: str   
    email: str
    role: str
    employee_id: str
    hashed_password: str
  

class DeveloperTesterResponse(BaseModel):
    id: int
    username: str   
    email: str
    role: str
    employee_id: str
    admin_id: str
    created_at: datetime

    class Config:
        from_attributes = True
    

class ProfilePicUploadResponse(BaseModel):
    message: str
    profile_pic_url: Optional[str] = None

    class Config:
        from_attributes = True