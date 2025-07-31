import requests
import os
import re
from ret_sum_folder.call_llm import call_llm

Maps_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "your_api_key_here")

# --- Specificity Filter Configuration ---
SPECIFIC_SITE_KEYWORDS = {
    # Specific sites and locations
    'hospital', 'clinic', 'school', 'mosque', 'church', 'university', 'building',
    'tower', 'checkpoint', 'crossing', 'port', 'station', 'camp', 'market',
    'bakery', 'center', 'cafeteria', 'compound', 'base', 'post', "neighborhood", 
    'house', 'home', 'residence', 'apartment', 'farm', 'factory', 'warehouse',
    'ministry', 'embassy', 'courthouse', 'police', 'prison', 'barracks', 'office',
    'street', 'road', 'junction', 'roundabout', 'square', 'bridge', 'airport',
    'facility', 'plant', 'refuge', 'shelter', 'hotel', 'court'

    # small cities and towns
    'khan yunis'
}
OVERLY_BROAD_AREAS = {
    # Countries and regions
    'gaza strip', 'west bank', 'golan heights', 'gaza', 'israel', 'lebanon', 'egypt', 'syria',
    'palestine', 'jordan', 'iraq', 'saudi arabia', 'iran', 'turkey', 'kuwait', 'bahrain',
    'qatar', 'uae', 'united arab emirates', 'oman', 'yemen',

    # Large cities and capitals (broad without specificity)
    'jerusalem', 'tel aviv', 'damascus', 'cairo', 'beirut', 'amman', 'baghdad',
    'tehran', 'riyadh', 'istanbul', 'ankara',

    # Administrative and geographic divisions
    'governorate', 'province', 'district', 'region', 'state', 'city', 'town', 'village',
    'municipality', 'area', 'zone', 'territory', 'nation', 'country', 'settlement',
    'locality', 'prefecture', 'continent', 'urban area', 'rural area', 'metropolitan area',
    'division', 'department', 'county', 'subdistrict', 'canton'
}

# -----------------------------------------

def search_maps(location_name):
    """Searches Google Maps for a given location name."""
    if not location_name:
        return None, None
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": location_name, "key": Maps_API_KEY}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "OK" or not data.get("results"):
            return None, None

        # This geographic filter seems specific to your use case, so I've kept it.
        for result in data["results"]:
            lat = result["geometry"]["location"]["lat"]
            lng = result["geometry"]["location"]["lng"]
            if 11 <= lat <= 38 and 26 <= lng <= 62:
                return result, result["formatted_address"]
        
        # Fallback to the first result if none are in the custom region
        first_result = data["results"][0]
        return first_result, first_result["formatted_address"]

    except requests.exceptions.RequestException as e:
        print(f"Google Maps API network error: {e}")
        return None, None

def validate_match(original_query, google_name, original_message):
    """
    A single, unified LLM call to validate if the Google result is a good match.
    """
    system_prompt = """
        You are a location validation expert for a conflict map. Your job is to determine
        if a Google Maps result accurately represents the specific location from a text.

        RULES:
        1.  **Exact or reasonable variations are GOOD.** This includes common spelling/transliteration differences (e.g., Beirut vs. Bayrut).
        2.  **Specific Site Rule:** If the original query mentions a specific site (hospital, checkpoint, etc.),
            the Google result MUST also refer to that specific site. A match with only the surrounding city is a **BAD** match.
        3.  **Core Location Rule:** A match is **GOOD** if the Google result correctly identifies the most specific place in the query, even if it drops redundant descriptors ('City', 'North') or regional context ('Gaza Strip'). However, a match is **BAD** if it's a completely different level of specificity (e.g., a query for a city that results in the whole country).

        Respond with only "GOOD" or "BAD".

        Examples:
        ---
        - Original message: "The Jabalia City area in the North Gaza Strip was targeted."
        - Original search query: "Jabalia City North Gaza Strip"
        - Google Maps result: "Jabalia"
        Decision: GOOD
        ---
        - Original message: "Shelling hit the Al-Shifa Hospital in Gaza City."
        - Original search query: "Al-Shifa Hospital Gaza"
        - Google Maps result: "Gaza"
        Decision: BAD
        ---
        - Original message: "The incident took place in southern Gaza."
        - Original search query: "southern Gaza"
        - Google Maps result: "Khan Yunis"
        Decision: BAD
        ---
        - Original message: "Reports from Beirut, Lebanon."
        - Original search query: "Beirut, Lebanon"
        - Google Maps result: "Bayrut, Lebanon"
        Decision: GOOD
        ---
        - Original message: "Troops are operating in the Khan Yunis area of the Gaza Strip."
        - Original search query: "Khan Yunis Gaza"
        - Google Maps result: "Khan Yunis"
        Decision: GOOD
        """
    user_prompt = f"""
    - Original message: "{original_message}"
    - Original search query: "{original_query}"
    - Google Maps result: "{google_name}"

    Decision:
    """
    try:
        result = call_llm(user_prompt, system_prompt, temperature=0.1, max_tokens=10)
        print(f"Validation result: {result.strip()}")
        return "GOOD" in result.upper()
    except Exception as e:
        print(f"Error in LLM location validation: {e}")
        return False

