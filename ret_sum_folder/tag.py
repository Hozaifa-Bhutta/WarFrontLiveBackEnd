import re
from ret_sum_folder.call_llm import call_llm
from ret_sum_folder.location_validator import search_and_validate

def extract_and_refine_locations(text):
    """
    Step 1: Use a single LLM call to act as a geographic analyst,
    extracting and refining locations into optimal search queries.
    """
    system_prompt = f"""
Extract all location names mentioned in the following text:

\"\"\"{text}\"\"\"

If multiple place names or directional phrases are used together to describe one specific area, combine them into a single location phrase that preserves the original wording and relative positions.

Return only a Python list of these combined location phrases.
"""
    user_prompt = f'Message: "{text}"\nOutput:'

    try:
        result = call_llm(user_prompt, system_prompt, temperature=0.1, max_tokens=100)
        return eval(result)  # Safely parse the response to a list
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