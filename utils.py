import requests
import google.generativeai as genai
import time
from config import GEMINI_API_KEY, IDENTITIES, BOT_TOKEN

# إعداد Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def get_readable_content(data):
    """
    دالة ذكية تحاول استخراج النص المفيد من أشكال JSON المختلفة
    """
    content = ""
    # التعامل مع NewsAPI
    if "articles" in data and len(data["articles"]) > 0:
        item = data["articles"][0] # نأخذ أحدث خبر
        content = f"العنوان: {item.get('title')}\nالوصف: {item.get('description')}"
    
    # التعامل مع TheSportsDB
    elif "events" in data and data["events"]:
        item = data["events"][0]
        content = f"مباراة: {item.get('strEvent')}\nالوقت: {item.get('strTime')}"
        
    return content

def smart_fetch_and_process(api_list, channel_type):
    """
    1. تجرب الروابط بالترتيب
    2. تستخرج النص
    3. ترسله لجميني
    """
    raw_text = None
    
    # 1. جلب البيانات (Failover System)
    for url in api_list:
        try:
            print(f"[{channel_type}] جاري الاتصال بـ: {url}...")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                raw_text = get_readable_content(data)
                if raw_text:
                    break # وجدنا بيانات، نوقف البحث
        except Exception as e:
            print(f"خطأ في الرابط: {e}")
            continue

    if not raw_text:
        print(f"[{channel_type}] فشلت كل المصادر في جلب بيانات.")
        return None

    # 2. المعالجة بـ Gemini
    try:
        print(f"[{channel_type}] جاري المعالجة بالذكاء الاصطناعي...")
        identity = IDENTITIES.get(channel_type, IDENTITIES["mix"])
        prompt = f"{identity}\n\nالبيانات الخام:\n{raw_text}"
        
        ai_response = model.generate_content(prompt)
        return ai_response.text
    except Exception as e:
        print(f"خطأ في Gemini: {e}")
        return None

def send_to_telegram(text, channel_id):
    if not text or not channel_id:
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": channel_id,
        "text": text,
        "parse_mode": "Markdown" # أو HTML
    }
    try:
        requests.post(url, data=payload)
        print(f"✅ تم النشر في {channel_id}")
    except Exception as e:
        print(f"❌ فشل النشر: {e}")
