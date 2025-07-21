import json
import re

from call_llm import call_llm

def extract_relevant_locations_llm(text):
    """Extract locations directly involved in violent attacks using LLM."""
    system_prompt = """You are a location‑extraction assistant for a conflict‑intelligence mapping system.
Your job is to return one combined, geocodable location for each distinct violent event described, using exactly the place names as they appear in the text. If the message describes multiple events in different places, return each combined location separated by commas.

Output format:
  Location1, Location2, …

Where each Location is formatted by concatenating, in order and separated by spaces, only those components that appear in the message:
  [Site_or_Landmark] [Neighborhood_or_City] [Region_or_City_or_Country]

Rules:
1. Include **only** the place names explicitly mentioned in the text—and only those.  
2. If the text names a region or city alongside a specific site, include it.  
   - E.g. “Zikim checkpoint, north of the Gaza Strip” → `Zikim checkpoint Gaza Strip`  
3. If multiple distinct events occur at different mentioned locations, separate them with commas.  
4. Do **not** invent or infer additional places beyond what’s named.  

Examples:

Message:  
  “Wounded by shelling of the vicinity of Al‑Asdekaa Cafeteria in Mawasi, Khan Yunis, southern Gaza Strip.”  
Output:  
  Al‑Asdekaa Cafeteria Mawasi Khan Yunis southern Gaza Strip

Message:  
  “Breaking: an Israeli bulldozer is running over bodies at the Zikim checkpoint, north of the Gaza Strip.”  
Output:  
  Zikim checkpoint Gaza Strip

Message:  
  “IDF struck sites in Jabaliya and later in Khan Yunis.”  
Output:  
  Jabaliya, Khan Yunis

Message:  
  “Violent Zionist bombing of the Gaza Strip now.”  
Output:  
  Gaza Strip
"""
    user_prompt = f"""For each violent event in this message, extract one combined location string by concatenating only the place names that appear verbatim in the text (site, neighborhood/city, region/country) with spaces between them.  
There may be more than one event: return multiple combined locations separated by commas.  
Each location must be specific enough to be found by the Google Maps API—so if a named site is too granular, only include it when paired with its named city, region, or country.

Message: "{text}"
Output:"""




    print(f"Extracting relevant locations from: '{text[:100]}...'")
    try:
        result = call_llm(user_prompt, system_prompt, temperature=0.1, max_tokens=50)
        result = result.strip().split('\n')[0].strip()
        print(f"LLM extraction result: '{result}'")
        
        if result.upper() == "NONE" or not result:
            return []
        
        # Parse comma-separated locations
        locations = [loc.strip() for loc in result.split(',') if loc.strip()]
        return locations
    except Exception as e:
        print(f"Error in LLM location extraction: {e}")
        return []

def extract_locations(text):
    """ Extract locations directly involved in violent attacks using LLM.
    Returns a list of specific, geocodable location names with directional qualifiers."""
    
    # Use LLM to directly extract relevant locations involved in violent attacks
    locations_extracted = extract_relevant_locations_llm(text)
    
    if not locations_extracted:
        return []
    
    # Apply directional qualifier normalization
    locations_with_qualifiers = normalize_directional_qualifiers(locations_extracted, text)
    
    return locations_with_qualifiers





def normalize(text):
    return ' '.join(text.lower().split())

def normalize_directional_qualifiers(locations, text):
    """
    Normalize location names to include directional qualifiers when present nearby.
    Prefers "northern Gaza", "central Gaza Strip", etc. over just "Gaza Strip"
    """
    directional_words = {
        'north', 'northern', 'south', 'southern', 'east', 'eastern', 
        'west', 'western', 'central', 'northeast', 'northwest', 
        'southeast', 'southwest', 'upper', 'lower'
    }
    
    normalized = []
    text_lower = text.lower()
    

    
    for location in locations:
        # Find the location in the original text to get context
        loc_lower = location.lower()
        
        # Find ALL occurrences of this location in the text
        all_indices = []
        start_pos = 0
        while True:
            idx = text_lower.find(loc_lower, start_pos)
            if idx == -1:
                break
            # Check if this is a complete word match (not part of another word)
            if (idx == 0 or not text_lower[idx-1].isalnum()) and \
               (idx + len(loc_lower) == len(text_lower) or not text_lower[idx + len(loc_lower)].isalnum()):
                all_indices.append(idx)
            start_pos = idx + 1
        
        
        if not all_indices:
            normalized.append(location)
            continue
        
        # Check each occurrence for directional qualifiers
        best_match = None
        best_direction = None
        
        for loc_index in all_indices:
            
            # Look for directional words before the location (within 30 characters for better coverage)
            start_search = max(0, loc_index - 30)
            before_text = text_lower[start_search:loc_index]
            
            
            # Also check the actual extracted span in case directional word was included
            full_span_start = max(0, loc_index - 15)
            full_span_end = min(len(text), loc_index + len(location) + 15)
            full_context = text_lower[full_span_start:full_span_end]
            
            
            # Find directional qualifier for this occurrence
            found_direction = None
            
            # First, check if directional word is already in the location itself
            for direction in directional_words:
                if direction in loc_lower:
                    found_direction = direction
                    break
            
            if not found_direction:
                # Look for directional words in the text before the location
                for direction in directional_words:
                    # Check in before_text (words preceding the location)
                    if direction in before_text:
                        words_before = before_text.split()
                        if words_before and direction in words_before[-5:]:  # Within last 5 words
                            found_direction = direction
                            break
                    
                    # Also check in full context for patterns like "southern Syria"
                    direction_pattern = r'\b' + re.escape(direction) + r'\s+' + re.escape(loc_lower) + r'\b'
                    if re.search(direction_pattern, full_context):
                        found_direction = direction
                        break
            
            # If we found a directional qualifier, prefer this occurrence
            if found_direction:
                best_match = loc_index
                best_direction = found_direction
                break  # Use first occurrence with directional qualifier
        
        
        if best_direction and best_direction not in loc_lower:
            # Add directional qualifier if not already present
            result = f"{best_direction} {location}"
            normalized.append(result)
        else:
            normalized.append(location)
    
    return normalized