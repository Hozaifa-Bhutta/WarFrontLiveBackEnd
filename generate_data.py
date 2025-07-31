from stream_processor import extract
from retriever_summarizer import retriever_summarizer
from update_cache import update_cache
import asyncio


# asyncio.run(extract()) # This will run the Telegram message extraction process
# wait for the stream processor to finish
print("Stream Processor finished. Now running the retriever summarizer...")
retriever_summarizer()
print("Retriever Summarizer finished. Now running the cache updater...")
update_cache()