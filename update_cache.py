import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()

Maps_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
def save_cache(cache):
    """Save the cache to the shared folder."""
    with open("shared_folder/location_cache.json", "w") as f:
        json.dump(cache, f, indent=4)
def get_bounding(location_name):
    """Get the bounding box for a location name."""    
    # Call the Google Maps API or any other service to get the bounding box
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={location_name}&key={Maps_API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching data for {location_name}: {response.status_code}")
        return None
    data = response.json()
    # if the bounding box is wider or longer than 0.01 degree, return json object in format of
    # {"east": 0.01, "west": -0.01, "north": 0.01, "south": -0.01}
    # otherwise, return {"lat": 0.01, "lon": -0.01}
    if data['results']:
        bounds = data['results'][0].get('geometry', {}).get('bounds', {})
        if bounds:
            northeast = bounds.get('northeast', {})
            southwest = bounds.get('southwest', {})
            bounding_box = {
                "east": northeast.get('lng', 0.01),
                "west": southwest.get('lng', -0.01),
                "north": northeast.get('lat', 0.01),
                "south": southwest.get('lat', -0.01)
            }
            if (abs(bounding_box['east'] - bounding_box['west']) >= 0.01) or (abs(bounding_box['north'] - bounding_box['south']) >= 0.01):
                return bounding_box
        location = data['results'][0].get('geometry', {}).get('location', {})
        bounding_box = {
            "lat": location.get('lat', 0.01),
            "lon": location.get('lng', -0.01)
        }
        return bounding_box
    else:
        print(f"No results found for {location_name}")
        return None
def update_cache():
    try:
        with open("shared_folder/location_cache.json", "r") as f:
            cache = json.load(f)
    except:
        cache = {}
    print(f"Cache loaded with {len(cache)} entries.")
    with open("shared_folder/tagged_messages.json", "r") as f:
        tagged_messages = json.load(f)



    for msg in tagged_messages:
        for loc in msg["locations"]:
            if loc.lower() not in cache:
                print(f"Adding {loc} to cache")
                cache[loc.lower()] = get_bounding(loc)
                save_cache(cache)
        # Save the updated cache
    save_cache(cache)