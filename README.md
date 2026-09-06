# 📊 Price Intelligence Tracker

A Python-based price tracking system that monitors product prices, stores price history, detects price drops, and sends email alerts.

## 🚀 Features

- 🌐 Web scraping using Requests and BeautifulSoup
- 💾 SQLite database for price history
- 📉 Automatic price-drop detection
- 🎯 Custom alert threshold
- 📧 Gmail email alerts
- ⏰ Automatic price checking using Scheduler
- 📊 Streamlit dashboard
- 📈 Interactive price history charts
- 🏆 Lowest and highest price tracking
- 🔄 Dashboard auto-refresh

## 🛠️ Technologies Used

- Python
- Requests
- BeautifulSoup
- SQLite
- Pandas
- Streamlit
- Plotly
- SMTP / Gmail
- Schedule

## 📂 Project Structure

```text
price-i/
├── dashboard.py
├── price_scraper.py
├── scheduler.py
├── .gitignore
└── README.md

⚙️ How It Works

Product Website
      ↓
Python Scraper
      ↓
SQLite Database
      ↓
Price Comparison
      ↓
Price Drop Detection
      ↓
Email Alert
      ↓
Streamlit Dashboard

▶️ Run the Project

Start the dashboard:
python3 -m streamlit run dashboard.py
Run the scraper:
python3 price_scraper.py
Start automatic price checking:
python3 scheduler.py

🔐 Security

Sensitive credentials are stored in .env and should never be uploaded to GitHub.

📌 Testing Website

This project currently uses Books to Scrape as a safe testing website for the scraper.

🎯 Future Improvements

Add more products
Support multiple stores
Telegram notifications
Better analytics
Price prediction
AI-based price insights