from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.integrations.modes import all_modes, any_demo
from app.routers import capture, facilities, language, redistribution, states
from app.store import InvalidAction, NotFound

app = FastAPI(title=settings.project_name, description="PHC Pulse API. Synthetic demo data is labelled as such.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (facilities, capture, redistribution, language, states):
    app.include_router(r.router)


@app.exception_handler(NotFound)
async def not_found(_: Request, exc: NotFound) -> JSONResponse:
    return JSONResponse({"detail": str(exc.args[0] if exc.args else exc)}, status_code=404)


@app.exception_handler(InvalidAction)
async def invalid(_: Request, exc: InvalidAction) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=400)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "project": settings.project_name, "model": settings.gemini_model,
            "demo_mode": any_demo(), "integrations": {m["id"]: m["mode"] for m in all_modes()}}
