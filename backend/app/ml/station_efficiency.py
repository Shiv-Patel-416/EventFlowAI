"""
EventFlow AI — Police Station Efficiency Engine (Step 7)

Computes an efficiency_score per police station from historical event data.
Score = how much faster/slower a station resolves events vs. the ML baseline.

Score > 1.0 → station resolves faster than average (good)
Score < 1.0 → station resolves slower (understaffed / poor access)
Score = 1.0 → exactly at baseline

This score is:
  (a) Exposed as the Leaderboard API (/api/leaderboard)
  (b) Injected as a new feature into the Duration ML model to localise predictions
"""
import csv, json, math, os
from collections import defaultdict
from typing import Dict, List, Optional

# Baseline average resolution hours per cause (from training data)
BASELINE_HOURS = {
    "vehicle_breakdown": 0.97,  "others": 5.0,    "pot_holes": 4.0,
    "construction": 4.0,        "water_logging": 3.0, "accident": 0.80,
    "tree_fall": 2.5,           "road_conditions": 4.0, "congestion": 1.24,
    "public_event": 4.0,        "procession": 0.91,  "vip_movement": 3.0,
    "protest": 0.41,            "debris": 5.0,     "fog_low_visibility": 2.0,
}
GLOBAL_BASELINE_HOURS = 2.5   # fallback when cause unknown
MIN_EVENTS_FOR_SCORE  = 3     # minimum events to compute a reliable score


def _parse_dt(s: str):
    if not s or s.strip() in ("NULL", "null", ""):
        return None
    try:
        base = s.strip().split("+")[0].split(".")[0]
        from datetime import datetime
        return datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def compute_station_efficiency(raw_csv_path: str) -> Dict[str, dict]:
    """
    Read raw event CSV, group by police_station, compute:
      - avg_resolution_hours
      - baseline_hours (weighted avg of cause-level baselines)
      - efficiency_score = baseline / actual (>1 is faster)
      - total_events, resolved_events, fast_resolve_rate (<=60 min)
    Returns dict keyed by station name.
    """
    station_events = defaultdict(list)

    with open(raw_csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cause = row.get("event_cause", "").lower().strip()
            if cause == "test_demo":
                continue
            ps = row.get("police_station", "").strip()
            if not ps or ps in ("NULL", "null", ""):
                ps = "Unknown"

            start = _parse_dt(row.get("start_datetime", ""))
            closed = _parse_dt(row.get("closed_datetime", "")) or \
                     _parse_dt(row.get("resolved_datetime", ""))
            if start is None:
                continue

            res_hours = None
            if closed:
                diff = (closed - start).total_seconds() / 3600
                if 0 < diff < 720:
                    res_hours = diff

            station_events[ps].append({
                "cause": cause,
                "resolution_hours": res_hours,
            })

    leaderboard = {}
    for ps, events in station_events.items():
        total = len(events)
        resolved = [e for e in events if e["resolution_hours"] is not None]
        n_resolved = len(resolved)

        if n_resolved == 0:
            avg_actual   = None
            avg_baseline = GLOBAL_BASELINE_HOURS
            efficiency   = 1.0          # neutral — no data
        else:
            avg_actual   = sum(e["resolution_hours"] for e in resolved) / n_resolved
            avg_baseline = sum(
                BASELINE_HOURS.get(e["cause"], GLOBAL_BASELINE_HOURS)
                for e in resolved
            ) / n_resolved
            if avg_actual > 0:
                efficiency = avg_baseline / avg_actual
            else:
                efficiency = 1.0

        fast = sum(
            1 for e in resolved
            if e["resolution_hours"] is not None and e["resolution_hours"] * 60 <= 60
        )
        fast_rate = fast / max(n_resolved, 1)

        # Rank label
        if efficiency >= 1.3:     rank = "Excellent"
        elif efficiency >= 1.0:   rank = "Good"
        elif efficiency >= 0.7:   rank = "Average"
        else:                     rank = "Needs Improvement"

        leaderboard[ps] = {
            "police_station":      ps,
            "total_events":        total,
            "resolved_events":     n_resolved,
            "avg_resolution_hours": round(avg_actual, 3) if avg_actual else None,
            "baseline_hours":      round(avg_baseline, 3),
            "efficiency_score":    round(min(efficiency, 3.0), 4),  # cap at 3x
            "fast_resolve_rate":   round(fast_rate, 4),
            "rank_label":          rank,
            "reliable":            n_resolved >= MIN_EVENTS_FOR_SCORE,
        }

    return leaderboard


def build_leaderboard(raw_csv_path: str, output_path: Optional[str] = None) -> List[dict]:
    """Build sorted leaderboard list and optionally save to JSON."""
    data   = compute_station_efficiency(raw_csv_path)
    board  = sorted(data.values(), key=lambda x: -x["efficiency_score"])

    # Add rank position
    for i, row in enumerate(board, 1):
        row["rank"] = i

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"leaderboard": board, "total_stations": len(board)}, f, indent=2)
        print(f"Leaderboard saved → {output_path} ({len(board)} stations)")

    return board


def get_station_efficiency_score(station_name: str,
                                 leaderboard: List[dict]) -> float:
    """
    Lookup efficiency_score for a given station from a pre-built leaderboard.
    Returns 1.0 (neutral) if station not found or has insufficient data.
    """
    for row in leaderboard:
        if row["police_station"] == station_name and row.get("reliable", False):
            return float(row["efficiency_score"])
    return 1.0   # neutral — no reliable history


# ── Singleton cache loaded at runtime ─────────────────────────────────────────
_cached_leaderboard: List[dict] = []
_leaderboard_map:   Dict[str, float] = {}


def load_leaderboard_cache(json_path: str) -> bool:
    global _cached_leaderboard, _leaderboard_map
    if not os.path.exists(json_path):
        print(f"[StationEfficiency] No leaderboard file at {json_path}. Using neutral scores.")
        return False
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    _cached_leaderboard = data.get("leaderboard", [])
    _leaderboard_map = {
        r["police_station"]: r["efficiency_score"]
        for r in _cached_leaderboard
        if r.get("reliable", False)
    }
    print(f"[StationEfficiency] Loaded {len(_cached_leaderboard)} stations, "
          f"{len(_leaderboard_map)} reliable scores")
    return True


def lookup_efficiency(station: str) -> float:
    """Fast O(1) lookup from the in-memory cache."""
    return _leaderboard_map.get(station, 1.0)


def get_cached_leaderboard() -> List[dict]:
    return _cached_leaderboard


# ── CLI entry-point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    base    = os.path.dirname(__file__)
    raw     = os.path.join(base, "..", "data", "raw", "events_raw.csv")
    out     = os.path.join(base, "..", "data", "processed", "leaderboard.json")
    board   = build_leaderboard(raw, out)
    print(f"\nTop 10 Police Stations by Efficiency:")
    print(f"{'Rank':>4} {'Station':30} {'Score':>6} {'Avg Res(h)':>10} {'Label'}")
    print("-"*65)
    for r in board[:10]:
        avg = f"{r['avg_resolution_hours']:.2f}" if r['avg_resolution_hours'] else "N/A"
        print(f"  {r['rank']:>2}  {r['police_station']:30} {r['efficiency_score']:>6.3f} "
              f"{avg:>10}   {r['rank_label']}")
