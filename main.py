import uuid
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models
from schema import User as UserSchema, UserCreate, UserUpdate, LoginRequest, Token
from models import User as UserModel
from models import Project
from schema import ProjectCreate, ProjectResponse   
from database import SessionLocal, engine, Base
import auth
from auth import hash_password, verify_password
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
from mailconfig import send_verification_email
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends


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

security = HTTPBearer()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.email == username).first()
    if user is None:
        raise credentials_exception
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
def login_for_access_token(login_request: LoginRequest, db: Session = Depends(get_db)):
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

@app.post("/createprojects", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    print("tokenvalue:", credentials.credentials)  # debug

    # Extract token
    token = credentials.credentials

    # Validate JWT token
    user = validate_token(token, db)

    print("USER ROLE:", user.role)

    # Role check
    if user.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN can create projects"
        )

    # Create project
    db_project = Project(
        project_name=project.project_name,
        description=project.description
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


