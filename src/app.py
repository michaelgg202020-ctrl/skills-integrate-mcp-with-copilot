"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import hashlib
import os
from pathlib import Path
import secrets

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class RegistrationRequest(BaseModel):
    email: str
    password: str
    name: str
    grade: str | None = None
    interests: list[str] = []
    contact: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    grade: str | None = None
    interests: list[str] | None = None
    contact: str | None = None


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split("$", 1)
    candidate = hash_password(password, bytes.fromhex(salt_hex)).split("$", 1)[1]
    return secrets.compare_digest(candidate, digest_hex)


users = {}
sessions = {}


def public_user(user: dict) -> dict:
    return {key: value for key, value in user.items() if key != "password_hash"}


def normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise HTTPException(status_code=422, detail="A valid email is required")
    return normalized


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    user_email = sessions.get(authorization.removeprefix("Bearer "))
    user = users.get(user_email)
    if not user or not user["active"]:
        raise HTTPException(status_code=401, detail="Invalid or inactive session")
    return user


def require_roles(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return dependency


admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")
if admin_email and admin_password:
    normalized_admin_email = admin_email.strip().lower()
    users[normalized_admin_email] = {
        "email": normalized_admin_email,
        "name": "Administrator",
        "grade": None,
        "interests": [],
        "contact": None,
        "role": "admin",
        "active": True,
        "password_hash": hash_password(admin_password),
    }

# In-memory activity database
activities = {
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
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/auth/register", status_code=201)
def register(request: RegistrationRequest):
    email = normalize_email(request.email)
    if email in users:
        raise HTTPException(status_code=409, detail="User already exists")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    users[email] = {
        "email": email,
        "name": request.name,
        "grade": request.grade,
        "interests": request.interests,
        "contact": request.contact,
        "role": "student",
        "active": True,
        "password_hash": hash_password(request.password),
    }
    return public_user(users[email])


@app.post("/auth/login")
def login(request: LoginRequest):
    user = users.get(normalize_email(request.email))
    if not user or not user["active"] or not verify_password(
        request.password, user["password_hash"]
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_urlsafe(32)
    sessions[token] = user["email"]
    return {"access_token": token, "token_type": "bearer", "user": public_user(user)}


@app.post("/auth/logout")
def logout(authorization: str | None = Header(default=None), user: dict = Depends(current_user)):
    if authorization:
        sessions.pop(authorization.removeprefix("Bearer "), None)
    return {"message": f"Logged out {user['email']}"}


@app.get("/auth/me")
def get_current_user(user: dict = Depends(current_user)):
    return public_user(user)


@app.patch("/users/me")
def update_profile(
    request: ProfileUpdateRequest, user: dict = Depends(current_user)
):
    for field, value in request.model_dump(exclude_unset=True).items():
        user[field] = value
    return public_user(user)


@app.get("/users")
def list_users(user: dict = Depends(require_roles("admin"))):
    return [public_user(registered_user) for registered_user in users.values()]


@app.patch("/users/{email}/status")
def update_user_status(
    email: str,
    active: bool,
    user: dict = Depends(require_roles("admin")),
):
    target = users.get(normalize_email(email))
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target["email"] == user["email"] and not active:
        raise HTTPException(status_code=400, detail="You cannot deactivate yourself")
    target["active"] = active
    return public_user(target)


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str | None = None,
    user: dict = Depends(current_user),
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    email = normalize_email(email or user["email"])
    if user["role"] == "student" and email != user["email"]:
        raise HTTPException(status_code=403, detail="Students can only manage their own signup")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str | None = None,
    user: dict = Depends(current_user),
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    email = normalize_email(email or user["email"])
    if user["role"] == "student" and email != user["email"]:
        raise HTTPException(status_code=403, detail="Students can only manage their own signup")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
