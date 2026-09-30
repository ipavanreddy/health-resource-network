"""Shared router dependencies. Exactly two roles: PHC Staff and District Health Officer.

Demo auth: the role comes from the `X-Role` header set by each app. Production would derive it from a
Firebase Auth ID token (custom claim `role`).
"""
from fastapi import Header, HTTPException

from app.store import Store, get_store

PHC_STAFF = "phc_staff"
DHO = "district_health_officer"
ROLES = {PHC_STAFF, DHO}


def store() -> Store:
    return get_store()


def role(x_role: str = Header(default=PHC_STAFF)) -> str:
    if x_role not in ROLES:
        raise HTTPException(403, f"Unknown role {x_role}; expected one of {sorted(ROLES)}")
    return x_role


def require_dho(x_role: str = Header(default=PHC_STAFF)) -> str:
    if role(x_role) != DHO:
        raise HTTPException(403, "Only the District Health Officer can do this")
    return x_role
