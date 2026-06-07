from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers.ads import router as ads_router
from .routers.calibration import router as calibration_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="ai-ad API",
    description="抖音广告视频洞察笔记生成器 — Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ads_router)
app.include_router(calibration_router)


@app.get("/")
async def root():
    return {"service": "ai-ad", "status": "running", "docs": "/docs"}
