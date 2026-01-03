import time
import schedule
from channels import sport, tech, economy  # تأكد أنك أنشأت ملف economy.py

def job_sport():
    print("⏰ حان وقت نشر الرياضة...")
    sport.run()

def job_tech():
    print("⏰ حان وقت نشر التقنية...")
    tech.run()

def job_economy():
    print("⏰ حان وقت نشر الاقتصاد...")
    economy.run()

def main():
    print("🤖 البوت يعمل الآن (Sport + Tech + Economy)...")

    # --- جدول المواعيد ---
    
    # الرياضة: كل 4 ساعات (لتغطية المباريات والأخبار)
    schedule.every(4).hours.do(job_sport)
    
    # التقنية: كل 6 ساعات
    schedule.every(6).hours.do(job_tech)
    
    # الاقتصاد: كل 6 ساعات (تحديث أسعار وعملات)
    schedule.every(6).hours.do(job_economy)

    # --- تشغيل تجريبي أولي عند بدء البوت ---
    # (قم بإلغاء التعليق إذا أردت أن ينشر فور التشغيل للتجربة)
    # job_sport()
    # job_tech()
    # job_economy()

    # حلقة الانتظار اللانهائية
    while True:
        schedule.run_pending()
        time.sleep(60) # فحص الجدول كل دقيقة

if __name__ == "__main__":
    main()
