import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import rest, ws
from backend.core.db import connect, migrate
from backend.core.wake_loop import start as start_wake_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    ran = migrate(connect())
    if ran:
        print(f"applied migrations: {', '.join(ran)}")
    start_wake_loop(asyncio.get_running_loop())
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="A.R.I.A.", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(rest.router)
    app.include_router(ws.router)
    return app


app = create_app()
