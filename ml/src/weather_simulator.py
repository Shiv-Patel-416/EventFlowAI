"""
EventFlow AI — Weather Simulator
Injects historical weather data (rainfall_mm) into the dataset based on 
seasonal monsoon patterns. In production, this would be replaced by an 
OpenWeatherMap API historical bulk download.
"""
import random

# Typical monsoon rainfall probabilities in Bangalore/India
MONTHLY_RAIN_PROB = {
    1: 0.05, 2: 0.05, 3: 0.10, 4: 0.20,  # Pre-monsoon
    5: 0.40, 6: 0.60, 7: 0.70, 8: 0.75,  # Monsoons
    9: 0.65, 10: 0.50, 11: 0.20, 12: 0.10 # Post-monsoon
}

def get_historical_weather(month: int, hour: int, seed_id: str) -> float:
    """
    Simulates historical rainfall based on the month.
    Uses the event ID as a random seed so the simulation is deterministic 
    and reproducible across pipeline runs.
    Returns: rainfall_mm (float)
    """
    # Deterministic randomness based on event ID
    random.seed(seed_id)
    
    prob = MONTHLY_RAIN_PROB.get(month, 0.10)
    
    # Evening/night rain is slightly more common in tropical climates
    if 16 <= hour <= 22:
        prob *= 1.2
        
    is_raining = random.random() < prob
    
    if is_raining:
        # Generate between 2mm (light rain) and 45mm (heavy downpour)
        rainfall_mm = round(random.uniform(2.0, 45.0), 2)
    else:
        rainfall_mm = 0.0
        
    return rainfall_mm
