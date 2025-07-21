import asyncio
from telethon import TelegramClient
from datetime import datetime, timezone
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from deep_translator import GoogleTranslator
import json
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

# Telegram API credentials
api_id = 21381904
api_hash = "62922f5fe934d21fc4a0730c87327b1e"

# Load model once globally
model = SentenceTransformer('all-MiniLM-L6-v2')


import re

def clean_text(text):
    """Cleans the input text and translates it to English if necessary, preserving standard punctuation only."""
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Replace newlines and tabs with spaces
    text = text.replace('\n', ' ').replace('\t', ' ')

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Check if text is non-English (basic heuristic)
    if not text.isascii() or any(ord(char) > 127 for char in text if char.isalpha()):
        return False

    # Remove "unnecessary" punctuation (like **, ==, ~~, etc.)
    text = re.sub(r'[\*\~\=\_\[\]\(\)\{\}\<\>\|\\\/@#$%^&*+=`]', '', text)

    # Compress repeated punctuation (e.g. "!!" → "!")
    text = re.sub(r'([!?.,])\1{1,}', r'\1', text)

    # Final spacing cleanup
    text = re.sub(r'\s+', ' ', text).strip()

    return text if len(text) > 5 else False


async def fetch_messages(client):
    channels = ["gazaalanpa", "abuobaidahenglish", "idfofficial", "PalestineResist", "the_jerusalem_post", "Alaqsa_voice"]
    messages = []

    for channel in channels:
        print(f'Stream Processor: Fetching messages from {channel}...')
        async for message in client.iter_messages(channel, limit=20):
            current_time = datetime.now(timezone.utc)
            if message.date and (current_time - message.date).total_seconds() < 86400 and message.text:
                cleaned_text = clean_text(message.text)
                if cleaned_text:
                    messages.append({
                        'channel': channel,
                        'date': message.date,
                        'text': cleaned_text
                    })
    return messages


async def loop_forever():
    client = TelegramClient("session_name", api_id, api_hash)
    await client.start()
    print("Stream Processor: Telegram Client started successfully", flush=True)
    try:
        while True:
            messages = await fetch_messages(client)

            # Read existing messages
            try:
                with open("messages.json", "r") as f:
                    messages_json = json.load(f)
            except FileNotFoundError:
                messages_json = []

            # Track seen messages to avoid duplicates
            message_ids = {}
            for msg in messages_json:
                text_key = msg.get("text", "")[:100]
                key = f"{msg['channel']}_{msg['date']}_{hash(text_key)}"
                message_ids[key] = msg

            # Add new messages
            for msg in messages:
                msg_date_str = msg["date"].isoformat()
                text_key = msg["text"][:100]
                key = f"{msg['channel']}_{msg_date_str}_{hash(text_key)}"

                if key not in message_ids:
                    json_msg = {
                        'channel': msg['channel'],
                        'date': msg_date_str,
                        'text': msg['text']
                    }
                    message_ids[key] = json_msg

            # Deduplicated list
            updated_messages = list(message_ids.values())

            # Write updated messages
            with open("messages.json", "w") as f:
                json.dump(updated_messages, f, indent=4)
            with open("../shared_folder/extracted_messages.json", "w") as f:
                json.dump(updated_messages, f, indent=4)

            print(f"Stream Processor: Extracted {len(messages)} messages. Total stored: {len(updated_messages)} at {datetime.now()}", flush=True)

            await asyncio.sleep(3600)  # Wait for 1 hour
    except KeyboardInterrupt:
        print("Stream Processor: Stopping the client...")
        await client.disconnect()


# Start once
if __name__ == "__main__":
    asyncio.run(loop_forever())
