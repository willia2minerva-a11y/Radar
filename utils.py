import requests
import google.generativeai as genai
import os
from config import GEMINI_API_KEY, IDENTITIES, BOT_TOKEN, FOOTBALL_KEY

# إعداد Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def get_readable_content(data):
    """
    دالة لاستخراج المحتوى المفيد سواء كان خبراً أو جدول مباريات
    """
    content = ""
    
    # --- الحالة 1: بيانات مباريات (من Football-Data.org) ---
    if "matches" in data:
        matches = data["matches"]
        if not matches:
            return "NO_MATCHES" # علامة خاصة لنعرف أنه لا توجد مباريات
        
        # نأخذ أهم 10 مباريات فقط
        match_list = []
        for match in matches[:10]:
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            time = match['utcDate'] # التوقيت الخام
            league = match['competition']['name']
            # نبني سطراً واحداً لكل مباراة
            match_list.append(f"Match: {home} vs {away} | League: {league} | Time: {time}")
        
        return "Raw Match Schedule:\n" + "\n".join(match_list)

    # --- الحالة 2: أخبار ومقالات (من NewsAPI) ---
    elif "articles" in data and len(data["articles"]) > 0:
        # نأخذ أول خبر متاح
        item = data["articles"][0]
        title = item.get('title', 'No Title')
        desc = item.get('description', '')
        return f"News Title: {title}\nDetails: {desc}"
    
    return None

def smart_fetch_and_process(api_list, channel_type):
    """
    المحرك الرئيسي: يجلب البيانات، يحللها، ويرسلها لـ Gemini
    """
    raw_text = None
    
    # 1. الدوران على المصادر (Failover)
    for url in api_list:
        try:
            headers = {}
            # إذا كان الرابط هو Football-Data، نضيف المفتاح في الهيدر
            if "football-data.org" in url:
                headers = {'X-Auth-Token': FOOTBALL_KEY}
                print(f"[{channel_type}] محاولة جلب جدول المباريات...")
            else:
                print(f"[{channel_type}] محاولة جلب أخبار من المصدر...")

            # طلب البيانات
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                extracted_text = get_readable_content(data)
                
                # إذا كانت النتيجة "لا توجد مباريات"، نتجاوز هذا المصدر ونذهب للتالي
                if extracted_text == "NO_MATCHES":
                    print(f"[{channel_type}] لا توجد مباريات مجدولة الآن، الانتقال للمصدر التالي...")
                    continue
                
                # إذا وجدنا نصاً حقيقياً، نعتمد عليه ونوقف البحث
                if extracted_text:
                    raw_text = extracted_text
                    break
            else:
                print(f"فشل المصدر (Code {response.status_code})")

        except Exception as e:
            print(f"خطأ في الاتصال: {e}")
            continue

    # إذا انتهت القائمة ولم نجد شيئاً
    if not raw_text:
        print(f"[{channel_type}] فشلت جميع المصادر في جلب محتوى.")
        return None

    # 2. المعالجة بـ Gemini
    try:
        print(f"[{channel_type}] جاري الصياغة عبر Gemini...")
        identity = IDENTITIES.get(channel_type, IDENTITIES["economy"])
        
        # تعليمات إضافية خاصة بالمباريات
        extra_instructions = ""
        if "Match Schedule" in raw_text:
            extra_instructions = "\nهام: هذه مواعيد مباريات UTC. حولها لتوقيت السعودية (+3) واعرضها بصيغة (00:00 م/ص). رتبها كقائمة جميلة."

        full_prompt = f"{identity}\n{extra_instructions}\n\nالبيانات الخام:\n{raw_text}"
        
        ai_response = model.generate_content(full_prompt)
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
        "parse_mode": "Markdown" # تأكد أن Gemini لا يستخدم رموزاً تكسر المارك داون
    }
    try:
        requests.post(url, data=payload)
        print(f"✅ تم النشر في {channel_id}")
    except Exception as e:
        print(f"❌ فشل النشر: {e}")
