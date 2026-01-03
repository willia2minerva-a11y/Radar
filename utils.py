import requests
import google.generativeai as genai
import os
from config import GEMINI_API_KEY, IDENTITIES, BOT_TOKEN

# إعداد Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

def get_keys_list(env_var_name):
    """
    جلب سلسلة المفاتيح وتقسيمها إلى قائمة
    مثال: "key1,key2,key3" -> ['key1', 'key2', 'key3']
    """
    keys_str = os.getenv(env_var_name)
    if not keys_str:
        print(f"⚠️ تحذير: لم يتم العثور على مفاتيح في {env_var_name}")
        return []
    # التقسيم وحذف المسافات الزائدة
    return [k.strip() for k in keys_str.split(',') if k.strip()]

def get_readable_content(data):
    """استخراج النص المفيد من البيانات"""
    # 1. حالة المباريات
    if "matches" in data:
        matches = data["matches"]
        if not matches: return "NO_MATCHES"
        match_list = []
        for match in matches[:10]: # أهم 10 مباريات
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            time = match['utcDate']
            league = match['competition']['name']
            match_list.append(f"League: {league} | {home} vs {away} | Time: {time}")
        return "Match Schedule (UTC):\n" + "\n".join(match_list)
    
    # 2. حالة الأخبار
    elif "articles" in data and len(data["articles"]) > 0:
        item = data["articles"][0]
        return f"Title: {item.get('title')}\nDesc: {item.get('description')}"
    
    return None

def smart_fetch_and_process(api_list, channel_type):
    """
    المحرك الرئيسي:
    1. يمر على كل رابط (Source)
    2. داخل كل رابط، يجرب كل المفاتيح (Keys) بالترتيب
    """
    raw_text = None
    
    # تحديد نوع المفاتيح بناءً على نوع القناة أو الرابط
    # هنا سنفترض أننا نملك مجموعتين من المفاتيح في Github Secrets
    news_keys = get_keys_list("NEWS_API_KEY")
    football_keys = get_keys_list("FOOTBALL_DATA_KEY")

    # --- الحلقة الأولى: المصادر (URLs) ---
    for url_template in api_list:
        
        # تحديد أي قائمة مفاتيح سنستخدم لهذا الرابط
        if "football-data.org" in url_template:
            current_keys = football_keys
            is_football = True
        else:
            current_keys = news_keys
            is_football = False
            
        if not current_keys:
            print(f"❌ خطأ: لا توجد مفاتيح متاحة لرابط {channel_type}. تخطي...")
            continue

        # --- الحلقة الثانية: المفاتيح (Keys) ---
        # نجرب المفتاح الأول، لو فشل نجرب الثاني...
        for i, key in enumerate(current_keys):
            try:
                # تجهيز الرابط والهيدر
                final_url = url_template
                headers = {}
                
                if is_football:
                    # مفتاح الكرة يوضع في الهيدر
                    headers = {'X-Auth-Token': key}
                    print(f"🔄 [{channel_type}] المصدر {api_list.index(url_template)+1} | محاولة بالمفتاح رقم {i+1}...")
                else:
                    # مفتاح الأخبار يوضع في الرابط مكان {KEY}
                    final_url = url_template.replace("{KEY}", key)
                    print(f"🔄 [{channel_type}] المصدر {api_list.index(url_template)+1} | محاولة بالمفتاح رقم {i+1}...")

                # تنفيذ الطلب
                response = requests.get(final_url, headers=headers, timeout=20)
                
                # --- معالجة الاستجابة ---
                if response.status_code == 200:
                    data = response.json()
                    extracted = get_readable_content(data)
                    
                    if extracted == "NO_MATCHES":
                        print("ℹ️ الاتصال نجح لكن لا توجد مباريات.")
                        break # نوقف تجربة المفاتيح لهذا المصدر، وننتقل للمصدر التالي
                    
                    if extracted:
                        raw_text = extracted
                        print("✅ تم جلب البيانات بنجاح!")
                        break # نكسر حلقة المفاتيح (وجدنا الحل)
                
                # --- معالجة الأخطاء الشائعة ---
                elif response.status_code == 401:
                    print(f"⚠️ خطأ مصادقة (401): المفتاح رقم {i+1} غير صالح أو انتهى.")
                    # لا نوقف الحلقة، سيكمل للمفتاح التالي تلقائياً
                elif response.status_code == 429:
                    print(f"⚠️ خطأ (429): تجاوزنا الحد المسموح للمفتاح رقم {i+1}.")
                    # يكمل للمفتاح التالي
                else:
                    print(f"❌ خطأ غير متوقع ({response.status_code}): {response.text[:100]}")
                    # يكمل للمفتاح التالي (ربما مفتاح آخر يعمل بطريقة ما)

            except Exception as e:
                print(f"❌ خطأ اتصال مع المفتاح {i+1}: {e}")
                continue # يكمل للمفتاح التالي
        
        # إذا وجدنا نصاً (raw_text) بعد تجربة المفاتيح، نوقف البحث في المصادر أيضاً
        if raw_text:
            break

    # --- النهاية: هل وجدنا محتوى؟ ---
    if not raw_text:
        print(f"🚫 [{channel_type}] فشل جلب أي محتوى بعد تجربة كل المصادر والمفاتيح.")
        return None

    # --- مرحلة الذكاء الاصطناعي (Gemini) ---
    try:
        print(f"🤖 [{channel_type}] جاري المعالجة عبر Gemini...")
        identity = IDENTITIES.get(channel_type, "")
        
        extra_prompt = ""
        if "Match Schedule" in raw_text:
            extra_prompt = "\nملاحظة: التوقيتات UTC. حولها لمكة المكرمة (+3) ورتبها."

        response = model.generate_content(f"{identity}{extra_prompt}\n\nالبيانات:\n{raw_text}")
        return response.text
    except Exception as e:
        print(f"❌ خطأ في Gemini API: {e}")
        return None

def send_to_telegram(text, channel_id):
    if not text or not channel_id: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # disable_web_page_preview يمنع ظهور صورة صغيرة من الرابط للحفاظ على نظافة الرسالة
        payload = {"chat_id": channel_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
        resp = requests.post(url, data=payload)
        if resp.status_code != 200:
            print(f"❌ فشل الإرسال لتليجرام: {resp.text}")
        else:
            print(f"✅ تم النشر في {channel_id}")
    except Exception as e:
        print(f"❌ خطأ إرسال: {e}")
