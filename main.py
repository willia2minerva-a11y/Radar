from channels import sport, tech, economy
import time

def main():
    print("🚀 بدء تشغيل البوت عبر GitHub Actions...")

    # تشغيل القنوات بالتتابع
    
    # 1. الرياضة
    try:
        print("⚽ تشغيل تحديث الرياضة...")
        sport.run()
    except Exception as e:
        print(f"❌ خطأ في الرياضة: {e}")

    # فاصل زمني قصير جداً لعدم التداخل
    time.sleep(5)

    # 2. التقنية
    try:
        print("💻 تشغيل تحديث التقنية...")
        tech.run()
    except Exception as e:
        print(f"❌ خطأ في التقنية: {e}")

    time.sleep(5)

    # 3. الاقتصاد
    try:
        print("💰 تشغيل تحديث الاقتصاد...")
        economy.run()
    except Exception as e:
        print(f"❌ خطأ في الاقتصاد: {e}")

    print("✅ انتهت الدورة. إغلاق البوت.")

if __name__ == "__main__":
    main()
