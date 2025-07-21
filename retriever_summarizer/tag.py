import json
import re
from call_llm import call_llm

def extract_relevant_locations_llm(text):
    """Extract locations directly involved in violent attacks using LLM."""
    system_prompt = """You are a location extraction assistant for a conflict intelligence mapping system. Your job is to identify and extract ONLY the physical locations that are directly involved in violent attacks, military operations, or conflict events mentioned in the message.

Your output must:
- Extract ONLY locations where violent events (attacks, strikes, bombings, fighting, etc.) are taking place
- Provide cleaned-up, geocodable location names that would work with mapping services
- Include specific landmarks, facilities, or districts when mentioned along with cities
- Return locations in a simple comma-separated list format
- Return "NONE" if no relevant locations are found

Important criteria:
- ONLY include locations where violent events are happening
- Include cities, neighborhoods, buildings, landmarks, crossings, facilities directly involved in conflict
- Exclude locations mentioned only in passing or for context
- Exclude political groups, organizations, people, military units
- Format as: "Location1, Location2, Location3" (no quotes, no explanations)

Examples:

Message: "Airstrikes reported in Gaza City targeting residential buildings near Al-Shifa Hospital."
Output: Gaza City, Al-Shifa Hospital

Message: "Heavy fighting continues around the Erez Crossing in northern Gaza."
Output: Erez Crossing

Message: "The AlMuhand Hall in Khan Younis was hit by an airstrike."
Output: AlMuhand Hall Khan Younis

Message: "Hamas announced they will continue resistance operations from Gaza."
Output: NONE

Message: "IDF forces are stationed near the border but no operations reported."
Output: NONE"""
    
    user_prompt = f"""Extract ONLY the physical locations directly involved in violent attacks or conflict events from this message.

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