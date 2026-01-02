from utils import smart_fetch_and_process, send_to_telegram
from config import API_SOURCES, CHANNELS

def run():
    print("--- بدء تحديث المنوعات ---")
    final_text = smart_fetch_and_process(API_SOURCES["mix"], "mix")
    
    if final_text:
        send_to_telegram(final_text, CHANNELS["mix"])
