import requests
def call_llm(user_prompt, system_prompt="", temperature=0.2, max_tokens=100):
    prompt = ""
    if system_prompt:
        prompt += f"System: {system_prompt.strip()}\n\n"
    # make sure to add that the output should be very specific and no explanation is needed
    prompt += f"User: {user_prompt.strip()}\n\nAssistant:"

    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "openchat",
        "prompt": prompt,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
        "stop": ["User:", "System:", "\n\n"]  # You can tweak this list
    })

    if response.status_code == 200:
        print(f"LLM response: {response.json()['response'].strip()}")
        return response.json()["response"].strip()
    else:
        raise Exception("LLM request failed: " + response.text)
