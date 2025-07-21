import json
from google_bounding import get_bounding
with open("../shared_folder/tagged_messages.json", "r") as f:
    tagged_messages = json.load(f)

with open("../shared_folder/location_cache.json", "r") as f:
    location_cache = json.load(f)

# print(tagged_messages)
# print(location_cache)
for msg in tagged_messages:
    for loc in msg["locations"]:
        if loc not in location_cache:
            location_cache[loc.lower()] = get_bounding(loc)

with open("../shared_folder/location_cache.json", "w") as f:
    json.dump(location_cache, f, indent=4)
    print(f"Updated location cache with {len(location_cache)} locations.")
    print(f"Total locations in cache: {len(location_cache)}")
