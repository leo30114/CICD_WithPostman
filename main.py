from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from sqlalchemy import (
    create_engine, Column, Integer, String
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ── 2.1 連線字串 ──
# SQLite
DATABASE_URL = "sqlite:///./test.db"
# MySQL 範例： mysql+pymysql://user:password@localhost:3306/yourdb
# DATABASE_URL = "mysql+pymysql://root:1234@127.0.0.1:3306/test_db"

# ── 2.2 SQLAlchemy 設定 ──
# SQLite 需要加 connect_args
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ── 2.3 定義資料表模型 ──
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), index=True)
    description = Column(String(256), nullable=True)

# 建表
Base.metadata.create_all(bind=engine)

# ── 2.4 Pydantic Schema ──
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ItemRead(ItemCreate):
    id: int
    class Config:
        orm_mode = True  # 讓 ORM model 可自動轉成 Pydantic

# ── 2.5 FastAPI App ──
app = FastAPI()

# 取得 DB Session 的 dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── 2.6 CRUD 路由 ──

# Create
@app.post("/items/", response_model=ItemRead)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(name=item.name, description=item.description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# Read (list)
@app.get("/items/", response_model=List[ItemRead])
def read_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()

# Read (single)
@app.get("/items/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# Update
@app.put("/items/{item_id}", response_model=ItemRead)
def update_item(item_id: int, req: ItemCreate, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    item.name = req.name
    item.description = req.description
    db.commit()
    db.refresh(item)
    return item

# Delete
@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
