from call_llm import call_llm
import re

def clean_text(text):
    """Cleans the input text and preserves readable punctuation while removing non-standard symbols."""
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Replace newlines and tabs with spaces
    text = text.replace('\n', ' ').replace('\t', ' ')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove formatting or symbolic punctuation: ** ~~ == [] {} <> etc.
    text = re.sub(r'[\*\~\=\_\[\]\(\)\{\}\<\>\|\\\/@#$%^&+=`]', '', text)

    # Reduce repeated standard punctuation (e.g. "!!" → "!")
    text = re.sub(r'([!?.,])\1{1,}', r'\1', text)

    # Final whitespace cleanup
    text = re.sub(r'\s+', ' ', text).strip()

    return text if text else False


def clean_messages(messages, max_characters=500):
    """Filter messages for relevance and clean retained ones for clustering. Keeps actor, event, location, timing, and purpose."""

    system_prompt = """You are an assistant for a conflict intelligence system. Your job is to rewrite noisy or redundant Telegram messages into clean, fact-based summaries. Focus only on the essential conflict-related information.

Your behavior must follow these rules:
- Never invent details not present in the message
- Do not editorialize or speculate
- Do not include usernames, hashtags, emojis, or channel branding
- Eliminate redundant phrases, repeated actions, and any non-operational content
- Keep the cleaned version in a single clear paragraph

Preserve the following elements when present:
- WHO performed the action (e.g. IDF, Hezbollah, resistance group)
- WHAT happened (e.g. strike, shelling, drone attack)
- WHERE it occurred (city, region, landmark). Do not mention the location unless it is directly relevant to the action. At the same time, do not remove specifiers like "North" or "neighborhood" if they help specify the location.
- WHEN it happened (date, time of day, or “today”/“yesterday” if given)

Note we do not need to include WHY the action was taken or any political context. Focus on the operational facts only.

You are supporting military-grade event tracking. Accuracy, brevity, and clarity are essential."""

    user_prompt = """Rewrite the following Telegram message into a concise, factual summary focusing on essential operational information. Return a single paragraph without usernames, hashtags, emojis, or propaganda. Do not invent any details.

Examples:

---
Original: "BREAKING: Hezbollah claims responsibility for an RPG attack on Israeli tank in southern Lebanon today."
Cleaned: "Hezbollah claimed responsibility for RPG attack on Israeli tank in southern Lebanon today."

---
Original: "@resistance_news: We struck a Zionist vehicle near a neighborhood in Beit Hanoun using an explosive device. #Gaza"
Cleaned: "Resistance forces struck Israeli vehicle near a neighborhood in Beit Hanoun using explosive device."

---
Original: "IDF strikes terror targets in central Gaza to prevent future attacks and protect Israeli civilians from Hamas aggression"
Cleaned: "IDF struck targets in central Gaza."

---
Original: "IDF struck military compounds used by Hezbollah in south Beirut for training terrorists to attack Israeli forces"
Cleaned: "IDF struck Hezbollah military compounds in south Beirut."

---
Original message:
"{MESSAGE_TO_CLEAN}"

Cleaned summary:"""

    cleaned_output = []
    for i, msg in enumerate(messages):
        print(f"retriever_summarizer: Cleaning up message {i+1}/{len(messages)}")
        if msg and msg.get('text'):
            prompt = user_prompt.replace("{MESSAGE_TO_CLEAN}", msg['text'][:max_characters])
            cleaned = call_llm(
                prompt,
                system_prompt=system_prompt,
                temperature=0.2,
                max_tokens=300
            ).strip().strip('"')

            # remove special characters and extra spaces
            cleaned = clean_text(cleaned)

            cleaned_output.append({
                'text': msg['text'],
                'cleaned_text': cleaned,
                'channel': msg['channel'],
                'date': msg['date']
            })
    return cleaned_output
