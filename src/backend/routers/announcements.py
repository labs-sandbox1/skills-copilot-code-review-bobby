"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementCreate(BaseModel):
    """Model for creating a new announcement"""
    message: str
    start_date: Optional[str] = None
    end_date: str


class AnnouncementUpdate(BaseModel):
    """Model for updating an announcement"""
    message: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """
    Get all active announcements (those within their date range)
    """
    active_announcements = []
    current_date = date.today().isoformat()
    
    for announcement_id, announcement in announcements_collection.items():
        # Check if announcement is within its active date range
        start_date = announcement.get("start_date")
        end_date = announcement.get("end_date")
        
        # If start_date is set and current date is before it, skip
        if start_date and current_date < start_date:
            continue
        
        # If end_date is set and current date is after it, skip
        if end_date and current_date > end_date:
            continue
        
        active_announcements.append(announcement)
    
    # Sort by created_at (most recent first)
    active_announcements.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return active_announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher_username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """
    Get all announcements (including expired ones) - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Return all announcements sorted by created_at (most recent first)
    all_announcements = list(announcements_collection.values())
    all_announcements.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return all_announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    announcement: AnnouncementCreate,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Create a new announcement - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate that end_date is provided
    if not announcement.end_date:
        raise HTTPException(
            status_code=400, detail="Expiration date is required")
    
    # Validate date format and that end_date is in the future
    try:
        end_date_obj = datetime.fromisoformat(announcement.end_date).date()
        if end_date_obj < date.today():
            raise HTTPException(
                status_code=400, detail="Expiration date must be in the future")
        
        # Validate start_date if provided
        if announcement.start_date:
            start_date_obj = datetime.fromisoformat(announcement.start_date).date()
            if start_date_obj > end_date_obj:
                raise HTTPException(
                    status_code=400, detail="Start date must be before expiration date")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Generate new ID
    new_id = str(max([int(k) for k in announcements_collection.keys()], default=0) + 1)
    
    # Create announcement
    new_announcement = {
        "id": new_id,
        "message": announcement.message,
        "start_date": announcement.start_date,
        "end_date": announcement.end_date,
        "created_by": teacher_username,
        "created_at": datetime.now().isoformat()
    }
    
    announcements_collection[new_id] = new_announcement
    
    return new_announcement


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    announcement: AnnouncementUpdate,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Update an existing announcement - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Find the announcement
    existing_announcement = announcements_collection.get(announcement_id)
    if not existing_announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Update fields if provided
    if announcement.message is not None:
        existing_announcement["message"] = announcement.message
    
    if announcement.start_date is not None:
        existing_announcement["start_date"] = announcement.start_date
    
    if announcement.end_date is not None:
        # Validate date format
        try:
            end_date_obj = datetime.fromisoformat(announcement.end_date).date()
            start_date = existing_announcement.get("start_date")
            if start_date:
                start_date_obj = datetime.fromisoformat(start_date).date()
                if start_date_obj > end_date_obj:
                    raise HTTPException(
                        status_code=400, detail="Start date must be before expiration date")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        existing_announcement["end_date"] = announcement.end_date
    
    return existing_announcement


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, str]:
    """
    Delete an announcement - requires teacher authentication
    """
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Find and delete the announcement
    if announcement_id not in announcements_collection:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    del announcements_collection[announcement_id]
    
    return {"message": "Announcement deleted successfully"}
