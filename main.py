import time
import schedule
from channels import sport, tech, mix

def job_sport():
    sport.run()

def job_tech():
    tech.run()

def job_mix():
    mix.run()

def main():
    print("🤖 البوت يعمل الآن...")

    # جدولة المهام (مثلاً)
    # الرياضة كل ساعتين
    schedule.every(2).hours.do(job_sport)
    
    # التقنية كل 4 ساعات
    schedule.every(4).hours.do(job_tech)
    
    # المنوعات كل 6 ساعات
    schedule.every(6).hours.do(job_mix)

    # تشغيل فوري للتجربة عند البدء
    job_sport()
    # job_tech() 
    # job_mix()

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
