# 📊 Price Intelligence Tracker

A Python-based product price monitoring and alert system that automatically tracks product prices, stores price history, detects price drops, and displays insights through an interactive Streamlit dashboard.

## 🚀 Features

- 🌐 Automated product price scraping
- 🗄️ SQLite price-history database
- 📉 Price-drop detection
- 🚨 Email & Telegram alerts
- 💱 GBP → INR price conversion
- 📊 Interactive Plotly price-history charts
- 🔄 Streamlit dashboard auto-refresh
- ⏰ Automated price checking
- 🤖 GitHub Actions automation
- ☁️ Streamlit Cloud deployment

## 🏗️ Architecture

Website
↓
Python Scraper
↓
SQLite Database
↓
Price Change Detection
↓
Email / Telegram Alerts
↓
Streamlit Dashboard

## 🛠️ Tech Stack

- Python
- Requests
- BeautifulSoup
- SQLite
- Pandas
- Plotly
- Streamlit
- GitHub Actions
- Schedule
- SMTP
- Telegram Bot API

## ⚙️ How It Works

1. The scraper requests product pages.
2. BeautifulSoup extracts product names and prices.
3. Prices are stored in SQLite.
4. Previous and latest prices are compared.
5. Price drops are detected automatically.
6. Alerts can be sent through Email and Telegram.
7. Streamlit visualizes the price history.
8. GitHub Actions automates the scraping workflow.

## 📊 Dashboard

The dashboard provides:

- Total products
- Average price
- Lowest price
- Active price drops
- Current price
- Previous price
- Price-change percentage
- Historical price charts

## 🤖 Automation

GitHub Actions runs the price-tracking workflow automatically.

The workflow:

- Sets up Python
- Installs dependencies
- Runs the scraper
- Updates the database
- Commits updated price data

## ☁️ Deployment

The Streamlit dashboard is deployed online using Streamlit Community Cloud.

## 📸 Screenshots

Dashboard screenshots are available in the `screenshots/` folder.

## 🔐 Security

Sensitive credentials such as email passwords, Telegram tokens, and environment variables are kept outside the source code.

## 🔮 Future Improvements

- ☁️ Cloud database integration
- 💹 Live currency exchange rates
- 🤖 AI-powered price insights
- 📱 Mobile-friendly dashboard
- 📈 Advanced price forecasting
- 🛒 Support for additional e-commerce platforms
- 🔔 More notification channels

## 👨‍💻 Author

Developed as a portfolio project to explore Python automation, web scraping, databases, data visualization, cloud deployment, and CI/CD.
