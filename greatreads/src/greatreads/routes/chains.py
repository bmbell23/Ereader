"""Chain management API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.reading import Reading, ReadingResponse
from ..services.chain_calculator import ChainCalculator

router = APIRouter()


@router.post("/recalculate")
async def recalculate_chains(db: Session = Depends(get_db)):
    """Recalculate all reading chains."""
    calculator = ChainCalculator(db)
    calculator.recalculate_all_chains()
    return {"message": "Chains recalculated successfully"}


@router.get("/", response_model=List[List[ReadingResponse]])
async def get_all_chains(db: Session = Depends(get_db)):
    """Get all reading chains."""
    # Get all unfinished readings
    unfinished_readings = db.query(Reading).filter(
        Reading.date_finished_actual.is_(None)
    ).all()
    
    if not unfinished_readings:
        return []
    
    # Build chains
    calculator = ChainCalculator(db)
    chain_map = calculator._build_chain_map(unfinished_readings)
    chain_heads = calculator._find_chain_heads(unfinished_readings)
    
    chains = []
    for head in chain_heads:
        chain = []
        current = head
        processed_ids = set()
        
        while current and current.id not in processed_ids:
            chain.append(current)
            processed_ids.add(current.id)
            
            # Find next reading
            next_reading = None
            for reading in unfinished_readings:
                if reading.id_previous == current.id:
                    next_reading = reading
                    break
            current = next_reading
        
        if chain:
            chains.append(chain)
    
    return chains


@router.get("/{reading_id}/chain", response_model=List[ReadingResponse])
async def get_reading_chain(reading_id: int, db: Session = Depends(get_db)):
    """Get the chain containing a specific reading."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    calculator = ChainCalculator(db)
    chain_readings = calculator._get_chain_readings(reading)
    
    return chain_readings


@router.post("/{reading_id}/move")
async def move_reading_in_chain(
    reading_id: int,
    new_position: int,
    db: Session = Depends(get_db)
):
    """Move a reading to a new position in its chain."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    calculator = ChainCalculator(db)
    calculator.reorder_reading(reading_id, new_position)
    
    return {"message": f"Reading moved to position {new_position}"}


@router.post("/{reading_id}/break-chain")
async def break_chain_after_reading(reading_id: int, db: Session = Depends(get_db)):
    """Break the chain after a specific reading."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    # Find the next reading in the chain
    next_reading = db.query(Reading).filter(
        Reading.id_previous == reading_id
    ).first()
    
    if next_reading:
        next_reading.id_previous = None
        db.commit()
        
        # Recalculate chains
        calculator = ChainCalculator(db)
        calculator.recalculate_all_chains()
    
    return {"message": "Chain broken successfully"}


@router.post("/{reading_id}/connect-to/{target_id}")
async def connect_reading_to_target(
    reading_id: int,
    target_id: int,
    db: Session = Depends(get_db)
):
    """Connect a reading to follow another reading."""
    reading = db.query(Reading).filter(Reading.id == reading_id).first()
    target = db.query(Reading).filter(Reading.id == target_id).first()
    
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target reading not found")
    
    # Update the chain link
    reading.id_previous = target_id
    db.commit()
    
    # Recalculate chains
    calculator = ChainCalculator(db)
    calculator.recalculate_all_chains()
    
    return {"message": f"Reading {reading_id} now follows reading {target_id}"}
