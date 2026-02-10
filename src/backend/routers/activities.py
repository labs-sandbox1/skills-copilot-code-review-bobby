"""
Endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from typing import Dict, Any, Optional, List

from ..database import activities_collection, teachers_collection

router = APIRouter(
    prefix="/activities",
    tags=["activities"]
)


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
def get_activities(
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all activities with their details, with optional filtering by day and time

    - day: Filter activities occurring on this day (e.g., 'Monday', 'Tuesday')
    - start_time: Filter activities starting at or after this time (24-hour format, e.g., '14:30')
    - end_time: Filter activities ending at or before this time (24-hour format, e.g., '17:00')
    """
    # Filter activities based on provided filters
    activities = {}
    
    for name, activity in activities_collection.items():
        # Apply filters if provided
        if day and day not in activity["schedule_details"]["days"]:
            continue
        
        if start_time and activity["schedule_details"]["start_time"] < start_time:
            continue
        
        if end_time and activity["schedule_details"]["end_time"] > end_time:
            continue
        
        activities[name] = activity

    return activities


@router.get("/days", response_model=List[str])
def get_available_days() -> List[str]:
    """Get a list of all days that have activities scheduled"""
    # Collect unique days across all activities
    days_set = set()
    
    for activity in activities_collection.values():
        days_set.update(activity["schedule_details"]["days"])
    
    # Sort days alphabetically
    return sorted(list(days_set))


@router.post("/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Sign up a student for an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Get the activity
    activity = activities_collection.get(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Already signed up for this activity")

    # Add student to participants
    activity["participants"].append(email)

    return {"message": f"Signed up {email} for {activity_name}"}


@router.post("/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, teacher_username: Optional[str] = Query(None)):
    """Remove a student from an activity - requires teacher authentication"""
    # Check teacher authentication
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.get(teacher_username)
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    # Get the activity
    activity = activities_collection.get(activity_name)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400, detail="Not registered for this activity")

    # Remove student from participants
    activity["participants"].remove(email)

    return {"message": f"Unregistered {email} from {activity_name}"}
