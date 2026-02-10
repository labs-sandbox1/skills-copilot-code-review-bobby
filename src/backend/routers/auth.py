"""
Authentication endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..database import teachers_collection, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/login")
def login(username: str, password: str) -> Dict[str, Any]:
    """Login a teacher account"""
    # Find the teacher in the database
    teacher = teachers_collection.get(username)

    # Verify password using Argon2 verifier from database.py
    if not teacher or not verify_password(teacher.get("password", ""), password):
        raise HTTPException(
            status_code=401, detail="Invalid username or password")

    # Return teacher information (excluding password)
    return {
        "username": username,
        "display_name": teacher.get("display_name", teacher.get("name", "")),
        "role": teacher.get("role", "teacher")
    }


@router.get("/check-session")
def check_session(username: str) -> Dict[str, Any]:
    """Check if a session is valid by username"""
    teacher = teachers_collection.get(username)

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return {
        "username": username,
        "display_name": teacher.get("display_name", teacher.get("name", "")),
        "role": teacher.get("role", "teacher")
    }
