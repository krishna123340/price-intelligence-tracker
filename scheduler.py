import schedule
import time
import subprocess

def job():
    print("🔄 Price check running...")
    subprocess.run(["python3", "price_scraper.py"])

schedule.every(1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)