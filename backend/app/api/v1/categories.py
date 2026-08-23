from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("", response_model=List[CategoryRead])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all categories for the current user"""
    return db.query(Category).filter(Category.user_id == current_user.id).order_by(Category.name.asc()).all()

@router.post("", status_code=201, response_model=CategoryRead)
def add_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new category"""
    existing = db.query(Category).filter(Category.name == payload.name, Category.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    category = Category(name=payload.name, user_id=current_user.id)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int, 
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update/rename an existing category strictly linked to the current user's library.
    """
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    category.name = payload.new_name
    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a category strictly linked to the current user's library.
    """
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == current_user.id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    db.delete(category)
    db.commit()
    return {"success": True}
