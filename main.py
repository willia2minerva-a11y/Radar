#!/usr/bin/env python3
"""
🤖 رادار نيوز المتطور - نظام النشر الذكي
نسخة محسنة مع دمج أفضل ميزات bot (1).py
"""

import time
import random
from datetime import datetime
import utils
from config import API_SOURCES

def main():
    print("\n" + "="*60)
    print("🚀 رادار نيوز المتطور v4.0 - النظام الذكي")
    print(f"⏰ وقت البدء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # اختيار عشوائي للقنوات (لمنع التكرار)
    channels = list(API_SOURCES.keys())
    random.shuffle(channels)
    
    success_count = 0
    
    for channel in channels[:2]:  # نشر في قناتين فقط لكل تشغيل
        try:
            print(f"\n🎯 معالجة قناة: {channel.upper()}")
            
            utils.smart_fetch_and_process(
                API_SOURCES[channel],
                channel
            )
            
            success_count += 1
            
            # فاصل بين القنوات (1-3 دقائق عشوائي)
            if channel != channels[-1]:
                wait_time = random.randint(60, 180)
                print(f"⏳ انتظر {wait_time//60} دقائق قبل القناة التالية...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"❌ خطأ في معالجة {channel}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"📊 ملخص التنفيذ:")
    print(f"   ✅ ناجح: {success_count}/{len(channels[:2])}")
    print(f"   🕒 وقت الانتهاء: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    # إرسال تقرير للإدارة إذا كان هناك ADMIN_ID
    if utils.ADMIN_ID:
        try:
            report = f"📋 تقرير الرادار\nالناجح: {success_count}\nالوقت: {datetime.now().strftime('%H:%M')}"
            utils.smart_send_to_telegram(report, utils.ADMIN_ID)
        except:
            pass

if __name__ == "__main__":
    main()
