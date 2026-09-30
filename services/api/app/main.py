import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.integrations.modes import all_modes, start_probes
from app.routers import capture, facilities, language, redistribution, states
from app.store import InvalidAction, NotFound

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_probes()  # verify each configured Google integration in the background
    yield


app = FastAPI(title=settings.project_name, description="PHC Pulse API. Synthetic demo data is labelled as such.",
              lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_origin_regex=settings.cors_origin_regex or None,
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
    modes = all_modes(wait_seconds=0)
    return {"status": "ok", "project": settings.project_name, "model": settings.gemini_model,
            "demo_mode": any(m["mode"] == "demo" for m in modes), "integrations": {m["id"]: m["mode"] for m in modes}}
