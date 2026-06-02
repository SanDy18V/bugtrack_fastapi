import uuid
from fastapi import FastAPI, Depends, Form, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import models
from schema import ProfilePicUploadResponse, User as UserSchema, UserCreate, UserUpdate, LoginRequest, Token
from models import User as UserModel
from models import Project
from schema import ProjectCreate, ProjectResponse   
from models import Bug
from schema import BugCreate, BugResponse
from models import registeredDeveloperandtester
from schema import DeveloperTesterCreate, DeveloperTesterResponse
from database import SessionLocal, engine, Base
import auth
from auth import hash_password, verify_password
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
from mailconfig import send_verification_email
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, Depends
import shutil
import os


print("Tables detected:", Base.metadata.tables.keys())



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
os.makedirs("uploads/images", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)

Base.metadata.create_all(bind=engine)
print("Tables detected:", Base.metadata.tables.keys())
# dependency to get db session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

security = HTTPBearer()

##oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/protected")
def protected_route(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    return {
        "message": "Authenticated",
        "token": token
    }
def authenticate_user(db: Session, email: str, password: str):
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_verfied:
        return None
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    print("INSIDE GET_CURRENT_USER")

    token = credentials.credentials

    payload = jwt.decode(
        token,
        auth.SECRET_KEY,
        algorithms=[auth.ALGORITHM]
    )

    username = payload.get("sub")

    user = db.query(UserModel).filter(
        UserModel.email == username
    ).first()

    return user

def validate_token(token: str, db: Session) -> UserModel:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        print("TOKEN:", token)

        payload = jwt.decode(
            token,
            auth.SECRET_KEY,
            algorithms=[auth.ALGORITHM]
        )

        print("PAYLOAD:", payload)

        username: str | None = payload.get("sub")

        print("SUB:", username)

        if username is None:
            raise credentials_exception

    except JWTError as e:
        print("JWT ERROR:", e)
        raise credentials_exception

    user = db.query(UserModel).filter(
        UserModel.email == username
    ).first()

    print("USER:", user)

    if user is None:
        raise credentials_exception

    return user
   


@app.post("/login", response_model=Token)
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(get_db),):
    user = authenticate_user(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "user_id": str(user.user_id), "role": user.role},
        expires_delta=access_token_expires,
    )
    print("Generated Access Token:", access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserSchema)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
     return current_user


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

    user.is_verfied= True
    user.verification_token = None
    user.verification_token_expiry = None
    print("After:", user.is_verfied)
    db.commit()
    db.refresh(user)
   
    return {
        "message": "Email verified successfully"
    }

@app.post("/createprojects")
def create_project(
    project: ProjectCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_project = Project(
        project_name=project.project_name,
        description=project.description,
        owner_id=current_user.user_id
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project

#report a bug
@app.post("/reportbug", response_model=BugCreate)
def report_bug(
   title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    project_id: int = Form(...),
    assignee_id: int = Form(...),

    screenshot: UploadFile = File(None),
    video: UploadFile = File(None),

    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):  
    image_path = None
    video_path = None
    if screenshot:
        image_path = f"uploads/images/{uuid.uuid4()}_{screenshot.filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(screenshot.file, buffer)
    if video:
        video_path = f"uploads/videos/{uuid.uuid4()}_{video.filename}"
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)        
    db_bug = Bug(
        title=title,
        description=description,
        priority=priority,
        project_id=project_id,
        assignee_id=assignee_id,
        reporter_id=current_user.id,
        status="OPEN",
        screenshot_url=image_path,
        video_url=video_path,
    )
    print("Bug details:", db_bug)
    db.add(db_bug)
    db.commit()
    db.refresh(db_bug)

    return db_bug

@app.post("/createdevandtester", response_model=DeveloperTesterResponse)
def create_developer_and_tester(
   
    dev_tester: DeveloperTesterCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    hashed_password = hash_password(dev_tester.hashed_password)
    db_dev_tester = registeredDeveloperandtester(
        username=dev_tester.username,
        email=dev_tester.email,
        role=dev_tester.role,
        hashed_password=hashed_password,
        employee_id=dev_tester.employee_id,
        admin_id=current_user.user_id
    )

    db.add(db_dev_tester)
    db.commit()
    db.refresh(db_dev_tester)

    return db_dev_tester



@app.post("/loginforemployee", response_model=Token)
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(get_db),):
    user = db.query(registeredDeveloperandtester).filter(registeredDeveloperandtester.email == login_request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email, password, or email not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "user_id": str(user.user_id), "role": user.role},
        expires_delta=access_token_expires,
    )
    print("Generated Access Token:", access_token)
    return {"access_token": access_token, "token_type": "bearer"}






@app.post("/upload-profile")
async def upload_profile(
    file: UploadFile = File(...),
    current_user: ProfilePicUploadResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("current_user:", current_user)
    os.makedirs("uploads", exist_ok=True)

    file_path = f"uploads/{current_user.id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_pic = file_path
    print("Updated profile_pic:", current_user.profile_pic)
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile picture uploaded",
        "file_path": file_path
    }



  