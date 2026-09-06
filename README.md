# 📊 Price Intelligence Tracker

> **An automated price monitoring and alert system built with Python.**

Track product prices, maintain historical data, detect price drops, and receive instant notifications through **Email & Telegram**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 Web Scraping | Extracts product names and prices automatically |
| 💾 Price History | Stores historical prices using SQLite |
| 📉 Price Detection | Detects price increases, decreases, and unchanged prices |
| 🚨 Smart Alerts | Sends alerts when price drops cross the threshold |
| 📧 Email Alerts | Gmail notifications for significant price drops |
| 📱 Telegram Alerts | Instant Telegram notifications |
| 📊 Dashboard | Interactive Streamlit dashboard |
| 📈 Analytics | Price history, lowest & highest price tracking |
| 🔄 Auto Refresh | Dashboard automatically refreshes |

---

## 🛠️ Tech Stack

**Language:** Python  
**Web Scraping:** Requests, BeautifulSoup  
**Database:** SQLite  
**Data Analysis:** Pandas  
**Dashboard:** Streamlit  
**Visualization:** Plotly  
**Notifications:** Gmail SMTP, Telegram Bot API  
**Automation:** Schedule  

---

## ⚙️ How It Works

```text
🌐 Product Website
        ↓
🐍 Python Scraper
        ↓
🧹 Data Extraction
        ↓
💾 SQLite Database
        ↓
📊 Price History
        ↓
🔍 Price Comparison
        ↓
📉 Drop Detection
        ↓
🚨 Email + Telegram Alert
        ↓
📊 Streamlit Dashboard

📉 Price Drop Detection
The system compares the latest price with the previous recorded price.
Formula:

Price Drop %
=
(Previous Price − Latest Price)
──────────────────────────── × 100
       Previous Price
If the calculated drop reaches the configured Alert Threshold, the system automatically sends notifications.
🔔 Notification System
The tracker supports two notification channels:
📧 Email — Gmail SMTP
📱 Telegram — Telegram Bot API
All sensitive credentials are stored securely in the .env file and excluded from GitHub using .gitignore.
▶️ Run the Project
1. Run the Scraper
python3 price_scraper.py
2. Start the Dashboard
python3 -m streamlit run dashboard.py
3. Start Automatic Price Monitoring
python3 scheduler.py
🔐 Security
Sensitive files are excluded from version control:
.env
prices.db
.DS_Store
Credentials such as email passwords and Telegram bot tokens are never stored directly in the source code.
🌐 Testing Environment
The project currently uses Books to Scrape as a safe testing website for demonstrating the price-tracking workflow.
🚀 Future Scope
🛍️ Multiple e-commerce stores
🔗 Custom product URL tracking
📊 Advanced price analytics
🤖 AI-powered price insights
☁️ Cloud deployment
📱 Enhanced notification system
🎯 Project Highlights
This project demonstrates practical implementation of Web Scraping, Database Management, Data Analysis, Automation, API Integration, Notifications, and Dashboard Development using Python.
👨‍💻 Built With
Python • SQLite • Streamlit • Plotly • BeautifulSoup • Telegram API

Ye version **GitHub par kaafi professional** lagega—especially tumhare 2nd-year portfolio/project ke liye.  

Aur haan, **How It Works ke neeche wala flow diagram rehne dena**; wahi README ko visually aesthetic banata hai.
