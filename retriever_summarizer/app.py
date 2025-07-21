# retriever_summarizer/app.py
import json
import time
from datetime import datetime, timezone
from call_llm import call_llm
from remove_irrelevant_messages import remove_irrelevant_messages
from clean import clean_messages, clean_text
from tag import extract_locations



while True:
    # with open('../shared_folder/extracted_messages.json', 'r') as f:
    #     messages = json.load(f)

    # # only take care of messaages that have not been tagged yet
    # # get existing tagged messages
    # with open('../shared_folder/tagged_messages.json', 'r') as f:
    #     existing_tagged_messages = json.load(f)
    # # Filter out messages that have already been tagged
    # for exisitng_msg in existing_tagged_messages:
    #     for msg in messages:
    #         if (exisitng_msg['text'] == msg['text'] and
    #             exisitng_msg['channel'] == msg['channel']):
    #             messages.remove(msg)
    #             break


    # filtered_messages = remove_irrelevant_messages(messages)
    # # save as checkpoint
    # with open('filtered_messages.json', 'w') as f:
    #     json.dump(filtered_messages, f, indent=4)
    # # todo: remove filtered messages from "../shared_folder/extracted_messages.json"

    # cleaned_messages = clean_messages(filtered_messages)  
    # # save as checkpoint
    # with open('cleaned_messages.json', 'w') as f:
    #     json.dump(cleaned_messages, f, indent=4)


    with open("cleaned_messages.json", "r") as f:
        cleaned_messages = json.load(f)

    tagged_messages = []
    for message in cleaned_messages[:]:
        # message["locations"] = extract_locations(message["cleaned_text"])
        locations = extract_locations(message["cleaned_text"])
        for i in range(len(locations)):
            # titular capitalize the location
            locations[i] = locations[i].title()
            locations[i] = clean_text(locations[i])
        tagged_messages.append({
            'text': message['text'],
            'cleaned_text': message['cleaned_text'],
            'channel': message['channel'],
            'date': message['date'],
            'locations': locations
        })

    print(f"retriever_summarizer: Number of messages with locations tagged: {len(tagged_messages)}")
    # # Combine existing tagged messages with new ones
    # for msg in tagged_messages:
    #     if not any(existing_msg['text'] == msg['text'] and existing_msg['channel'] == msg['channel'] for existing_msg in existing_tagged_messages):
    #         existing_tagged_messages.append(msg)

    with open('../shared_folder/tagged_messages.json', 'w') as f:
        json.dump(tagged_messages, f, indent=4)
    # print(f"retriever_summarizer: Processed {len(tagged_messages)} messages. Total tagged messages stored: {len(existing_tagged_messages)} at time {datetime.now()}", flush=True)
    time.sleep(3600)  # Sleep for 1 hour before next run