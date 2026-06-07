from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────

class Industry(str, enum.Enum):
    beauty = "美妆"
    food = "食品"
    electronics = "3C"
    education = "教育"
    ecommerce = "电商"
    finance = "金融"
    gaming = "游戏"
    other = "其他"


class PriceRange(str, enum.Enum):
    low = "低价"
    mid = "中价"
    high = "高价"
    free = "免费"
    unknown = "不清楚"


class Platform(str, enum.Enum):
    douyin = "抖音"
    xiaohongshu = "小红书"
    shipinhao = "视频号"
    kuaishou = "快手"
    other = "其他"


class AdStatus(str, enum.Enum):
    pending = "pending"
    analyzing = "analyzing"
    completed = "completed"
    failed = "failed"


# ── Request schemas ────────────────────────────────────

class AdCreateRequest(BaseModel):
    ad_title: Optional[str] = Field(default=None, max_length=200)
    brand_name: str = Field(..., min_length=1, max_length=100)
    product_name: Optional[str] = Field(default=None, max_length=200)
    industry: Industry
    price_range: Optional[PriceRange] = None
    ad_copy: Optional[str] = Field(default=None, max_length=5000)
    scene_description: Optional[str] = Field(default=None, max_length=3000)
    screenshot_description: Optional[str] = Field(default=None, max_length=2000)
    user_context: Optional[str] = Field(default=None, max_length=2000)
    seen_at: Optional[str] = None
    platform: Platform


# ── Response schemas ───────────────────────────────────

class AdSummary(BaseModel):
    id: str
    brand_name: str
    product_name: Optional[str] = None
    industry: str
    platform: str
    status: str
    created_at: str
    one_sentence_takeaway: Optional[str] = None


class AdDetail(BaseModel):
    id: str
    status: str
    ad_title: Optional[str] = None
    brand_name: str
    product_name: Optional[str] = None
    industry: str
    price_range: Optional[str] = None
    ad_copy: Optional[str] = None
    scene_description: Optional[str] = None
    screenshot_description: Optional[str] = None
    user_context: Optional[str] = None
    seen_at: Optional[str] = None
    platform: str
    analysis: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class AdCreateResponse(BaseModel):
    id: str
    status: str
    created_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    mock_mode: bool


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[list] = None


# ── Link parsing schemas ───────────────────────────────

class ParseLinkRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class ParseLinkResponse(BaseModel):
    url: str
    platform: str = ""
    title: str = ""
    author: str = ""
    description: str = ""
    thumbnail_url: str = ""
    parsed: bool = False
    error: str = ""


# ── Media analysis schemas ─────────────────────────────

class MediaAnalyzeRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class MediaSegment(BaseModel):
    start: float
    end: float
    text: str


class MediaFrame(BaseModel):
    path: str
    filename: str
    timestamp: float
    width: int = 0
    height: int = 0


class MediaAnalyzeResponse(BaseModel):
    url: str
    duration: float = 0.0
    transcript: str = ""
    transcript_segments: list[MediaSegment] = []
    transcript_language: str = ""
    frame_count: int = 0
    error: str = ""


# ── Automatic job workflow schemas ─────────────────────

class JobCreateRequest(BaseModel):
    share_text: str = Field(..., min_length=1, max_length=10000)


class MetadataConfirmationRequest(BaseModel):
    brand_name: Optional[str] = Field(default=None, max_length=100)
    product_name: Optional[str] = Field(default=None, max_length=200)
    industry: Optional[Industry] = None


class JobCreateResponse(BaseModel):
    id: str
    status: str
    stage: str
    next_url: str