def refine_location_query(original_query, original_message, google_result_name):
    """
    Use LLM to suggest a refined, less specific query for better geocoding.
    """
    system_prompt = """You are a geographic query refinement expert. Your job is to take a failed location search and suggest a slightly broader, more geocodable alternative that still represents the same general area.

RULES:
1. Make the query slightly less specific but still geographically relevant
2. Remove overly specific details that might prevent geocoding
3. Keep the core geographic area intact
4. If the original mentions a specific site (hospital, checkpoint, etc.), try removing some of the words and describe the next most specific area that is likely to be found by Google Maps
5. For neighborhoods or districts, try the parent city

Examples:
- "Netzarim corridor Shuja'iyya Daraj Tuffah Beit Hanoun Gaza Strip" → "Beit Hanoun"
- "Haidar Abdel Shafi Roundabout, Gaza City" → "Gaza City"
- "East of Khan Younis, near the agricultural school" → "Khan Younis"


Return only the refined query string, nothing else."""

    user_prompt = f"""
Original failed query: "{original_query}"
Google found: "{google_result_name}"
Original message context: "{original_message}"

Suggest a refined query:"""

    try:
        refined = call_llm(user_prompt, system_prompt, temperature=0.2, max_tokens=30)
        if refined:
            return refined.strip().strip('"').strip("'")
        return None
    except Exception as e:
        print(f"Error in location refinement: {e}")
        return None

def is_too_vague(original_query, validated_location):
    """
    Check if the validated location is too vague compared to the original query using keyword filters.
    """
    original_lower = original_query.lower()
    validated_lower = validated_location.lower()
    
    # Check if original query mentions a specific site
    has_specific_site = any(keyword in original_lower for keyword in SPECIFIC_SITE_KEYWORDS)
    
    # Check if validated result is overly broad
    is_overly_broad = any(broad_area in validated_lower for broad_area in OVERLY_BROAD_AREAS)
    
    # If original had specific site but result is overly broad, it's too vague
    if has_specific_site and is_overly_broad:
        return True
    
    return False

def search_and_validate(query, original_message):
    """
    Handles the primary search attempt, fallback, and filtering logic.
    """
    # --- Primary Attempt (Step 2) ---
    google_result, google_name = search_maps(query)
    print(f"Searching for: {query} → Google result: {google_name}")
    if google_result and validate_match(query, google_name, original_message):
        return google_name
    print("Not validated in primary search, trying fallback...")

    # --- LLM Fallback Attempt (Step 3) ---
    refined_query = refine_location_query(query, original_message, google_name or "No result")
    if refined_query and refined_query.lower() != query.lower():
        refined_result, refined_name = search_maps(refined_query)
        print(f"Searching for refined query: {refined_query} → Google result: {refined_name}")
        if refined_result and validate_match(refined_query, refined_name, original_message):
            if not is_too_vague(query, refined_name):
                return refined_name
            else:
                print(f"✗ Refined result '{refined_name}' is too vague")

    # --- Programmatic Fallback Attempt (Step 4) ---
    query_parts = query.split()
    if len(query_parts) > 1:
        for i in range(1, len(query_parts)):
            fallback_query = " ".join(query_parts[i:])
            print(f"Trying fallback: '{fallback_query}'")
            fallback_result, fallback_name = search_maps(fallback_query)
            print(f"Fallback search result: {fallback_name}")
            if fallback_result and validate_match(fallback_query, fallback_name, original_message):
                if not is_too_vague(query, fallback_name):
                    return fallback_name
                else:
                    print(f"✗ Fallback result '{fallback_name}' is too vague")
                    break
            
    # If all attempts fail
    print(f"✗ Could not validate location for query: '{query}'")
    return None

def search_location_with_validation(query_name, original_message):
    """
    Main entry point for location validation. 
    Uses the search_and_validate function to find and validate locations.
    """
    return search_and_validate(query_name, original_message)