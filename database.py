# TODO 내장 DB 설정(SQLite)
import json
import sqlite3
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
def get_kst_now():
    return datetime.now(KST)

# 1. DB 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    
    return db

# 2. ORM
class RegisteredDataset(Base):
    __tablename__ = "register"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200))
    author = Column(String(200))
    createdDate = Column(DateTime, default=get_kst_now)
    content = Column(Text)
    approvedDate = Column(DateTime, nullable=True)
# Base.metadata.drop_all(engine)
Base.metadata.create_all(bind=engine)


# 3. 데이터베이스 테이블 생성
def load_json_to_database(json_file_path: str):
    """JSON 파일을 읽어서 SQLite 데이터베이스에 저장"""
    
    # JSON 파일 읽기
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {json_file_path}")
        return
    except json.JSONDecodeError:
        print("JSON 파일 형식이 올바르지 않습니다.")
        return
    
    # 데이터베이스 세션 생성
    db = get_db()
    
    try:
        for item in data:
            dataset = RegisteredDataset(
                title=item.get("title"),
                author=item.get("author"),
                createdDate=datetime.strptime(item.get("createdDate"), "%Y-%m-%d %H:%M:%S"),
                content=item.get("content"),
                approvedDate=item.get("approvedDate")
            )
            db.add(dataset)
        db.commit()
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()
        