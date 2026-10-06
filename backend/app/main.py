"""
FastAPI application entry point for Sahayak Voice V2.
Sets up CORS, registers routes and WebSocket endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as http_router
from app.api.websocket import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle manager."""
    print("🚀 Sahayak Voice V2 Backend Started — Port 8001 ready.")
    yield
    print("🛑 Sahayak Voice V2 Backend Stopped.")


app = FastAPI(
    title="Sahayak Voice V2",
    description="Gujarati Voice AI Relationship Manager for Indian Retail Banking",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router)
app.include_router(ws_router)
