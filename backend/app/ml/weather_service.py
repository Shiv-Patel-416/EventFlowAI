import requests
from datetime import datetime
from app.config import settings

# This would normally be set in .env
# We'll use a free tier OpenWeatherMap geocoding / current weather endpoint
# If no key is provided, we fall back to a reasonable default based on month/time
WEATHER_API_KEY = getattr(settings, 'WEATHER_API_KEY', None)

def get_current_rainfall_mm(lat: float, lon: float) -> float:
    """
    Pings OpenWeatherMap to get the current rainfall in mm for the last hour.
    If the API fails or no key is present, falls back to a seasonal average.
    """
    if not WEATHER_API_KEY:
        return _fallback_weather_logic()
        
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            # OpenWeatherMap returns rain in a 'rain' dict, usually '1h' key
            if 'rain' in data and '1h' in data['rain']:
                return float(data['rain']['1h'])
            return 0.0
        else:
            print(f"[WeatherService] API error: {response.status_code}")
            return _fallback_weather_logic()
            
    except Exception as e:
        print(f"[WeatherService] Exception: {e}")
        return _fallback_weather_logic()

def _fallback_weather_logic() -> float:
    """
    If the API is down, we use a simple heuristic:
    Is it monsoon season in Bangalore? Is it evening?
    """
    now = datetime.now()
    month = now.month
    hour = now.hour
    
    # Bangalore monsoon peaks in July-Sept
    if 6 <= month <= 10:
        # Higher chance in late afternoon/evening
        if 15 <= hour <= 21:
            return 12.5  # Heavy-ish rain
        return 3.0       # Light rain
        
    return 0.0           # Dry season
