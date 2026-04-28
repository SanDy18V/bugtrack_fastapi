from sqlalchemy import create_engine;
from sqlalchemy.orm import sessionmaker ,declarative_base;
from dotenv import load_dotenv;
import os;  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

print("DATABASE_URL =", DATABASE_URL)  # debug

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")
engine = create_engine(DATABASE_URL);       
SessionLocal = sessionmaker(bind=engine,autocommit=False, autoflush=False)  
Base = declarative_base()