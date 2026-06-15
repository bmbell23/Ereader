"""Inventory management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.inventory import Inventory, InventoryCreate, InventoryUpdate, InventoryResponse

router = APIRouter()


@router.get("/", response_model=List[InventoryResponse])
async def get_inventory(
    book_id: int = None,
    db: Session = Depends(get_db)
):
    """Get inventory entries, optionally filtered by book_id."""
    query = db.query(Inventory)
    
    if book_id:
        query = query.filter(Inventory.book_id == book_id)
    
    return query.all()


@router.get("/{inventory_id}", response_model=InventoryResponse)
async def get_inventory_item(inventory_id: int, db: Session = Depends(get_db)):
    """Get a specific inventory entry."""
    inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    return inventory


@router.post("/", response_model=InventoryResponse)
async def create_inventory(inventory: InventoryCreate, db: Session = Depends(get_db)):
    """Create a new inventory entry."""
    # Check if inventory already exists for this book
    existing = db.query(Inventory).filter(Inventory.book_id == inventory.book_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Inventory entry already exists for this book. Use PUT to update."
        )
    
    db_inventory = Inventory(**inventory.model_dump())
    db.add(db_inventory)
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


@router.put("/{inventory_id}", response_model=InventoryResponse)
async def update_inventory(
    inventory_id: int,
    inventory: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """Update an inventory entry."""
    db_inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    
    update_data = inventory.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_inventory, field, value)
    
    db.commit()
    db.refresh(db_inventory)
    return db_inventory


@router.put("/book/{book_id}", response_model=InventoryResponse)
async def update_inventory_by_book(
    book_id: int,
    inventory: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """Update or create inventory entry for a specific book."""
    db_inventory = db.query(Inventory).filter(Inventory.book_id == book_id).first()
    
    if not db_inventory:
        # Create new inventory entry
        inventory_data = inventory.model_dump(exclude_unset=True)
        inventory_data['book_id'] = book_id
        db_inventory = Inventory(**inventory_data)
        db.add(db_inventory)
    else:
        # Update existing inventory
        update_data = inventory.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_inventory, field, value)
    
    db.commit()
    db.refresh(db_inventory)
    return InventoryResponse.from_orm(db_inventory)


@router.delete("/{inventory_id}")
async def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    """Delete an inventory entry."""
    db_inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    
    db.delete(db_inventory)
    db.commit()
    return {"message": "Inventory entry deleted successfully"}

