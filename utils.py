import requests
import google.generativeai as genai
import os
import time
# التصحيح هنا: حذفنا FOOTBALL_KEY من هذا السطر
from config import IDENTITIES, BOT_TOKEN

def get_keys_list(env_var_name):
    """جلب قائمة المفاتيح من متغيرات البيئة مفصولة بفواصل"""
    keys_str = os.getenv(env_var_name)
    if not keys_str:
        print(f"⚠️ تحذير: لم يتم العثور على مفاتيح في {env_var_name}")
        return []
    return [k.strip() for k in keys_str.split(',') if k.strip()]

def get_readable_content(data):
    """استخراج النص من البيانات JSON"""
    if "matches" in data:
        matches = data["matches"]
        if not matches: return "NO_MATCHES"
        match_list = []
        for match in matches[:10]:
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            time_utc = match['utcDate']
            league = match['competition']['name']
            match_list.append(f"League: {league} | {home} vs {away} | Time: {time_utc}")
        return "Match Schedule (UTC):\n" + "\n".join(match_list)
    
    elif "articles" in data and len(data["articles"]) > 0:
        item = data["articles"][0]
        return f"Title: {item.get('title')}\nDesc: {item.get('description')}"
    
    return None

def call_gemini_with_failover(prompt):
    """دالة خاصة لتجربة مفاتيح Gemini واحداً تلو الآخر"""
    gemini_keys = get_keys_list("GEMINI_API_KEY")
    
    if not gemini_keys:
        print("❌ لا توجد مفاتيح Gemini متاحة!")
        return None

    for i, key in enumerate(gemini_keys):
        try:
            print(f"🤖 محاولة معالجة Gemini بالمفتاح رقم {i+1}...")
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                print(f"⚠️ مفتاح Gemini رقم {i+1} انتهى رصيده. الانتقال للتالي...")
            elif "API_KEY_INVALID" in error_msg:
                print(f"⚠️ مفتاح Gemini رقم {i+1} غير صالح.")
            else:
                print(f"❌ خطأ غير متوقع في Gemini مع المفتاح {i+1}: {e}")
            time.sleep(1)
            continue
    
    print("🚫 فشلت جميع مفاتيح Gemini في المعالجة.")
    return None

def smart_fetch_and_process(api_list, channel_type):
    """المحرك الرئيسي"""
    raw_text = None
    
    # جلب المفاتيح من البيئة مباشرة هنا
    news_keys = get_keys_list("NEWS_API_KEY")
    football_keys = get_keys_list("FOOTBALL_DATA_KEY") # التأكد من الاسم الصحيح في Secrets

    for url_template in api_list:
        if "football-data.org" in url_template:
            current_keys = football_keys
            is_football = True
        else:
            current_keys = news_keys
            is_football = False
            
        if not current_keys: continue

        for i, key in enumerate(current_keys):
            try:
                final_url = url_template
                headers = {}
                if is_football:
                    headers = {'X-Auth-Token': key}
                else:
                    final_url = url_template.replace("{KEY}", key)

                response = requests.get(final_url, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    extracted = get_readable_content(data)
                    if extracted == "NO_MATCHES": break 
                    if extracted:
                        raw_text = extracted
                        break 
                elif response.status_code in [401, 403, 429]:
                    print(f"⚠️ خطأ المصدر ({response.status_code}) بالمفتاح {i+1}. تجربة التالي...")
                    continue
            except Exception:
                continue
        
        if raw_text: break

    if not raw_text:
        print(f"🚫 [{channel_type}] لم يتم العثور على محتوى.")
        return None

    # المعالجة
    identity = IDENTITIES.get(channel_type, "")
    extra_prompt = ""
    if "Match Schedule" in raw_text:
        extra_prompt = "\nملاحظة: حول التوقيت لمكة (+3) ورتب القائمة."

    full_prompt = f"{identity}{extra_prompt}\n\nالبيانات:\n{raw_text}"
    
    return call_gemini_with_failover(full_prompt)

def send_to_telegram(text, channel_id):
    if not text or not channel_id: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": channel_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
        requests.post(url, data=payload)
        print(f"✅ تم النشر في {channel_id}")
    except Exception as e:
        print(f"❌ خطأ إرسال: {e}")
