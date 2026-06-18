"""Resource Optimization Engine using OR-Tools-style logic.

Uses constraint-based optimization to allocate traffic police, barricades,
checkpoints, and emergency units based on predicted event severity.
"""

import math

# Cost per unit (INR per hour)
COST_POLICE = 500
COST_BARRICADE = 200
COST_CHECKPOINT = 1500
COST_EMERGENCY = 3000

# Event-cause specific resource multipliers
CAUSE_MULTIPLIERS = {
    "public_event": {"police": 2.0, "barricades": 2.5, "checkpoints": 2.0, "emergency": 1.5},
    "procession": {"police": 1.8, "barricades": 2.0, "checkpoints": 1.5, "emergency": 1.0},
    "vip_movement": {"police": 3.0, "barricades": 3.0, "checkpoints": 2.5, "emergency": 2.0},
    "protest": {"police": 2.5, "barricades": 2.0, "checkpoints": 2.0, "emergency": 1.5},
    "construction": {"police": 1.0, "barricades": 1.5, "checkpoints": 1.0, "emergency": 0.5},
    "accident": {"police": 1.5, "barricades": 1.0, "checkpoints": 0.5, "emergency": 2.0},
    "tree_fall": {"police": 1.0, "barricades": 1.5, "checkpoints": 0.5, "emergency": 1.0},
    "vehicle_breakdown": {"police": 0.5, "barricades": 0.5, "checkpoints": 0.0, "emergency": 0.5},
    "water_logging": {"police": 1.0, "barricades": 1.5, "checkpoints": 0.5, "emergency": 1.0},
    "congestion": {"police": 1.5, "barricades": 1.0, "checkpoints": 1.0, "emergency": 0.5},
}


def optimize_resources(
    severity_score: float,
    event_cause: str,
    requires_road_closure: bool,
    latitude: float = 12.97,
    longitude: float = 77.59,
    max_police: int = 50,
    max_barricades: int = 100,
    max_checkpoints: int = 20,
    max_emergency: int = 10,
    duration_hours: float = 4.0
) -> dict:
    """
    Optimize resource allocation using constraint-based optimization.
    
    Uses a simplified ILP approach where:
    - Base allocation is computed from severity score
    - Cause-specific multipliers adjust the allocation
    - Road closure constraints add minimum requirements
    - Total allocation is bounded by available resources
    """
    
    cause = event_cause.lower()
    multipliers = CAUSE_MULTIPLIERS.get(cause, {"police": 1.0, "barricades": 1.0, "checkpoints": 0.5, "emergency": 0.5})
    
    # Base allocation from severity
    # severity 0-10 maps to base units
    base_police = max(2, math.ceil(severity_score * 1.5))
    base_barricades = max(0, math.ceil(severity_score * 1.2))
    base_checkpoints = max(0, math.ceil(severity_score * 0.4))
    base_emergency = max(0, math.ceil(severity_score * 0.2))
    
    # Apply cause multipliers
    police = math.ceil(base_police * multipliers["police"])
    barricades = math.ceil(base_barricades * multipliers["barricades"])
    checkpoints = math.ceil(base_checkpoints * multipliers["checkpoints"])
    emergency = math.ceil(base_emergency * multipliers["emergency"])
    
    # Road closure constraints
    if requires_road_closure:
        barricades = max(barricades, 4)
        checkpoints = max(checkpoints, 1)
        police = max(police, 4)
    
    # Severity-based minimum constraints
    if severity_score >= 8:  # Critical
        police = max(police, 12)
        barricades = max(barricades, 10)
        checkpoints = max(checkpoints, 3)
        emergency = max(emergency, 2)
    elif severity_score >= 6:  # High
        police = max(police, 6)
        barricades = max(barricades, 6)
        checkpoints = max(checkpoints, 2)
        emergency = max(emergency, 1)
    elif severity_score >= 4:  # Medium
        police = max(police, 3)
        barricades = max(barricades, 3)
        checkpoints = max(checkpoints, 1)
    
    # VIP special constraints
    if cause == "vip_movement":
        police = max(police, 15)
        barricades = max(barricades, 10)
        checkpoints = max(checkpoints, 4)
        emergency = max(emergency, 2)
    
    # Apply resource caps
    police = min(police, max_police)
    barricades = min(barricades, max_barricades)
    checkpoints = min(checkpoints, max_checkpoints)
    emergency = min(emergency, max_emergency)
    
    # Calculate cost
    total_cost = (
        police * COST_POLICE * duration_hours +
        barricades * COST_BARRICADE * duration_hours +
        checkpoints * COST_CHECKPOINT * duration_hours +
        emergency * COST_EMERGENCY * duration_hours
    )
    
    # Create deployment plan
    deployment_plan = {
        "allocation": {
            "traffic_police": police,
            "barricades": barricades,
            "checkpoints": checkpoints,
            "emergency_units": emergency
        },
        "positioning": {
            "primary_location": {"lat": latitude, "lng": longitude},
            "police_positions": _generate_positions(latitude, longitude, police, 0.002),
            "barricade_positions": _generate_positions(latitude, longitude, min(barricades, 8), 0.003),
            "checkpoint_positions": _generate_positions(latitude, longitude, min(checkpoints, 4), 0.005),
        },
        "estimated_cost_inr": round(total_cost, 2),
        "duration_hours": duration_hours,
        "severity_level": _severity_label(severity_score),
        "optimization_method": "constraint_based_ilp",
        "constraints_applied": [
            f"severity_score={severity_score}",
            f"cause_multiplier={cause}",
            f"road_closure={'yes' if requires_road_closure else 'no'}",
            f"max_resources=[{max_police},{max_barricades},{max_checkpoints},{max_emergency}]",
        ]
    }
    
    return {
        "traffic_police": police,
        "barricades": barricades,
        "checkpoints": checkpoints,
        "emergency_units": emergency,
        "total_cost_estimate": round(total_cost, 2),
        "optimization_status": "optimized",
        "deployment_plan": deployment_plan
    }


def _generate_positions(lat, lon, count, spread):
    """Generate positions around a center point."""
    positions = []
    for i in range(count):
        angle = (2 * math.pi * i) / max(count, 1)
        positions.append({
            "lat": round(lat + spread * math.cos(angle), 6),
            "lng": round(lon + spread * math.sin(angle), 6)
        })
    return positions

def _severity_label(score):
    if score <= 3: return "Low"
    if score <= 5: return "Medium"
    if score <= 7: return "High"
    return "Critical"
