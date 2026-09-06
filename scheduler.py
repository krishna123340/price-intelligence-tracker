import schedule
import time
import subprocess


def job():

    print("\n🔄 Price check running...")

    try:

        subprocess.run(
            ["python3", "price_scraper.py"],
            check=True
        )

        print("✅ Price check finished!")

    except subprocess.CalledProcessError as error:

        print("❌ Price check failed:", error)


# Run once immediately
job()


# Run every 1 minute
schedule.every(1).minutes.do(job)


print("\n⏰ Scheduler started...")
print("📅 Price check will run every 1 minute.")
print("🛑 Press Control + C to stop.")


while True:

    schedule.run_pending()

    time.sleep(1)