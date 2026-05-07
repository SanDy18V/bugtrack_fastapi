import uuid
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from schema import User as UserSchema, UserCreate,UserUpdate
from models import User as UserModel
from models import Project
from schema import ProjectCreate, ProjectResponse   
from database import SessionLocal, engine, Base
from auth import hash_password, verify_password
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
from mailconfig import send_verification_email
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
@app.post("/register", response_model=UserSchema)
def create_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.hashed_password)
    token = str(uuid.uuid4())
    expiry_time = datetime.utcnow() + timedelta(minutes=5)
    print("DB URL:", engine.url)
    db_user = UserModel(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        verification_token=token,
        verification_token_expiry=expiry_time
       
    )   
    print("Entered password",hashed_password)
    db.add(db_user)
    db.commit()
    background_tasks.add_task(
    send_verification_email,
    user.email,
    token
)
    db.refresh(db_user)
    return db_user




@app.get("/verify/{token}")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):

    user = db.query(UserModel).filter(
        UserModel.verification_token == token
    ).first()

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )

    if datetime.utcnow() > user.verification_token_expiry:
        raise HTTPException(
            status_code=400,
            detail="Verification link expired"
        )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expiry = None
    print("After:", user.is_verified)
    db.commit()
    db.refresh(user)
   
    return {
        "message": "Email verified successfully"
    }







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
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db_user.role = user.role
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

#create project
@app.post("/projects", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(
        project_name=project.project_name,
       
        description=project.description,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
