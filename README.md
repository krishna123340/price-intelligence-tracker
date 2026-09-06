# 📊 Price Intelligence Tracker

> **An automated product price monitoring and smart alert system built with Python.**

Price Intelligence Tracker automatically collects product prices, stores historical price data, detects price changes, and sends notifications when a significant price drop is detected.

The project also includes an interactive **Streamlit dashboard** for monitoring price history and product statistics.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 Web Scraping | Extracts product names and prices automatically |
| 💾 Price History | Stores historical price records using SQLite |
| 📉 Price Detection | Detects price increases, decreases, and unchanged prices |
| 🚨 Smart Alerts | Triggers alerts when price drops cross the configured threshold |
| 📧 Email Alerts | Sends price-drop notifications through Gmail SMTP |
| 📱 Telegram Alerts | Sends instant notifications through Telegram Bot API |
| 📊 Interactive Dashboard | Visualizes product prices using Streamlit |
| 📈 Price Analytics | Tracks current, previous, lowest, and highest prices |
| 🔄 Auto Refresh | Dashboard automatically refreshes every minute |
| ⏰ Automation | Automatically checks prices at scheduled intervals |

---

## 🛠️ Tech Stack

### Programming Language
- Python

### Web Scraping
- Requests
- BeautifulSoup

### Database
- SQLite

### Data Analysis
- Pandas

### Dashboard
- Streamlit

### Data Visualization
- Plotly

### Notifications
- Gmail SMTP
- Telegram Bot API

### Automation
- Schedule

---

## 🏗️ Project Architecture

```text
Product Website
      │
      ▼
Python Web Scraper
      │
      ▼
Data Extraction
      │
      ▼
SQLite Database
      │
      ▼
Price History
      │
      ▼
Price Comparison
      │
      ▼
Drop Detection
      │
      ├──────────────► 📧 Email Alert
      │
      └──────────────► 📱 Telegram Alert
      │
      ▼
Streamlit Dashboard

⚙️ How It Works

1. 🌐 Web Scraping
The Python scraper sends HTTP requests to the product pages and extracts:
Product name
Product price
The project currently uses Books to Scrape as a safe testing environment.

2. 💾 Database Storage
Product prices are stored in a local SQLite database.
Each price record contains:
Product name
Price
Date and time
This allows the system to maintain historical price information.

3. 📊 Price History
Every scheduled price check stores a new price record in the database.
This historical data is later used by the dashboard to visualize price movement.

4. 📉 Price Drop Detection
The system compares the latest recorded price with the previous recorded price.
Formula
Price Drop % =
((Previous Price - Latest Price) / Previous Price) × 100
For example:
Previous Price = £60
Latest Price   = £40

Price Drop =
((60 - 40) / 60) × 100

= 33.33%
If the calculated price drop reaches the configured Alert Threshold, notifications are triggered.

🚨 Smart Alert System
The project supports configurable price-drop alerts.
For example:

Alert Threshold = 5%
If a product's price decreases by 5% or more, the system triggers notifications.
The dashboard also allows the alert threshold to be adjusted.

🔔 Notification System
The tracker supports two notification channels.

📧 Email
Email notifications are sent using:
Gmail SMTP
The notification includes:
Product name
Previous price
Current price
Price-drop percentage

📱 Telegram
Telegram notifications are sent using:
Telegram Bot API
The notification provides the same important price-drop information.

📊 Streamlit Dashboard
The project includes an interactive dashboard built with Streamlit.
The dashboard provides:
🛍️ Total product count
💰 Average current price
🏆 Lowest current price
🚨 Active price drops
📋 Product comparison table
📉 Price-drop status
📈 Price history chart
💱 GBP to INR price display
⚙️ Configurable alert threshold
🔄 Automatic dashboard refresh

📁 Project Structure
price-intelligence-tracker/
│
├── dashboard.py
├── price_scraper.py
├── scheduler.py
├── README.md
├── .gitignore
│
├── prices.db        # Local database, ignored by Git
└── .env             # Credentials, ignored by Git

🚀 Installation
1. Clone the Repository
git clone https://github.com/krishna123340/price-intelligence-tracker.git
Move into the project directory:
cd price-intelligence-tracker
2. Install Required Packages
python3 -m pip install requests beautifulsoup4 streamlit plotly schedule streamlit-autorefresh python-dotenv

🔐 Environment Variables
Create a .env file in the project directory.
Store notification credentials inside .env instead of directly inside the Python source code.

Example:

EMAIL_SENDER=your_email@gmail.com
EMAIL_RECEIVER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
⚠️ Never commit .env to GitHub.
The .gitignore file prevents sensitive files from being uploaded.

▶️ Run the Project

1. Run the Scraper
python3 price_scraper.py
This performs a price check and stores the results in SQLite.

2. Start the Dashboard
python3 -m streamlit run dashboard.py
The dashboard will open in your browser.

3. Start Automatic Price Monitoring
python3 scheduler.py
The scheduler automatically runs the price-checking process at regular intervals.
To stop the scheduler:
Control + C

🧪 Testing Environment
The project currently uses:
Books to Scrape

as a safe testing website for demonstrating the complete price-monitoring workflow.

The current scraper monitors selected products from this testing website.

🔐 Security
Sensitive files are excluded from version control:
.env
prices.db
.DS_Store
Credentials such as:
Email passwords
Telegram bot tokens
Chat IDs
are not stored directly in the source code.
They are loaded through environment variables using .env.

🧪 Alert Testing
The notification system was tested using a controlled test price scenario.
Example:

Previous Price = £60
Latest Price   = £40

Price Drop = 33.33%
The test successfully verified:
Price Comparison
       ↓
Drop Calculation
       ↓
Threshold Detection
       ↓
Email Notification
       ↓
Telegram Notification
Test data is removed from the production database after testing.

🔮 Future Scope
The project can be extended with:
🛍️ Support for multiple e-commerce platforms
🔗 Custom product URL tracking
📊 Advanced price analytics
📈 Price prediction
🤖 AI-powered price insights
☁️ Cloud deployment
📱 Dedicated mobile application
🔔 More notification channels
🗃️ Larger product database
👤 User-specific watchlists

🎯 Project Highlights
This project demonstrates practical implementation of:
Web Scraping
Python Programming
Database Management
Data Analysis
Data Visualization
Automation
API Integration
Email Notifications
Telegram Notifications
Dashboard Development
Environment Variable Management
Git & GitHub

💡 Learning Outcomes
Through this project, the following concepts were implemented:
Python
  ↓
HTTP Requests
  ↓
Web Scraping
  ↓
Data Processing
  ↓
SQLite
  ↓
Price Analysis
  ↓
Automation
  ↓
API Integration
  ↓
Notifications
  ↓
Streamlit Dashboard

👨‍💻 Built With
Python • Requests • BeautifulSoup • SQLite • Pandas • Streamlit • Plotly • Schedule • Gmail SMTP • Telegram Bot API
⭐ Project
Price Intelligence Tracker
An end-to-end Python project for automated product price monitoring, historical price tracking, intelligent price-drop detection, and real-time notifications.


### Ab kya karna hai

`README.md` me **poora old content delete → upar wala code paste → `⌘ + S`**.

⚠️ **Abhi Git commit/push mat karna.** Pehle README save karke mujhe **screenshot bhejna**. Main formatting check karunga, phir GitHub par final push karenge.
