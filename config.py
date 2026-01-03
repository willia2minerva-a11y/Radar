import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# لا حاجة لاستيراد المفاتيح هنا، utils يجلبها بنفسه

# تعريف الروابط فقط
API_SOURCES = {
    "sport": [
        "https://api.football-data.org/v4/matches?status=SCHEDULED",
        "https://newsapi.org/v2/top-headlines?category=sports&country=eg&apiKey={KEY}"
    ],
    "tech": [
        "https://newsapi.org/v2/top-headlines?category=technology&language=ar&apiKey={KEY}"
    ],
    "economy": [
        "https://newsapi.org/v2/everything?q=crypto&apiKey={KEY}"
    ]
}

IDENTITIES = {
    "sport": "أنت رادار الرياضة. لخص المباريات والأخبار بحماس ⚽.",
    "tech": "أنت رادار التقنية. بسط الأخبار التقنية 📱.",
    "economy": "أنت رادار الاقتصاد. حلل سوق الكريبتو والمال 💰."
}
