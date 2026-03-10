"""
大臣管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import get_db
from app.models.minister import Minister
from pydantic import BaseModel

router = APIRouter()

class MinisterCreate(BaseModel):
    name: str
    department: str
    model_id: str
    workspace: str
    api_key: str = None
    enabled: bool = True

class MinisterUpdate(BaseModel):
    name: str = None
    department: str = None
    model_id: str = None
    workspace: str = None
    api_key: str = None
    enabled: bool = None

class MinisterResponse(BaseModel):
    id: int
    name: str
    department: str
    model_id: str
    workspace: str
    enabled: bool
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[MinisterResponse])
async def get_ministers(db: Session = Depends(get_db)):
    """获取大臣列表"""
    ministers = db.query(Minister).all()
    return ministers

@router.get("/{minister_id}", response_model=MinisterResponse)
async def get_minister(minister_id: int, db: Session = Depends(get_db)):
    """获取大臣详情"""
    minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not minister:
        raise HTTPException(status_code=404, detail="大臣不存在")
    return minister

@router.post("/", response_model=MinisterResponse)
async def create_minister(minister: MinisterCreate, db: Session = Depends(get_db)):
    """创建大臣"""
    db_minister = Minister(**minister.dict())
    db.add(db_minister)
    db.commit()
    db.refresh(db_minister)
    return db_minister

@router.put("/{minister_id}", response_model=MinisterResponse)
async def update_minister(minister_id: int, minister: MinisterUpdate, db: Session = Depends(get_db)):
    """更新大臣配置"""
    db_minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not db_minister:
        raise HTTPException(status_code=404, detail="大臣不存在")
    
    update_data = minister.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_minister, key, value)
    
    db.commit()
    db.refresh(db_minister)
    return db_minister

@router.delete("/{minister_id}")
async def delete_minister(minister_id: int, db: Session = Depends(get_db)):
    """删除大臣"""
    db_minister = db.query(Minister).filter(Minister.id == minister_id).first()
    if not db_minister:
        raise HTTPException(status_code=404, detail="大臣不存在")
    
    db.delete(db_minister)
    db.commit()
    return {"message": "删除成功"}
