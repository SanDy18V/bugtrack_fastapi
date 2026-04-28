from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from schema import User as UserSchema, UserCreate
from models import User as UserModel
from database import SessionLocal, engine, Base
from auth import hash_password, verify_password
print("Tables detected:", Base.metadata.tables.keys())



app = FastAPI()

Base.metadata.create_all(bind=engine)
print("Tables detected:", Base.metadata.tables.keys())
# dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# create a user 
@app.post("/users", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.hashed_password)
    print("DB URL:", engine.url)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        is_active=user.is_active
    )   
    print("Entered password",hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# get all users
@app.get("/users", response_model=list[UserSchema])
def get_users(db: Session = Depends(get_db)):
    return db.query(UserModel).all()    

# get user by id
@app.get("/users/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    singleuser= db.query(UserModel).filter(UserModel.id == user_id).first() 
    if singleuser is None:
        raise HTTPException(status_code=404, detail="User not found")
    return singleuser     

# update user by id
@app.put("/users/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db_user.password = user.password
    db_user.role = user.role
    db_user.is_active = user.is_active
    db.commit()
    db.refresh(db_user)
    return db_user




# update user role by id
@app.patch("/users/{user_id}/role", response_model=UserSchema)
def update_user_role(user_id: int, role: str, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.role = role
    db.commit()
    db.refresh(db_user)
    return db_user