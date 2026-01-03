import os
from dotenv import load_dotenv

load_dotenv()

# --- المتغيرات الأساسية ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- معرفات القنوات ---
CHANNELS = {
    "sport": os.getenv("SPORT_CHANNEL_ID"),
    "tech": os.getenv("TECH_CHANNEL_ID"),
    "economy": os.getenv("MIX_CHANNEL_ID") # قناة الاقتصاد
}

# --- المصادر (API Sources) ---
# ملاحظة: نستخدم {KEY} كعلامة سيقوم ملف utils باستبدالها بالمفتاح الحقيقي
API_SOURCES = {
    "sport": [
        # المصدر 1: مباريات اليوم (يحتاج مفتاح في الهيدر، لا نضعه في الرابط)
        "https://api.football-data.org/v4/matches?status=SCHEDULED",
        
        # المصدر 2: أخبار رياضية (NewsAPI) - لاحظ مكان {KEY}
        "https://newsapi.org/v2/top-headlines?category=sports&country=eg&apiKey={KEY}"
    ],
    "tech": [
        "https://newsapi.org/v2/top-headlines?category=technology&language=ar&apiKey={KEY}"
    ],
    "economy": [
        "https://newsapi.org/v2/everything?q=bitcoin OR crypto&language=ar&sortBy=publishedAt&apiKey={KEY}",
        "https://newsapi.org/v2/top-headlines?category=business&country=ae&apiKey={KEY}"
    ]
}

# --- الهويات (Prompts) ---
IDENTITIES = {
    "sport": """
    أنت محلل رياضي محترف. 
    - إذا كانت مباريات: اعرض الجدول بتوقيت مكة (أضف 3 ساعات لـ UTC) مع إيموجي ⚽.
    - إذا كان خبراً: لخصه بحماس.
    """,
    "tech": "أنت خبير تقني. اشرح الخبر ببساطة وفائدة للمستخدم.",
    "economy": "أنت خبير اقتصادي. ركز على لغة الأرقام، وحلل تأثير الخبر على السوق (صعود/هبوط) دون نصائح استثمارية."
}
