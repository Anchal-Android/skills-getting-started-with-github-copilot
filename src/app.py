"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import re

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Basketball": {
        "description": "Team basketball practice and friendly matches",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": []
    },
    "Tennis Club": {
        "description": "Tennis training and tournaments",
        "schedule": "Saturdays, 10:00 AM - 12:00 PM",
        "max_participants": 10,
        "participants": []
    },
    "Drama Club": {
        "description": "Theater productions and acting workshops",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": []
    },
    "Digital Art": {
        "description": "Learn digital design, animation, and graphic art",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",     
        "max_participants": 18,
        "participants": []
    },
    "Debate Team": {
        "description": "Competitive debate and public speaking",
        "schedule": "Tuesdays, 4:00 PM - 5:30 PM",
        "max_participants": 16,
        "participants": []
    },
    "Science Club": {
        "description": "Explore STEM topics through experiments and projects",
        "schedule": "Fridays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": []
    },
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    }
}


def slugify(name: str) -> str:
    """Create a simple slug from a name (lowercase, dashes)."""
    s = name.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    return s.strip('-')


def resolve_activity_key(identifier: str) -> str:
    """Resolve an identifier that may be a full activity name, case-insensitive name, or slug."""
    # Exact match
    if identifier in activities:
        return identifier
    # Case-insensitive match
    for name in activities.keys():
        if name.lower() == identifier.lower():
            return name
    # Slug match
    slug = slugify(identifier)
    for name in activities.keys():
        if slugify(name) == slug:
            return name
    # Not found
    raise HTTPException(status_code=404, detail="Activity not found")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    # Include a stable slug/id for each activity so clients can use it reliably
    return { name: { **details, "id": slugify(name) } for name, details in activities.items() }


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Resolve activity identifier (accept full name, case-insensitive, or slug)
    resolved_name = resolve_activity_key(activity_name)
    activity = activities[resolved_name]

    # Check if already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")  
    
    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {resolved_name}"}


@app.delete("/activities/{activity_name}/participants")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity."""
    resolved_name = resolve_activity_key(activity_name)
    activity = activities[resolved_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Student not found in this activity")
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {resolved_name}"}
