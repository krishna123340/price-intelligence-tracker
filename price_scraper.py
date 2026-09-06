import requests
from bs4 import BeautifulSoup
import sqlite3

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

ALERT_THRESHOLD = 5

url = "https://books.toscrape.com/"


# Email alert function
def send_email_alert(product_name, previous, latest, drop_percent):

    msg = EmailMessage()

    msg["Subject"] = f"📉 Price Drop Alert: {product_name}"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    msg.set_content(
        f"Price dropped for {product_name}.\n\n"
        f"Previous price: £{previous:.2f}\n"
        f"Current price: £{latest:.2f}\n"
        f"Drop: {drop_percent:.2f}%"
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("📧 Email alert sent!")

    except Exception as e:
        print("❌ Email failed:", e)


# Website request
page = requests.get(url)

print("Status:", page.status_code)

soup = BeautifulSoup(page.text, "html.parser")

print("Title:", soup.title.text)

products = soup.find_all("article", class_="product_pod")


# Connect to database
db = sqlite3.connect("prices.db")
cursor = db.cursor()


# Create table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS prices (
    product TEXT,
    price REAL,
    date TEXT
)
""")


# Save latest prices
for product in products[:5]:

    name = product.h3.a["title"]

    price = product.find("p", class_="price_color").text.strip()
    price = price.replace("£", "").replace("Â", "")
    price = float(price)

    cursor.execute(
        """
        INSERT INTO prices (product, price, date)
        VALUES (?, ?, datetime('now', '+5 hours', '+30 minutes'))
        """,
        (name, price)
    )

    print("Product:", name)
    print("Price:", price)
    print("----------------")


db.commit()
db.close()


# Check price changes
db = sqlite3.connect("prices.db")
cursor = db.cursor()


cursor.execute("""
SELECT DISTINCT product
FROM prices
""")


products = cursor.fetchall()


for product in products:

    product_name = product[0]

    cursor.execute("""
    SELECT price, date
    FROM prices
    WHERE product = ?
    ORDER BY date DESC
    LIMIT 2
    """, (product_name,))

    rows = cursor.fetchall()

    if len(rows) < 2:
        continue

    latest_price = rows[0][0]
    old_price = rows[1][0]

    print("\nProduct:", product_name)
    print("Latest:", latest_price)
    print("Previous:", old_price)


    # Price dropped
    if latest_price < old_price:

        drop_percent = (
            (old_price - latest_price)
            / old_price
        ) * 100

        print("📉 Price dropped!")
        print("Drop:", round(drop_percent, 2), "%")


        # Email only if drop >= threshold
        if drop_percent >= ALERT_THRESHOLD:

            send_email_alert(
                product_name,
                old_price,
                latest_price,
                drop_percent
            )

        else:

            print("📧 Email not sent — below threshold")


    # Price increased
    elif latest_price > old_price:

        print("📈 Price increased!")


    # Price unchanged
    else:

        print("➡️ Price unchanged!")


db.close()