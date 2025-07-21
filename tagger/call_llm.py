import requests
import time
import os
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Get api key from .env file
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# MODEL = "mistralai/mistral-small-3.2-24b-instruct:free"  # example free model
MODEL = "mistral-saba-24b"
tokens_remaining = 6000
tokens_reset = 30

def call_llm(user_prompt, system_prompt, temperature=0.2, max_tokens=1024):
    global tokens_remaining 
    global tokens_reset
    if tokens_remaining < len((user_prompt+system_prompt).split(" "))*1.5:
        print(f"Waiting for {tokens_reset} seconds for llm")
        time.sleep(tokens_reset+1) # wait until all tokens are reset
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    messages = [
        {"role": "system", "content": system_prompt} if system_prompt else {},
        {"role": "user", "content": user_prompt}
    ]
    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
    }

    response = requests.post(url, headers=headers, json=data)
    tokens_remaining = int(response.headers.get('x-ratelimit-remaining-tokens'))
    tokens_reset = float(response.headers.get('x-ratelimit-reset-tokens')[:-1]) 

    # Only parse JSON if status is 200
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        raise Exception("LLM request failed: " + response.text)