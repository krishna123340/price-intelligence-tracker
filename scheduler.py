import os
import schedule
import time
import subprocess

from dotenv import load_dotenv


# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()


# ==========================================
# CONFIGURATION
# ==========================================

# .env se interval read hoga
# Agar .env mein value nahi mili,
# to default 1 minute rahega

PRICE_CHECK_INTERVAL = int(
    os.getenv("PRICE_CHECK_INTERVAL", "1")
)


# ==========================================
# PRICE CHECK JOB
# ==========================================

def job():

    print("\n🔄 Price check running...")
    print("================================")

    try:

        subprocess.run(
            ["python3", "price_scraper.py"],
            check=True
        )

        print("================================")
        print("✅ Price check finished!")

    except subprocess.CalledProcessError as error:

        print("================================")
        print("❌ Price check failed!")
        print("Error:", error)


# ==========================================
# STARTUP
# ==========================================

print("\n🚀 Price Intelligence Tracker Scheduler")
print("========================================")

print("▶️ Running first price check...")

# Program start hote hi ek baar check
job()


# ==========================================
# SCHEDULE
# ==========================================

schedule.every(
    PRICE_CHECK_INTERVAL
).minutes.do(job)


# ==========================================
# SCHEDULER STATUS
# ==========================================

print("\n⏰ Scheduler started!")

print(
    f"📅 Price check will run every "
    f"{PRICE_CHECK_INTERVAL} minute(s)."
)

print("🛑 Press Control + C to stop.")


# ==========================================
# MAIN LOOP
# ==========================================

try:

    while True:

        schedule.run_pending()

        time.sleep(1)


except KeyboardInterrupt:

    print("\n\n🛑 Scheduler stopped by user.")
    print("👋 Goodbye!")