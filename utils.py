import requests
import google.generativeai as genai
import os
import time
import random
import re
import json
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import telebot
from config import IDENTITIES, IMAGE_CONFIG, PUBLISHING_SCHEDULE, BOT_TOKEN, ADMIN_ID

# === نظام المفاتيح الذكي ===
def get_keys_list(env_var_name):
    """نظام متعدد المفاتيح مع تدوير ذكي"""
    keys_str = os.getenv(env_var_name, "")
    if not keys_str:
        return []
    
    keys = [k.strip() for k in keys_str.split(',') if k.strip()]
    
    # حفظ آخر مفتاح مستخدم لتجنب التكرار
    cache_file = f"{env_var_name}_cache.txt"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                last_index = int(f.read().strip())
            keys = keys[last_index:] + keys[:last_index]
    except:
        pass
    
    return keys

def update_key_index(env_var_name, index):
    """تحديث مؤشر المفتاح المستخدم"""
    cache_file = f"{env_var_name}_cache.txt"
    with open(cache_file, 'w') as f:
        f.write(str((index + 1) % 10))

# === نظام الموديلات الآمنة ===
SAFE_MODELS = [
    "models/gemini-1.5-flash",      # الأسرع للأخبار
    "models/gemini-1.5-flash-8b",   # نسخة خفيفة
    "models/gemini-1.5-pro",        # للتحليل العميق
    "models/gemini-1.0-pro"         # احتياطي
]

# === مصادر الصور المتعددة ===
IMAGE_SOURCES = [
    {
        "name": "Unsplash",
        "url_template": "https://source.unsplash.com/featured/1080x1080/?{query}",
        "fallback": "https://source.unsplash.com/random/1080x1080"
    },
    {
        "name": "Picsum",
        "url_template": "https://picsum.photos/1080/1080?random={random_id}",
        "fallback": "https://picsum.photos/1080/1080"
    },
    {
        "name": "LoremFlickr",
        "url_template": "https://loremflickr.com/1080/1080/{query}",
        "fallback": "https://loremflickr.com/1080/1080/all"
    }
]

# === نظام التوقيت الذكي ===
def get_smart_publishing_time():
    """تحديد وقت النشر الأمثل (مقتبس من bot (1).py)"""
    current_hour = datetime.now().hour
    current_weekday = datetime.now().strftime("%A")
    
    for hour, greeting in PUBLISHING_SCHEDULE["optimal_times"]:
        if current_hour == hour and current_weekday in PUBLISHING_SCHEDULE["best_days"]:
            return greeting
    return "🌟 تحديث جديد مع"

# === توليد الصور الذكي ===
def generate_smart_image(category, query=None):
    """نظام متطور لتوليد الصور (مقتبس من bot (1).py)"""
    print(f"🖼️ توليد صورة ذكية للتصنيف: {category}")
    
    config = IMAGE_CONFIG.get(category, IMAGE_CONFIG["tech"])
    keywords = config["keywords"]
    
    if query:
        keywords.insert(0, query)
    
    chosen_query = random.choice(keywords)
    
    # تجربة جميع المصادر
    for source in IMAGE_SOURCES:
        try:
            print(f"   🔍 جرب {source['name']}...")
            
            if "{query}" in source["url_template"]:
                url = source["url_template"].format(query=chosen_query)
            elif "{random_id}" in source["url_template"]:
                url = source["url_template"].format(random_id=random.randint(1, 10000))
            else:
                url = source["fallback"]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # التحقق من الصورة
                img = Image.open(BytesIO(response.content))
                img.verify()
                
                img_io = BytesIO(response.content)
                img_io.name = 'smart_image.jpg'
                
                print(f"   ✅ نجاح من {source['name']}")
                return img_io
                
        except Exception as e:
            print(f"   ⚠️ {source['name']} فشل: {str(e)[:50]}")
            continue
    
    # إنشاء صورة مخصصة إذا فشلت المصادر
    return create_custom_image(category, chosen_query)

def create_custom_image(category, query):
    """إنشاء صورة مخصصة (مقتبس من bot (1).py)"""
    config = IMAGE_CONFIG.get(category, IMAGE_CONFIG["tech"])
    
    img = Image.new('RGB', (1080, 1080), color=config["color"])
    draw = ImageDraw.Draw(img)
    
    try:
        # إضافة نص وصورة
        font = ImageFont.load_default()
        text = f"{config['emoji']}\n{query.upper()}"
        draw.text((540, 400), text, fill=(255, 255, 255), font=font, anchor="mm", align="center")
        draw.text((540, 500), "رادار نيوز", fill=(255, 255, 255), font=font, anchor="mm")
    except:
        pass
    
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=90)
    img_byte_arr.seek(0)
    img_byte_arr.name = 'custom_image.jpg'
    
    return img_byte_arr

