from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import TodoCreate, TodoUpdate, TodoResponse
import crud as crud

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)


@router.get("/", response_model=List[TodoResponse])
def get_todos(db: Session = Depends(get_db)):
    todos = crud.get_all_todos(db)
    return todos


@router.post("/", response_model=TodoResponse)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    return crud.create_todo(db, todo)


@router.get("/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = crud.get_todo_by_id(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    todo = crud.update_todo(db, todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.patch("/{todo_id}/complete", response_model=TodoResponse)
def complete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = crud.complete_todo(db, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    success = crud.delete_todo(db, todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"message": "Todo deleted", "id": todo_id}
