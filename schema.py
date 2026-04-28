from pydantic import BaseModel;

class UserBase(BaseModel):
    username: str
    email: str
    # hashed_password: str
    role: str
    is_active: bool=False
    is_verfied: bool=False

class UserCreate(UserBase):
    hashed_password: str

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True

class Updaterole(BaseModel):
    role: str        