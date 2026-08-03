"""Owner-controlled collection scheduling with Supabase-authenticated updates."""
from datetime import datetime
import os
from zoneinfo import ZoneInfo

import httpx
from fastapi import Header, HTTPException, status
from sqlalchemy import select

from .database import AutomationSchedule, session_scope

IST = ZoneInfo("Asia/Kolkata")
VALID_FREQUENCIES = {"daily", "weekdays", "weekly"}
VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}

def get_schedule() -> AutomationSchedule:
    with session_scope() as session:
        schedule = session.scalar(select(AutomationSchedule).where(AutomationSchedule.id == 1))
        if schedule is None:
            schedule = AutomationSchedule(id=1)
            session.add(schedule)
            session.flush()
        session.expunge(schedule)
        return schedule

def update_schedule(frequency: str, day_of_week: str, time_ist: str, slack_enabled: bool) -> AutomationSchedule:
    if frequency not in VALID_FREQUENCIES or day_of_week not in VALID_DAYS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid schedule")
    try:
        datetime.strptime(time_ist, "%H:%M")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Time must use HH:MM") from exc
    with session_scope() as session:
        schedule = session.scalar(select(AutomationSchedule).where(AutomationSchedule.id == 1))
        if schedule is None:
            schedule = AutomationSchedule(id=1)
            session.add(schedule)
        schedule.frequency = frequency
        schedule.day_of_week = day_of_week
        schedule.time_ist = time_ist
        schedule.slack_enabled = slack_enabled
        session.flush()
        session.expunge(schedule)
        return schedule

def collection_due() -> tuple[bool, AutomationSchedule]:
    schedule = get_schedule()
    now = datetime.now(IST)
    today = now.date().isoformat()
    target_hour, target_minute = (int(part) for part in schedule.time_ist.split(":"))
    permitted_day = schedule.frequency == "daily" or (schedule.frequency == "weekdays" and now.weekday() < 5) or (schedule.frequency == "weekly" and now.strftime("%A") == schedule.day_of_week)
    due = permitted_day and schedule.last_run_date != today and (now.hour, now.minute) >= (target_hour, target_minute)
    return due, schedule

def mark_collected() -> None:
    with session_scope() as session:
        schedule = session.scalar(select(AutomationSchedule).where(AutomationSchedule.id == 1))
        if schedule is not None:
            schedule.last_run_date = datetime.now(IST).date().isoformat()

async def require_owner(authorization: str | None = Header(default=None)) -> str:
    """Validate a Supabase user token and restrict updates to the configured owner."""
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
    owner_email = os.getenv("OWNER_EMAIL", "").casefold()
    if not supabase_url or not supabase_anon_key or not owner_email:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Owner authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in is required")
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{supabase_url}/auth/v1/user", headers={"apikey": supabase_anon_key, "Authorization": authorization})
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is invalid")
    email = str(response.json().get("email", "")).casefold()
    if email != owner_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the workspace owner can change the schedule")
    return email
