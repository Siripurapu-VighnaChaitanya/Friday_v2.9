import requests
import webbrowser

def get_coordinates(location_name):
    """
    Uses OpenStreetMap's Nominatim Geocoding API to find the exact latitude and longitude of a place.
    Nominatim is 100% free and requires NO API KEY!
    """
    # Nominatim aggressively blocks non-browser User-Agents, so we mock a Chrome browser here.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    url = f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json&limit=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                # Return lon, lat (Nominatim returns strings for lat/lon, so we cast to float or just use as string)
                lat = data[0]['lat']
                lon = data[0]['lon']
                return (lon, lat), f"I have located {location_name}."
            else:
                return None, f"I couldn't find a location named {location_name}."
        else:
            return None, "There was an error connecting to the mapping service."
    except Exception as e:
        print(f"❌ Nominatim API Error: {e}")
        return None, "There was an error communicating with the map server."

def open_map(location_name):
    """
    Finds the coordinates and opens a browser pointing to the location.
    """
    coords, msg = get_coordinates(location_name)
    if coords:
        lon, lat = coords
        # Open Google Maps since it's the most user-friendly web UI
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        webbrowser.open(url)
        return msg
    return msg

if __name__ == "__main__":
    print(open_map("Statue of Liberty"))
