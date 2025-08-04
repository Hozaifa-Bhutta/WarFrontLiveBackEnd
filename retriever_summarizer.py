# retriever_summarizer/app.py
import json
import time
from datetime import datetime, timezone
from ret_sum_folder.remove_irrelevant_messages import remove_irrelevant_messages
from ret_sum_folder.clean import clean_messages
from ret_sum_folder.tag import extract_locations



def retriever_summarizer():
    """main function to run the retriever and summarizer"""
    with open('shared_folder/extracted_messages.json', 'r') as f:
        messages = json.load(f)

    # only take care of messaages that have not been tagged yet
    # get existing tagged messages
    try:
        with open('shared_folder/tagged_messages.json', 'r') as f:
            existing_tagged_messages = json.load(f)
    except:
        existing_tagged_messages = []
    # Filter out messages that have already been tagged
    for exisitng_msg in existing_tagged_messages:
        for msg in messages:
            if (exisitng_msg['text'] == msg['text'] and
                exisitng_msg['channel'] == msg['channel']):
                messages.remove(msg)
                break


    filtered_messages = remove_irrelevant_messages(messages)
    # save as checkpoint
    with open('shared_folder/filtered_messages.json', 'w') as f:
        json.dump(filtered_messages, f, indent=4)
    # todo: remove filtered messages from "../shared_folder/extracted_messages.json"

    cleaned_messages = clean_messages(filtered_messages)  
    # save as checkpoint
    with open('shared_folder/cleaned_messages.json', 'w') as f:
        json.dump(cleaned_messages, f, indent=4)


    # with open("shared_folder/cleaned_messages.json", "r") as f:
    #     cleaned_messages = json.load(f)

    # tagged_messages = []
    # for message in cleaned_messages[:]:
    #     # Extract and validate locations
    #     validated_locations = extract_locations(message["cleaned_text"])
        
    #     tagged_messages.append({
    #         'text': message['text'],
    #         'cleaned_text': message['cleaned_text'],
    #         'channel': message['channel'],
    #         'date': message['date'],
    #         'locations': validated_locations  # Now just a list of location names
    #     })

    # print(f"retriever_summarizer: Number of messages with locations tagged: {len(tagged_messages)}")
    # Combine existing tagged messages with new ones
    # for msg in tagged_messages:
    #     if not any(existing_msg['text'] == msg['text'] and existing_msg['channel'] == msg['channel'] for existing_msg in existing_tagged_messages):
    #         existing_tagged_messages.append(msg)
    # uncomment code above to remove duplicates
    # existing_tagged_messages = tagged_messages # remove duplicates later
    # with open('shared_folder/tagged_messages.json', 'w') as f:
    #     json.dump(existing_tagged_messages, f, indent=4)
    # print(f"retriever_summarizer: Processed {len(tagged_messages)} messages. Total tagged messages stored: {len(existing_tagged_messages)} at time {datetime.now()}", flush=True)