# === نظام توليد المحتوى الذكي ===
def generate_ai_content(prompt, category):
    """نظام متعدد المفاتيح والموديلات (مقتبس من bot (1).py)"""
    print(f"\n🧠 توليد محتوى ذكي للتصنيف: {category}")
    
    gemini_keys = get_keys_list("GEMINI_API_KEY")
    if not gemini_keys:
        print("❌ لا توجد مفاتيح Gemini")
        return None
    
    for key_index, api_key in enumerate(gemini_keys):
        print(f"\n🔄 تجربة المفتاح #{key_index + 1}")
        
        for model_name in SAFE_MODELS:
            try:
                print(f"   🤖 جرب النموذج: {model_name}")
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(model_name)
                
                # إعدادات لجعل المحتوى بشرياً
                generation_config = genai.GenerationConfig(
                    temperature=0.8,
                    top_p=0.95,
                    max_output_tokens=500,
                    top_k=40
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                if response and response.text:
                    print(f"   ✅ المحتوى تم توليده بنجاح")
                    update_key_index("GEMINI_API_KEY", key_index)
                    return response.text.strip()
                    
            except Exception as e:
                error_msg = str(e)
                
                if "404" in error_msg:
                    print(f"   ⚠️ النموذج {model_name} غير مدعوم")
                    continue
                elif "429" in error_msg:
                    print(f"   ⏳ المفتاح محدود، انتظر 30 ثانية")
                    time.sleep(30)
                    break
                elif "quota" in error_msg.lower():
                    print(f"   💸 حصة المفتاح نفذت")
                    break
                else:
                    print(f"   ❌ خطأ: {error_msg[:80]}")
                    continue
    
    return None

# === تنسيق المنشور النهائي ===
def format_post(content, category, greeting):
    """تنسيق احترافي للمنشور (مقتبس من bot (1).py)"""
    
    # إضافة الترحيب
    formatted = f"{greeting}\n\n"
    
    # تنظيف المحتوى
    content = re.sub(r'\*\*\*', '**', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # إضافة المحتوى
    formatted += content
    
    # إضافة عناصر تفاعلية حسب التصنيف
    interactive_elements = {
        "sport": [
            "\n\n⚽ **تحدي المباراة:** من سيفوز في رأيك؟",
            "\n\n🏆 **نصيحة تكتيكية:** شاهد المباراة من منظور المدرب!",
            "\n\n🎯 **إحصائية مذهلة:** هل تعلم أن...",
        ],
        "tech": [
            "\n\n🛠️ **جرب بنفسك:** الأداة متاحة مجاناً",
            "\n\n💡 **نصيحة تقنية:** احفظ هذه المعلومة",
            "\n\n🚀 **توقع المستقبل:** خلال سنة ستكون...",
        ],
        "economy": [
            "\n\n📈 **تحليل سريع:** اتجاه السوق صاعد/هابط",
            "\n\n💎 **فرصة ذهبية:** انتبه إلى...",
            "\n\n⚠️ **تحذير مهم:** تجنب...",
        ]
    }
    
    formatted += random.choice(interactive_elements.get(category, ["\n\n🌟 استفد وشارك الفائدة!"]))
    
    # إضافة هاشتاقات ذكية
    hashtags = {
        "sport": "\n\n#رياضة #كرة_القدم #أخبار_الرياضة #مباريات #رادار_الرياضة",
        "tech": "\n\n#تقنية #ذكاء_اصطناعي #تكنولوجيا #أدوات #رادار_التقنية",
        "economy": "\n\n#اقتصاد #كريبتو #استثمار #أسواق_المال #رادار_الاقتصاد"
    }
    
    formatted += hashtags.get(category, "\n\n#أخبار #محتوى #مفيد")
    
    # التحقق من الطول
    if len(formatted) > 900:
        formatted = formatted[:850] + "...\n\n📖 **تابع القراءة في التعليقات!**"
    
    return formatted

# === نظام الإرسال الذكي ===
def smart_send_to_telegram(text, channel_id, image_data=None):
    """إرسال ذكي مع معالجة الأخطاء"""
    if not text or not channel_id:
        print("❌ نص أو معرف القناة مفقود")
        return False
    
    try:
        bot = telebot.TeleBot(BOT_TOKEN)
        
        # التحقق من تنسيق Markdown
        text = validate_markdown(text)
        
        if image_data:
            bot.send_photo(
                channel_id,
                image_data,
                caption=text,
                parse_mode="Markdown",
                disable_notification=False
            )
            print(f"✅ تم النشر مع صورة إلى {channel_id}")
        else:
            bot.send_message(
                channel_id,
                text,
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            print(f"✅ تم النشر كنص إلى {channel_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في الإرسال: {e}")
        
        # محاولة بدون تنسيق Markdown
        try:
            plain_text = re.sub(r'[*_`\[\]()]', '', text)[:800]
            bot.send_message(channel_id, plain_text)
            print("⚠️ تم النشر كنص عادي")
            return True
        except:
            print("❌ فشل الإرسال تماماً")
            return False

def validate_markdown(text):
    """التحقق من صحة تنسيق Markdown"""
    # إغلاق العلامات المفتوحة
    while text.count('**') % 2 != 0:
        text += '**'
    while text.count('*') % 2 != 0:
        text += '*'
    while text.count('_') % 2 != 0:
        text += '_'
    while text.count('`') % 2 != 0:
        text += '`'
    
    # إصلاح الروابط
    text = re.sub(r'(\[[^\]]*)$', '', text)
    
    return text

# === المحرك الرئيسي ===
def smart_fetch_and_process(api_list, channel_type):
    """المحرك الذكي: جلب → معالجة → صور → نشر"""
    
    print(f"\n{'='*60}")
    print(f"🚀 بدء معالجة: {channel_type}")
    print(f"{'='*60}")
    
    # 1. جلب البيانات
    raw_data = fetch_data(api_list, channel_type)
    if not raw_data:
        print(f"❌ {channel_type}: لا توجد بيانات")
        return
    
    # 2. توليد المحتوى الذكي
    greeting = get_smart_publishing_time()
    identity = IDENTITIES.get(channel_type, "")
    
    full_prompt = f"""{identity}

البيانات الخام:
{raw_data}

🎯 التعليمات:
1. لخص المعلومة بشكل جذاب
2. أضف تحليلاً بسيطاً
3. استخدم لغة عربية سهلة
4. أضف قيمة للمتابع
5. الطول: 150-250 كلمة
6. كن طبيعياً كصديق ينقل خبراً مهماً

✅ المطلوب: منشور جاهز للنشر فوراً"""
    
    content = generate_ai_content(full_prompt, channel_type)
    
    if not content:
        content = generate_fallback_content(channel_type, raw_data)
    
    # 3. توليد صورة ذكية
    image_data = generate_smart_image(channel_type)
    
    # 4. تنسيق المنشور النهائي
    final_post = format_post(content, channel_type, greeting)
    
    # 5. النشر
    channel_id = os.getenv(f"{channel_type.upper()}_CHANNEL_ID")
    success = smart_send_to_telegram(final_post, channel_id, image_data)
    
    if success:
        print(f"\n🎉 {channel_type}: تم النشر بنجاح!")
    else:
        print(f"\n⚠️ {channel_type}: حدثت مشاكل طفيفة في النشر")
    
    print(f"{'='*60}")

def fetch_data(api_list, channel_type):
    """جلب البيانات من مصادر متعددة"""
    news_keys = get_keys_list("NEWS_API_KEY")
    football_keys = get_keys_list("FOOTBALL_DATA_KEY")
    
    for url_template in api_list:
        current_keys = football_keys if "football-data.org" in url_template else news_keys
        is_football = "football-data.org" in url_template
        
        if not current_keys:
            continue
        
        for key in current_keys:
            try:
                final_url = url_template if is_football else url_template.replace("{KEY}", key)
                headers = {'X-Auth-Token': key} if is_football else {}
                
                print(f"🌐 جلب البيانات من: {final_url[:80]}...")
                response = requests.get(final_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if is_football and "matches" in data:
                        return extract_football_data(data)
                    elif "articles" in data:
                        return extract_news_data(data)
                        
            except Exception as e:
                print(f"⚠️ خطأ في الجلب: {str(e)[:50]}")
                continue
    
    return None

def extract_football_data(data):
    """استخراج بيانات المباريات"""
    if "matches" in data and data["matches"]:
        matches = data["matches"][:5]
        lines = []
        for match in matches:
            home = match.get('homeTeam', {}).get('name', 'فريق')
            away = match.get('awayTeam', {}).get('name', 'فريق')
            date = match.get('utcDate', 'تاريخ غير محدد')
            competition = match.get('competition', {}).get('name', 'بطولة')
            lines.append(f"{home} 🆚 {away} | {competition} | {date}")
        return "المباريات القادمة:\n" + "\n".join(lines)
    return "لا توجد مباريات قادمة حالياً"

def extract_news_data(data):
    """استخراج الأخبار"""
    if "articles" in data and data["articles"]:
        articles = data["articles"][:3]
        lines = []
        for i, article in enumerate(articles[:3], 1):
            title = article.get('title', 'بدون عنوان')
            desc = article.get('description', 'بدون وصف')[:150]
            source = article.get('source', {}).get('name', 'مصدر')
            lines.append(f"{i}. {title}\n   {desc}... (المصدر: {source})")
        return "أهم الأخبار:\n" + "\n\n".join(lines)
    return "لا توجد أخبار جديدة"

def generate_fallback_content(category, raw_data):
    """محتوى احتياطي ذكي"""
    fallbacks = {
        "sport": f"⚽ **تحديث رياضي سريع:**\n{raw_data[:300]}...\n\nتابعنا للمزيد من التفاصيل المثيرة!",
        "tech": f"📱 **آخر التطورات التقنية:**\n{raw_data[:300]}...\n\nالتقنية تتطور بسرعة، كن في المقدمة!",
        "economy": f"💰 **نظرة على الأسواق:**\n{raw_data[:300]}...\n\nالفرص لا تنتظر، كن مستعداً!"
    }
    return fallbacks.get(category, f"📢 **تحديث جديد:**\n{raw_data[:300]}...")
