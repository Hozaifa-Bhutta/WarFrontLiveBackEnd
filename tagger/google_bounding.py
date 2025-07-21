import requests
import os
from call_llm import call_llm
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Get api key from .env file
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def get_bounding(name):
    """Get bounding box for a location using Google Maps Geocoding API"""
    # inputs:
    # name: location name
    # message (str): to give context to the LLM for refining the location name
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def search_location(query_name):
        """Search location via Google Maps Geocoding API"""
        params = {
            "address": query_name,
            "key": GOOGLE_MAPS_API_KEY
        }

        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("results"):
            print(f"No results found for '{query_name}'")
            return None

        for result in data["results"]:
            # Optionally: Filter out locations outside Middle East
            # Approximate bounding box of the Middle East
            if "viewport" in result["geometry"]:
                lat = result["geometry"]["location"]["lat"]
                lng = result["geometry"]["location"]["lng"]

                if 11 <= lat <= 38 and 26 <= lng <= 62:
                    return result
        print(f"No valid Middle East location found for '{query_name}'")
        return None

    # first check if the location is a valid location
   
    # If so, try original, then refined rounds
    current_name = name
    print(f"Searching for original location: '{current_name}'")
    result = search_location(current_name)

    if result is None:
        return None

    geometry = result["geometry"]
    if "viewport" in geometry:
        # check size 
        northeast = geometry["viewport"]["northeast"]["lat"]
        southwest = geometry["viewport"]["southwest"]["lat"]
        northwest = geometry["viewport"]["southwest"]["lng"]
        southeast = geometry["viewport"]["northeast"]["lng"]
        if northeast - southwest <= 0.01 and southeast - northwest <= 0.01:
            return {
                "lat": geometry["location"]["lat"],
                "lon": geometry["location"]["lng"]
            }
        return {
            "south": geometry["viewport"]["southwest"]["lat"],
            "north": geometry["viewport"]["northeast"]["lat"],
            "west": geometry["viewport"]["southwest"]["lng"],
            "east": geometry["viewport"]["northeast"]["lng"]
        }
    return {
        "lat": geometry["location"]["lat"],
        "lon": geometry["location"]["lng"]
    }

