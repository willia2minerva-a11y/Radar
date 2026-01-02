from utils import smart_fetch_and_process, send_to_telegram
from config import API_SOURCES, CHANNELS

def run():
    print("--- بدء تحديث الرياضة ---")
    final_text = smart_fetch_and_process(API_SOURCES["sport"], "sport")
    
    if final_text:
        send_to_telegram(final_text, CHANNELS["sport"])
    else:
        print("لا يوجد محتوى رياضي جديد للنشر.")
