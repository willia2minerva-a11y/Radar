import requests
import google.generativeai as genai
import os
import time
import random
import re
from io import BytesIO
from PIL import Image
# لاحظ: حذفنا FOOTBALL_KEY من هنا لإصلاح الخطأ
from config import IDENTITIES, BOT_TOKEN

# --- قائمة الموديلات الآمنة (مستوحاة من ملفك) ---
SAFE_MODELS = [
    "models/gemini-1.5-flash",      # الأسرع والأرخص
    "models/gemini-1.5-flash-8b",   # نسخة خفيفة
    "models/gemini-1.5-pro",        # الأذكى
    "models/gemini-pro"             # الاحتياطي القديم
]

# --- مصادر الصور (مقتبسة من ملف bot (1).py) ---
IMAGE_SOURCES = [
    {"url": "https://source.unsplash.com/featured/1080x1080/?{query}", "name": "Unsplash"},
    {"url": "https://picsum.photos/1080/1080?random={rand}", "name": "Picsum"},
    {"url": "https://loremflickr.com/1080/1080/{query}", "name": "LoremFlickr"}
]

def get_keys_list(env_var_name):
    """جلب المفاتيح وتنظيفها"""
    keys_str = os.getenv(env_var_name)
    if not keys_str: return []
    return [k.strip() for k in keys_str.split(',') if k.strip()]

def validate_markdown(text):
    """تصحيح تنسيق المارك داون لتجنب أخطاء تليجرام"""
    # إغلاق النجوم والأقواس المفتوحة
    if text.count('*') % 2 != 0: text += '*'
    if text.count('_') % 2 != 0: text += '_'
    return text

def generate_image(query):
    """جلب صورة مجانية بناءً على موضوع الخبر"""
    print(f"🖼️ جاري البحث عن صورة لموضوع: {query}...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for source in IMAGE_SOURCES:
        try:
            url = source["url"].format(query=query, rand=random.randint(1, 1000))
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                # التحقق من سلامة الصورة
                img = Image.open(BytesIO(response.content))
                img.verify()
                
                # إعادة المؤشر للبداية للقراءة
                img_io = BytesIO(response.content)
                img_io.name = 'image.jpg'
                return img_io
        except Exception as e:
            print(f"⚠️ فشل المصدر {source['name']}: {e}")
            continue
    return None

def call_gemini_with_failover(prompt):
    """تجربة المفاتيح والموديلات بالتتابع"""
    gemini_keys = get_keys_list("GEMINI_API_KEY")
    if not gemini_keys: return None

    for i, key in enumerate(gemini_keys):
        # نجرب الموديلات المتاحة لكل مفتاح
        for model_name in SAFE_MODELS:
            try:
                print(f"🤖 محاولة Gemini (المفتاح {i+1} | الموديل {model_name})...")
                genai.configure(api_key=key)
                model = genai.GenerativeModel(model_name)
                
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
                    
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg:
                    print(f"⚠️ الموديل {model_name} غير مدعوم، ننتقل للتالي.")
                    continue # تجربة الموديل التالي لنفس المفتاح
                elif "429" in error_msg:
                    print(f"⏳ المفتاح {i+1} مشغول (Rate Limit).")
                    break # الانتقال للمفتاح التالي فوراً
                else:
                    print(f"❌ خطأ: {e}")
                    time.sleep(1)
    
    return None

def smart_fetch_and_process(api_list, channel_type):
    """المحرك الرئيسي: جلب -> تحليل -> صور -> إرسال"""
    raw_text = None
    news_keys = get_keys_list("NEWS_API_KEY")
    football_keys = get_keys_list("FOOTBALL_DATA_KEY")

    # 1. جلب البيانات (نفس المنطق السابق)
    for url_template in api_list:
        current_keys = football_keys if "football-data.org" in url_template else news_keys
        is_football = "football-data.org" in url_template
        
        if not current_keys: continue

        for key in current_keys:
            try:
                final_url = url_template if is_football else url_template.replace("{KEY}", key)
                headers = {'X-Auth-Token': key} if is_football else {}
                
                response = requests.get(final_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    # استخراج المحتوى
                    if is_football:
                         if "matches" in data and data["matches"]:
                             matches = data["matches"][:10]
                             match_lines = [f"{m['homeTeam']['name']} vs {m['awayTeam']['name']} ({m['utcDate']})" for m in matches]
                             raw_text = "Maches:\n" + "\n".join(match_lines)
                             break
                    elif "articles" in data and data["articles"]:
                         art = data["articles"][0]
                         raw_text = f"Title: {art['title']}\nDesc: {art['description']}"
                         break
            except: continue
        if raw_text: break

    if not raw_text:
        print(f"🚫 {channel_type}: لا يوجد محتوى.")
        return

    # 2. المعالجة بـ Gemini
    identity = IDENTITIES.get(channel_type, "")
    full_prompt = f"{identity}\n\nالبيانات:\n{raw_text}\n\nاجعل النص جاهزاً للنشر فوراً."
    final_text = call_gemini_with_failover(full_prompt)
    
    if not final_text: return

    # 3. جلب صورة (ميزة جديدة)
    # نستخرج كلمة مفتاحية بسيطة للصورة بناءً على نوع القناة
    image_query = "stadium" if channel_type == "sport" else "technology" if channel_type == "tech" else "bitcoin"
    image_file = generate_image(image_query)

    # 4. الإرسال
    send_to_telegram(final_text, os.getenv(f"{channel_type.upper()}_CHANNEL_ID") or IDENTITIES[channel_type], image_file)

def send_to_telegram(text, channel_id, image_file=None):
    if not text or not channel_id: return
    
    # تنظيف النص
    text = validate_markdown(text)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/"
    
    try:
        if image_file:
            print(f"📸 إرسال مع صورة إلى {channel_id}...")
            files = {'photo': image_file}
            data = {'chat_id': channel_id, 'caption': text, 'parse_mode': 'Markdown'}
            requests.post(url + "sendPhoto", data=data, files=files)
        else:
            print(f"📝 إرسال نص فقط إلى {channel_id}...")
            data = {'chat_id': channel_id, 'text': text, 'parse_mode': 'Markdown'}
            requests.post(url + "sendMessage", data=data)
            
        print("✅ تم النشر بنجاح!")
    except Exception as e:
        print(f"❌ فشل الإرسال: {e}")
