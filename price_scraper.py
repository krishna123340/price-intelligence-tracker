import os
import sqlite3
import requests
import smtplib

from bs4 import BeautifulSoup
from email.message import EmailMessage
from dotenv import load_dotenv


# ==========================================
# CONFIGURATION
# ==========================================

load_dotenv()

PRODUCT_URLS = [
    "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
    "https://books.toscrape.com/catalogue/soumission_998/index.html"
]

DATABASE = "prices.db"

ALERT_THRESHOLD = 5

GBP_TO_INR = 128

# ==========================================
# ALERT TEST MODE
# ==========================================

# True = Gmail + Telegram test
# False = Normal price monitoring

TEST_ALERT = False


# ==========================================
# EMAIL CREDENTIALS
# ==========================================

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# ==========================================
# TELEGRAM CREDENTIALS
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


# ==========================================
# EMAIL ALERT
# ==========================================

def send_email_alert(
    product_name,
    previous_price,
    latest_price,
    drop_percent
):

    if not EMAIL_SENDER or not EMAIL_RECEIVER or not EMAIL_PASSWORD:

        print("⚠️ Email credentials missing.")

        return

    previous_inr = previous_price * GBP_TO_INR
    latest_inr = latest_price * GBP_TO_INR

    message = EmailMessage()

    message["Subject"] = (
        f"📉 Price Drop Alert: {product_name}"
    )

    message["From"] = EMAIL_SENDER

    message["To"] = EMAIL_RECEIVER

    message.set_content(
        f"📉 Price Drop Alert!\n\n"
        f"Product: {product_name}\n\n"
        f"Previous Price: ₹{previous_inr:,.2f}\n"
        f"Current Price: ₹{latest_inr:,.2f}\n"
        f"Price Drop: {drop_percent:.2f}%\n\n"
        f"💱 GBP → INR Rate: ₹{GBP_TO_INR}"
    )

    try:

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=10
        ) as server:

            server.login(
                EMAIL_SENDER,
                EMAIL_PASSWORD
            )

            server.send_message(message)

        print("📧 Email alert sent!")

    except Exception as error:

        print(
            "❌ Email alert failed:",
            error
        )


# ==========================================
# TELEGRAM ALERT
# ==========================================

