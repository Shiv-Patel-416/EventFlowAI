"""
Leaderboard Router (Step 7)
GET  /api/leaderboard          — full ranked list
GET  /api/leaderboard/{station} — single station card
POST /api/leaderboard/refresh   — rebuild from raw CSV (admin action)
"""
import os
from fastapi import APIRouter, HTTPException
from app.ml.station_efficiency import (
    get_cached_leaderboard, load_leaderboard_cache,
    build_leaderboard, lookup_efficiency,
)
from app.config import settings

router = APIRouter()

# Path where the leaderboard JSON is stored
LEADERBOARD_JSON = os.path.join(
    settings.DATA_DIR, "processed", "leaderboard.json"
)
RAW_CSV = os.path.join(
    settings.DATA_DIR, "raw", "events_raw.csv"
)

# Load on startup
load_leaderboard_cache(LEADERBOARD_JSON)


@router.get("")
async def get_leaderboard(limit: int = 50, min_events: int = 1):
    """
    Return ranked police station leaderboard.
    - limit      : how many stations to return (default 50)
    - min_events : only include stations with >= N resolved events
    """
    board = get_cached_leaderboard()
    if not board:
        raise HTTPException(
            status_code=503,
            detail="Leaderboard not yet built. POST /api/leaderboard/refresh to generate."
        )
    filtered = [r for r in board if r.get("resolved_events", 0) >= min_events]
    return {
        "leaderboard":    filtered[:limit],
        "total_stations": len(filtered),
        "showing":        min(limit, len(filtered)),
        "note": (
            "efficiency_score > 1.0 = resolves faster than ML baseline. "
            "This score is also injected into the Duration model as a localisation feature."
        ),
    }


@router.get("/{station_name}")
async def get_station_card(station_name: str):
    """Return efficiency card for a specific police station."""
    board = get_cached_leaderboard()
    for row in board:
        if row["police_station"].lower() == station_name.lower():
            return row
    raise HTTPException(status_code=404, detail=f"Station '{station_name}' not found.")


@router.post("/refresh")
async def refresh_leaderboard():
    """
    Rebuild leaderboard from raw event CSV.
    Triggers automatically when new feedback data accumulates.
    """
    if not os.path.exists(RAW_CSV):
        raise HTTPException(
            status_code=404,
            detail=f"Raw CSV not found at {RAW_CSV}"
        )
    board = build_leaderboard(RAW_CSV, LEADERBOARD_JSON)
    load_leaderboard_cache(LEADERBOARD_JSON)
    return {
        "status":         "rebuilt",
        "total_stations": len(board),
        "top_3": board[:3],
    }


@router.get("/score/{station_name}")
async def get_efficiency_score(station_name: str):
    """Return just the efficiency score (used by ML pipeline integration tests)."""
    score = lookup_efficiency(station_name)
    return {
        "police_station":   station_name,
        "efficiency_score": score,
        "interpretation": (
            "faster than baseline" if score > 1.0 else
            "at baseline" if score == 1.0 else
            "slower than baseline"
        ),
    }
