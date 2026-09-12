# ⚡ PRICE INTELLIGENCE TRACKER

> **Automated price monitoring • Historical analytics • Smart alerts • AI-powered insights**

A Python-based price intelligence system that fetches configured product prices, stores historical records in SQLite, detects price changes, sends Email/Telegram alerts, and presents the results through an interactive Streamlit dashboard.

## ✦ Architecture

```text
Product Pages
     ↓
Requests + BeautifulSoup
     ↓
SQLite Price History
     ↓
Price Change Detection
     ├──→ Email Alert
     └──→ Telegram Alert
     ↓
Streamlit Dashboard
     ↓
AI Price Insights
```

## 🚀 Features

- 🌐 Automated product price scraping
- 🗄️ SQLite price-history storage
- 📉 Price drop / increase detection
- 🚨 Email alerts through Gmail SMTP
- 📱 Telegram bot alerts
- 💱 GBP → INR conversion
- 📊 Interactive Plotly price-history charts
- 🔄 Automatic dashboard refresh
- ⏰ Scheduled price checking
- 🤖 OpenAI-powered price insights
- 🎨 Dashboard themes, fonts, graph types and wallpaper options
- 🧪 Test mode for notification alerts

## 🤖 AI Price Insights

The AI module calculates and analyzes:
- Latest price
- Previous price
- Price change percentage
- Lowest recorded price
- Highest recorded price
- Historical average
- Alert threshold

It also classifies the current trend as **Falling, Rising, or Stable** and generates a short practical buying insight.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core logic |
| Requests | HTTP requests |
| BeautifulSoup | HTML parsing |
| SQLite | Price history |
| Pandas | Data processing |
| Plotly | Interactive charts |
| Streamlit | Dashboard |
| OpenAI API | AI insights |
| Schedule | Automatic checking |
| SMTP | Email alerts |
| Telegram Bot API | Telegram alerts |
| python-dotenv | Secret configuration |

## 📁 Project Structure

```text
price-intelligence-tracker/
├── dashboard.py
├── price_scraper.py
├── ai_insights.py
├── scheduler.py
├── requirements.txt
├── README.md
├── prices.db
└── .env                 # local only — never commit
```

### `price_scraper.py`
Handles product scraping, database creation, price storage, price-change detection, Email/Telegram alerts, and the main monitoring cycle.

### `ai_insights.py`
Calculates price statistics, determines the price trend, calls the OpenAI API, and prepares AI insights.

### `dashboard.py`
Loads historical data and displays metrics, AI insights, price statistics, recent records, and interactive Plotly charts.

### `scheduler.py`
Runs the scraper automatically at a configurable interval.

## ▶️ Run Locally

### 1. Clone

```bash
git clone https://github.com/krishna123340/price-intelligence-tracker.git
cd price-intelligence-tracker
```

### 2. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 3. Configure `.env`

```env
OPENAI_API_KEY=your_api_key
EMAIL_SENDER=your_email
EMAIL_RECEIVER=receiver_email
EMAIL_PASSWORD=your_app_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
PRICE_CHECK_INTERVAL=1
```

> **Never commit `.env` or expose API keys/passwords on GitHub.**

### 4. Start dashboard

```bash
python3 -m streamlit run dashboard.py
```

### 5. Start automatic monitoring

```bash
python3 scheduler.py
```

## 💱 Currency

The current project uses a configured **GBP → INR rate of ₹128**. This is a project configuration value, not a live exchange-rate feed.

## 🧪 Alert Testing

The scraper includes a test-alert mode for Email and Telegram notifications.

```python
TEST_ALERT = True
```

After testing, change it back to:

```python
TEST_ALERT = False
```

## 🔐 Security

Credentials are loaded through environment variables rather than hard-coded into the source.

Keep `.env` local. Also avoid committing runtime databases if they contain private or personal data.

## ⚠️ Data Source

The current scraper is configured for the **Books to Scrape** demonstration website. The project does not rely on bypassing CAPTCHA, anti-bot systems, or access controls.

## 🎯 Portfolio Value

This project demonstrates practical experience with:

**Python automation → Web scraping → SQLite → Data analysis → Visualization → Scheduling → Alerts → AI API integration → Streamlit**

## 🔮 Future Scope

- 🛒 More e-commerce sources through permitted/authorized data access
- 💱 Live currency exchange rates
- 📈 Advanced price forecasting
- ☁️ Cloud database
- 📱 Dedicated mobile application
- 🔔 More notification channels
- 👤 Multi-user cloud accounts

## 👨‍💻 Author

**Krishna Singh**

ECE Student • Python • AI/ML • Automation

---

### ⚡ Project Status

**Working portfolio project**
