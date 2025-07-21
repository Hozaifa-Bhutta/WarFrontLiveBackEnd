

from call_llm import call_llm

def remove_irrelevant_messages(messages):
    """ Remove messages that are not relevant for clustering using LLM. """
    system_prompt = """You are a highly accurate message filter for a conflict monitoring system. Your task is to identify and retain only messages that include:
1. A **specific geographic location** (e.g., city, town, region, known landmark), and
2. A **significant conflict-related event**, such as:
   - Missile or air strikes
   - Bombings or explosions
   - Artillery shelling
   - Ground assaults or offensives
   - Military aircraft sightings (planes, drones, helicopters)
   - Reports of casualties or major damage
   - Major troop movements or engagements

You must **discard** any messages that:
- Lack a clear geographic location
- Do not describe a drastic or violent event
- Are general news or vague political commentary/propaganda

Your response must be **only one word**, either:
- **RETAIN** – if both a specific location and a significant event are present
- **DISCARD** – if either is missing
"""
    user_prompt = """Evaluate the following Telegram message. Decide whether it should be **RETAINED** (clear location + drastic event) or **DISCARDED** (missing one or both criteria). See the examples below:

---
Message: "Explosion heard in the center of Kyiv. Emergency services on their way."
Decision: RETAIN

---
Message: "Multiple missile launches detected towards Lviv this morning. Air defense systems active."
Decision: RETAIN

---
Message: "President's latest speech on the conflict emphasized unity."
Decision: DISCARD

---
Message: "The local market in Mariupol was heavily shelled, significant damage reported."
Decision: RETAIN

---
Now evaluate the following message:

Message: "{MESSAGE_TO_EVALUATE}"
Decision:"""

    cleaned_messages_for_llm = []
    for i, msg in enumerate(messages):
        print(f"Determing relevancy of message {i+1}/{len(messages)}")
        if msg and msg.get('text') and len(msg['text']) > 10:
            user_prompt_eval = user_prompt.replace("{MESSAGE_TO_EVALUATE}", msg['text'])
            decision = call_llm(user_prompt_eval, system_prompt=system_prompt, temperature=0.0, max_tokens=5).lower().strip()
            if "retain" in decision and "discard" not in decision:
                final_decision = "retain"
            elif "discard" in decision and "retain" not in decision:
                final_decision = "discard"
            else:
                final_decision = "garbage"

            if final_decision == "retain":
                cleaned_messages_for_llm.append({
                    'text': msg['text'],
                    'channel': msg['channel'],
                    'date': msg['date']
                })
            elif final_decision == "discard":
                print(f"retriever_summarizer: Discarded message: {msg['text'][:100]} - Decision: {decision}")
            else:
                print(f"retriever_summarizer: Unexpected decision for message: {msg['text'][:100]} - Decision: {decision}")
    return cleaned_messages_for_llm
