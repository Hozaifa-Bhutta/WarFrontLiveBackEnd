import re
from ret_sum_folder.call_llm import call_llm
from ret_sum_folder.location_validator import search_and_validate

def extract_and_refine_locations(text):
    """
    Step 1: Use a single LLM call to act as a geographic analyst,
    extracting and refining locations into optimal search queries.
    """
    system_prompt = """
    You are an expert geographic analyst for a conflict intelligence system.
    Your task is to read a text and identify all distinct locations of violent events.
    For each distinct event location, generate one single, optimal search query for Google Maps.

    RULES:
    1.  Combine all related geographic terms for a single event (site, neighborhood, city, etc.) into one query.
    2.  Use your own world knowledge to correct or complete location names for better searchability.
    3.  If multiple distinct event locations are mentioned, list each search query and seperate by semicolon (;).

    Example 1:
    Message: “Wounded by shelling of the vicinity of Al-Asdekaa Cafeteria in Mawasi, Khan Yunis, southern Gaza Strip.”
    Output:
    Al-Asdekaa Cafeteria Al-Mawasi Khan Yunis

    Example 2:
    Message: “...at the Zikim checkpoint, north of the Gaza Strip."
    Output:
    Zikim checkpoint Israel

    Example 3:
    Message: "IDF struck sites in Jabaliya and later in Khan Yunis."
    Output:
    Jabaliya; Khan Yunis

    Example 4:
    Message: “Clashes erupted in the Tal al-Hawa neighborhood of Gaza City, while simultaneous strikes were reported near Rafah and east of Beit Hanoun.”
    Output:
    Tal al-Hawa Gaza City; Rafah Gaza; Beit Hanoun Gaza
    """
    user_prompt = f'Message: "{text}"\nOutput:'

    try:
        result = call_llm(user_prompt, system_prompt, temperature=0.1, max_tokens=100)
        print(f"Extracted locations: {result.strip()}")
        if result.upper().strip() == "NONE":
            return []
        # Split by semicolon and clean up whitespace
        return [loc.strip() for loc in result.strip().split(';') if loc.strip()]
    except Exception as e:
        print(f"Error in LLM location extraction/refinement: {e}")
        return []

def extract_direction(text, location_name):
    """
    Searches the text for directional words immediately preceding a validated location name.
    """
    directional_words = {
        'north', 'northern', 'south', 'southern', 'east', 'eastern',
        'west', 'western', 'central', 'northeast', 'northwest',
        'southeast', 'southwest', 'upper', 'lower'
    }
    
    text_lower = text.lower()
    # Check for any part of the validated location name
    location_parts = [part for part in location_name.split() if len(part) > 2]

    for part in location_parts:
        try:
            # Find all occurrences of the location part in the text
            indices = [m.start() for m in re.finditer(r'\b' + re.escape(part.lower()) + r'\b', text_lower)]
            if not indices:
                continue

            # Check context around the first occurrence for a directional word
            loc_index = indices[0]
            context_before = text_lower[max(0, loc_index - 30):loc_index]

            for direction in directional_words:
                if re.search(r'\b' + direction + r'\b', context_before):
                    # Return the direction capitalized and with a space
                    return direction.capitalize() + " "
        except Exception:
            continue # Ignore regex errors on complex/unusual location parts
            
    return ""

def extract_locations(text):
    """
    The main orchestration function. Extracts, validates, and finalizes locations from text.
    """
    # Step 1: Extract and refine queries in one shot
    search_queries = extract_and_refine_locations(text)
    print(f"Extracted {search_queries} from text: {text[:50]}...")
    if not search_queries:
        return []

    final_locations = []
    for query in search_queries:
        # Step 2 & 3: Search, validate, and fallback are handled by the validator module
        validated_name = search_and_validate(query, text)
        print(f"Validated location: {validated_name} for query: {query}")

        if validated_name:
            # Last step: Prepend direction if found
            direction = extract_direction(text, validated_name)
            final_locations.append(direction + validated_name)
            print(f"✓ Found location: {direction}{validated_name}")

    return list(set(final_locations))