from pydantic import BaseModel;

class UserBase(BaseModel):
    username: str
    email: str
    password: str
    role: str
    is_active: bool=False
    is_verfied: bool=False

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Updaterole(BaseModel):
    role: str        