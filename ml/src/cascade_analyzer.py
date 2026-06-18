"""
EventFlow AI — Congestion Cascade Analyzer (Step 3C)

Builds a junction co-occurrence matrix from historical data to predict whether
an event at Junction A is likely to trigger a secondary incident at a nearby
Junction B within a 60-minute window.

The cascade_probability score is then injected as a new feature into the
Duration model, explaining the "why" behind long-tail resolution times.

Usage:
    python -m ml.src.cascade_analyzer
"""

import csv
import json
import math
import os
from collections import defaultdict
from datetime import datetime, timedelta


# ────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────
CASCADE_WINDOW_MINUTES = 60       # Time window to detect cascade pairs
CASCADE_RADIUS_KM      = 5.0      # Spatial radius for "nearby" junctions
MIN_CO_OCCURRENCES     = 2        # Minimum observed pairs to trust the rate
DEFAULT_CASCADE_PROB   = 0.05     # Fallback when no history exists

# Causes known to amplify cascades (spill-on-road, mass gatherings, etc.)
HIGH_CASCADE_CAUSES = {
    "accident", "public_event", "procession", "vip_movement",
    "protest", "construction", "congestion",
}
LOW_CASCADE_CAUSES = {
    "vehicle_breakdown", "pot_holes", "debris",
    "fog_low_visibility", "water_logging",
}


# ────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(max(0.0, a)))


