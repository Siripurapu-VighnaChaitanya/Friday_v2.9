import requests
from utils.config import WEATHER_API_KEY

def get_weather(location):
    """
    Fetches the current weather for a specific location using WeatherAPI.com.
    Returns a natural language string for Friday to speak.
    """
    if not WEATHER_API_KEY:
        return "I cannot check the weather because the Weather API Key is missing from your config file."
    
    if not location:
        return "Please specify a city name to check the weather."

    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data['location']['name']
            temp_c = data['current']['temp_c']
            condition = data['current']['condition']['text']
            
            return f"The current weather in {city} is {temp_c} degrees Celsius and {condition.lower()}."
        else:
            return "I couldn't find the weather for that location. Please try again."
    except Exception as e:
        print(f"❌ Weather API Error: {e}")
        return "There was an error communicating with the weather service."

if __name__ == "__main__":
    # Test case (will fail without a key)
    print(get_weather("Hyderabad"))