def send_telegram_alert(
    product_name,
    previous_price,
    latest_price,
    drop_percent
):

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:

        print("⚠️ Telegram credentials missing.")

        return

    previous_inr = previous_price * GBP_TO_INR
    latest_inr = latest_price * GBP_TO_INR

    message = (
        f"📉 Price Drop Alert!\n\n"
        f"🛍️ Product: {product_name}\n\n"
        f"💰 Previous Price: ₹{previous_inr:,.2f}\n"
        f"💰 Current Price: ₹{latest_inr:,.2f}\n"
        f"📉 Price Drop: {drop_percent:.2f}%\n\n"
        f"💱 GBP → INR Rate: ₹{GBP_TO_INR}"
    )

    telegram_url = (
        "https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:

        response = requests.post(
            telegram_url,
            data=data,
            timeout=10
        )

        response.raise_for_status()

        print("📱 Telegram alert sent!")

    except requests.RequestException as error:

        print(
            "❌ Telegram alert failed:",
            error
        )


# ==========================================
# TEST ALERT
# ==========================================

def test_alert():

    print("\n🧪 TEST ALERT MODE")
    print("===================")

    product_name = "A Light in the Attic"

    previous_price = 60

    latest_price = 40

    drop_percent = (
        (previous_price - latest_price)
        / previous_price
    ) * 100

    print(
        f"Product: {product_name}"
    )

    print(
        f"Previous: ₹{previous_price * GBP_TO_INR:,.2f}"
    )

    print(
        f"Current: ₹{latest_price * GBP_TO_INR:,.2f}"
    )

    print(
        f"Drop: {drop_percent:.2f}%"
    )

    print(
        "\n📤 Sending test notifications..."
    )

    send_email_alert(
        product_name,
        previous_price,
        latest_price,
        drop_percent
    )

    send_telegram_alert(
        product_name,
        previous_price,
        latest_price,
        drop_percent
    )


# ==========================================
# SCRAPE PRODUCTS
# ==========================================

def scrape_products():

    product_data = []

    for url in PRODUCT_URLS:

        print("\n🌐 Connecting to:")
        print(url)

        try:

            response = requests.get(
                url,
                timeout=10
            )

            response.raise_for_status()

            print(
                "✅ Website response:",
                response.status_code
            )

        except requests.RequestException as error:

            print(
                "❌ Request failed:",
                error
            )

            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        try:

            title = soup.find(
                "h1"
            ).text.strip()

            price_text = soup.find(
                "p",
                class_="price_color"
            ).text.strip()

            price_text = (
                price_text
                .replace("£", "")
                .replace("Â", "")
            )

            price = float(price_text)

            product_data.append(
                (title, price)
            )

            price_inr = price * GBP_TO_INR

            print(
                f"🛍️ Product: {title}"
            )

            print(
                f"💰 Price: ₹{price_inr:,.2f}"
            )

            print(
                f"   Original: £{price:.2f}"
            )

            print(
                "----------------"
            )

        except (
            AttributeError,
            TypeError,
            ValueError
        ) as error:

            print(
                "⚠️ Product parsing failed:",
                error
            )

    return product_data


# ==========================================
# DATABASE SETUP
# ==========================================

def create_database():

    db = sqlite3.connect(
        DATABASE
    )

    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            product TEXT,
            price REAL,
            date TEXT
        )
    """)

    db.commit()

    db.close()


# ==========================================
# SAVE PRICES
# ==========================================

def save_prices(products):

    db = sqlite3.connect(
        DATABASE
    )

    cursor = db.cursor()

    for name, price in products:

        cursor.execute(
            """
            INSERT INTO prices (
                product,
                price,
                date
            )
            VALUES (
                ?,
                ?,
                datetime(
                    'now',
                    '+5 hours',
                    '+30 minutes'
                )
            )
            """,
            (
                name,
                price
            )
        )

        print(
            f"💾 Saved: {name}"
        )

    db.commit()

    db.close()


# ==========================================
# CHECK PRICE CHANGES
# ==========================================

def check_price_changes():

    db = sqlite3.connect(
        DATABASE
    )

    cursor = db.cursor()

    cursor.execute("""
        SELECT DISTINCT product
        FROM prices
    """)

    products = cursor.fetchall()

    for product in products:

        product_name = product[0]

        cursor.execute(
            """
            SELECT price, date
            FROM prices
            WHERE product = ?
            ORDER BY date DESC
            LIMIT 2
            """,
            (product_name,)
        )

        rows = cursor.fetchall()

        if len(rows) < 2:
            continue

        latest_price = rows[0][0]
        previous_price = rows[1][0]

        print(
            f"\nProduct: {product_name}"
        )

        print(
            f"Latest: ₹{latest_price * GBP_TO_INR:,.2f}"
        )

        print(
            f"Previous: ₹{previous_price * GBP_TO_INR:,.2f}"
        )

        # PRICE DROP
        if latest_price < previous_price:

            drop_percent = (
                (previous_price - latest_price)
                / previous_price
            ) * 100

            print("📉 Price dropped!")

            print(
                f"Drop: {drop_percent:.2f}%"
            )

            if drop_percent >= ALERT_THRESHOLD:

                print(
                    "🚨 Alert threshold reached!"
                )

                send_email_alert(
                    product_name,
                    previous_price,
                    latest_price,
                    drop_percent
                )

                send_telegram_alert(
                    product_name,
                    previous_price,
                    latest_price,
                    drop_percent
                )

            else:

                print(
                    "ℹ️ Price drop is below "
                    "alert threshold."
                )

        # PRICE INCREASE
        elif latest_price > previous_price:

            print(
                "📈 Price increased!"
            )

        # PRICE UNCHANGED
        else:

            print(
                "➡️ Price unchanged!"
            )

    db.close()


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():

    print(
        "\n🚀 Price Intelligence Tracker"
    )

    print(
        "================================"
    )

    # TEST MODE
    if TEST_ALERT:

        test_alert()

        print(
            "\n🧪 Test completed!"
        )

        return

    # NORMAL MODE
    create_database()

    products = scrape_products()

    if not products:

        print(
            "\n❌ No products found."
        )

        return

    save_prices(
        products
    )

    check_price_changes()

    print(
        "\n✅ Price check completed!"
    )


# ==========================================
# PROGRAM START
# ==========================================

if __name__ == "__main__":

    main()