"""
API Routes - Category Management
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.core.categories import CategoryManager

router = APIRouter()
category_manager = CategoryManager()


class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    new_name: str


@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get all categories"""
    return category_manager.get_categories()


@router.post("/categories", status_code=201)
async def add_category(category: CategoryCreate):
    """Add a new category"""
    result = category_manager.add_category(category.name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.put("/categories/{category_name}")
async def update_category(category_name: str, update: CategoryUpdate):
    """Update/rename a category"""
    result = category_manager.update_category(category_name, update.new_name)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.delete("/categories/{category_name}")
async def delete_category(category_name: str):
    """Delete a category"""
    result = category_manager.delete_category(category_name)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result