def _parse_dt(s: str):
    """Parse a datetime string robustly; returns None on failure."""
    if not s or s.strip() in ("NULL", "null", ""):
        return None
    try:
        base = s.strip().split("+")[0].split(".")[0]
        return datetime.strptime(base, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


# ────────────────────────────────────────────────────
# Phase 1 – Build Co-occurrence Matrix
# ────────────────────────────────────────────────────
def build_cooccurrence_matrix(raw_path: str) -> dict:
    """
    Scan every pair of events in the dataset.
    If event_B starts within CASCADE_WINDOW_MINUTES of event_A
    AND both events are within CASCADE_RADIUS_KM of each other,
    record the (junction_A → junction_B) pair as a cascade.

    Returns:
        {
          "pair_counts":  { "JuncA||JuncB": int },   # raw co-occurrences
          "pair_rates":   { "JuncA||JuncB": float },  # P(B | A happened)
          "origin_counts":{ "JuncA": int },            # how often A appears
          "cause_cascade_rates": { "cause": float },  # P(cascade | cause)
        }
    """
    print("=" * 60)
    print("Cascade Analyzer — Building Co-occurrence Matrix")
    print("=" * 60)

    # ── Load raw events ──────────────────────────────
    events = []
    with open(raw_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cause = row.get("event_cause", "").lower().strip()
            if cause == "test_demo":
                continue
            try:
                lat = float(row["latitude"])
                lon = float(row["longitude"])
                if lat == 0 or lon == 0:
                    continue
            except Exception:
                continue

            start_dt = _parse_dt(row.get("start_datetime", ""))
            if start_dt is None:
                continue

            events.append({
                "id":          row.get("id", ""),
                "junction":    row.get("junction", "Unknown").strip() or "Unknown",
                "corridor":    row.get("corridor", "Unknown").strip() or "Unknown",
                "lat":         lat,
                "lon":         lon,
                "cause":       cause,
                "start_dt":    start_dt,
                "priority":    row.get("priority", "Low").strip(),
            })

    print(f"Loaded {len(events)} events for cascade analysis")

    # ── Sort by time for efficient windowed search ───
    events.sort(key=lambda e: e["start_dt"])

    # ── Co-occurrence counting ───────────────────────
    pair_counts  = defaultdict(int)   # (juncA||juncB) → count
    origin_count = defaultdict(int)   # juncA → total appearances as origin

    cause_total   = defaultdict(int)  # cause → total events
    cause_cascade = defaultdict(int)  # cause → events that triggered a cascade

    n = len(events)
    cascade_events_found = 0

    for i, ev_a in enumerate(events):
        junc_a   = ev_a["junction"]
        cause_a  = ev_a["cause"]
        origin_count[junc_a] += 1
        cause_total[cause_a] += 1

        window_end = ev_a["start_dt"] + timedelta(minutes=CASCADE_WINDOW_MINUTES)
        triggered  = False

        # Scan forward until outside time window
        for j in range(i + 1, n):
            ev_b = events[j]
            if ev_b["start_dt"] > window_end:
                break

            junc_b = ev_b["junction"]
            if junc_b == junc_a:          # same junction — not a cascade
                continue

            dist_km = _haversine(ev_a["lat"], ev_a["lon"],
                                 ev_b["lat"], ev_b["lon"])
            if dist_km <= CASCADE_RADIUS_KM:
                pair_key = f"{junc_a}||{junc_b}"
                pair_counts[pair_key] += 1
                cascade_events_found  += 1
                triggered = True

        if triggered:
            cause_cascade[cause_a] += 1

    print(f"Found {cascade_events_found} cascade event-pairs")

    # ── Compute conditional rates ────────────────────
    pair_rates = {}
    for pair_key, count in pair_counts.items():
        junc_a = pair_key.split("||")[0]
        total  = origin_count.get(junc_a, 1)
        pair_rates[pair_key] = round(count / total, 4)

    cause_cascade_rates = {}
    for cause, total in cause_total.items():
        c_count = cause_cascade.get(cause, 0)
        cause_cascade_rates[cause] = round(c_count / max(total, 1), 4)

    # ── Summary ──────────────────────────────────────
    print(f"\nUnique cascade pairs found: {len(pair_counts)}")
    print("\nTop 10 cascade pairs (junction_A -> junction_B):")
    top_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:10]
    for pair_key, count in top_pairs:
        a, b = pair_key.split("||")
        rate = pair_rates.get(pair_key, 0)
        print(f"  {a:25s} -> {b:25s}  count={count:3d}  rate={rate:.3f}")

    print("\nCascade probability by event cause:")
    for cause, rate in sorted(cause_cascade_rates.items(), key=lambda x: -x[1]):
        print(f"  {cause:30s}: {rate:.3f}")

    return {
        "pair_counts":         dict(pair_counts),
        "pair_rates":          pair_rates,
        "origin_counts":       dict(origin_count),
        "cause_cascade_rates": cause_cascade_rates,
    }


# ────────────────────────────────────────────────────
# Phase 2 – Compute Per-Event Cascade Score
# ────────────────────────────────────────────────────
def compute_cascade_scores(records: list, matrix: dict) -> list:
    """
    For every cleaned record, compute a cascade_probability score between 0–1.

    Score formula (weighted combination):
        score = w1 * cause_rate
              + w2 * max(pair_rate for all known cascade partners of this junction)
              + w3 * peak_hour_bonus
              + w4 * priority_bonus
        (clamped to [0, 1])

    Args:
        records : list of cleaned record dicts (from data_pipeline.clean_data)
        matrix  : output of build_cooccurrence_matrix()

    Returns:
        Same records list with 'cascade_probability' field added.
    """
    pair_rates          = matrix.get("pair_rates", {})
    cause_cascade_rates = matrix.get("cause_cascade_rates", {})
    pair_counts         = matrix.get("pair_counts", {})

    # Pre-build: junction → best cascade rate as an ORIGIN
    junction_max_rate = defaultdict(float)
    for pair_key, rate in pair_rates.items():
        junc_a = pair_key.split("||")[0]
        count  = pair_counts.get(pair_key, 0)
        if count >= MIN_CO_OCCURRENCES:
            junction_max_rate[junc_a] = max(junction_max_rate[junc_a], rate)

    enriched = []
    for r in records:
        cause    = r.get("event_cause", "others")
        junction = r.get("junction", "Unknown")
        hour     = r.get("hour_ist", 12)
        priority = r.get("priority", "Low")

        # Component 1: Historical cause-level cascade rate
        cause_rate = cause_cascade_rates.get(cause, DEFAULT_CASCADE_PROB)

        # Component 2: Junction-specific cascade propensity
        junc_rate = junction_max_rate.get(junction, DEFAULT_CASCADE_PROB)

        # Component 3: Peak-hour multiplier (rush hour = more cascades)
        is_peak = 1 if (7 <= hour <= 10 or 17 <= hour <= 21) else 0
        peak_bonus = 0.08 if is_peak else 0.0

        # Component 4: High-priority flag
        priority_bonus = 0.05 if priority == "High" else 0.0

        # Component 5: Cause-type category bonus
        if cause in HIGH_CASCADE_CAUSES:
            type_bonus = 0.06
        elif cause in LOW_CASCADE_CAUSES:
            type_bonus = -0.04
        else:
            type_bonus = 0.0

        # Weighted combination
        cascade_prob = (
            0.40 * cause_rate
            + 0.35 * junc_rate
            + peak_bonus
            + priority_bonus
            + type_bonus
        )

        # Clamp to [0, 1]
        cascade_prob = round(max(0.0, min(1.0, cascade_prob)), 4)

        r_copy = dict(r)
        r_copy["cascade_probability"] = cascade_prob
        enriched.append(r_copy)

    avg_cascade = sum(e["cascade_probability"] for e in enriched) / max(len(enriched), 1)
    high_cascade = sum(1 for e in enriched if e["cascade_probability"] > 0.3)
    print(f"Cascade scores computed: avg={avg_cascade:.3f}, "
          f"high-risk (>0.3) = {high_cascade}/{len(enriched)}")
    return enriched


# ────────────────────────────────────────────────────
# Phase 3 – Save Matrix as JSON artifact
# ────────────────────────────────────────────────────
def save_matrix(matrix: dict, output_dir: str) -> str:
    """Persist the co-occurrence matrix to disk for the backend runtime."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "cascade_matrix.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2)
    print(f"Cascade matrix saved -> {path}")
    return path


# ────────────────────────────────────────────────────
# Standalone entry-point
# ────────────────────────────────────────────────────
if __name__ == "__main__":
    base      = os.path.dirname(__file__)
    raw_path  = os.path.join(base, "..", "data", "raw", "events_raw.csv")
    out_dir   = os.path.join(base, "..", "data", "processed")

    matrix = build_cooccurrence_matrix(raw_path)
    save_matrix(matrix, out_dir)
    print("\nDone. Run data_pipeline.py next to inject cascade features.")
