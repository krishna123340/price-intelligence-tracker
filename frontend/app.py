import os
import sys
import sqlite3
import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from dotenv import load_dotenv

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USERS_DATABASE = os.path.join(
    BASE_DIR,
    "users.db"
)

PRICE_DATABASE = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "prices.db"
    )
)

ENV_FILE = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        ".env"
    )
)


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv(ENV_FILE)


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_GBP_TO_INR = 128
DEFAULT_ALERT_THRESHOLD = 5

EMAIL_SENDER = os.getenv(
    "EMAIL_SENDER"
)

EMAIL_PASSWORD = os.getenv(
    "EMAIL_PASSWORD"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

WATCHLIST_DATABASE = os.path.join(
    BASE_DIR,
    "watchlist.db"
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Price Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

if "forgot_password" not in st.session_state:
    st.session_state.forgot_password = False

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False

if "reset_email" not in st.session_state:
    st.session_state.reset_email = ""

if "reset_otp" not in st.session_state:
    st.session_state.reset_otp = ""

if "otp_expiry" not in st.session_state:
    st.session_state.otp_expiry = None

if "otp_verified" not in st.session_state:
    st.session_state.otp_verified = False

if "theme" not in st.session_state:
    st.session_state.theme = "Midnight"

if "font" not in st.session_state:
    st.session_state.font = "Inter"

if "graph_type" not in st.session_state:
    st.session_state.graph_type = "Line"

if "wallpaper" not in st.session_state:
    st.session_state.wallpaper = "Premium Aurora"

if "gbp_to_inr" not in st.session_state:
    st.session_state.gbp_to_inr = DEFAULT_GBP_TO_INR

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = 60

if "alert_threshold" not in st.session_state:
    st.session_state.alert_threshold = DEFAULT_ALERT_THRESHOLD

if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []


# ============================================================
# WATCHLIST / SMART FEATURES
# ============================================================

def create_watchlist_table():

    db = sqlite3.connect(
        WATCHLIST_DATABASE
    )

    cursor = db.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            target_price REAL DEFAULT 0,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    db.commit()
    db.close()


def create_notifications_table():

    db = sqlite3.connect(WATCHLIST_DATABASE)
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            alert_type TEXT,
            product TEXT,
            message TEXT,
            alert_key TEXT UNIQUE,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


def add_notification(
    alert_type,
    product,
    message,
    alert_key
):

    user_email = st.session_state.get(
        "user_email",
        ""
    )

    if not user_email:
        return

    db = sqlite3.connect(WATCHLIST_DATABASE)
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO notifications
        (user_email, alert_type, product, message, alert_key, is_read)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
        (
            user_email,
            alert_type,
            product,
            message,
            f"{user_email}|{alert_key}"
        )
    )

    db.commit()
    db.close()


def get_notifications(unread_only=False):

    user_email = st.session_state.get(
        "user_email",
        ""
    )

    if not user_email:
        return pd.DataFrame(
            columns=[
                "id",
                "alert_type",
                "product",
                "message",
                "is_read",
                "created_at"
            ]
        )

    db = sqlite3.connect(WATCHLIST_DATABASE)

    query = """
        SELECT
            id,
            alert_type,
            product,
            message,
            is_read,
            created_at
        FROM notifications
        WHERE user_email = ?
    """

    params = [user_email]

    if unread_only:
        query += " AND is_read = 0"

    query += " ORDER BY datetime(created_at) DESC, id DESC"

    df = pd.read_sql_query(
        query,
        db,
        params=params
    )

    db.close()

    return df


def mark_notification_read(notification_id):

    db = sqlite3.connect(WATCHLIST_DATABASE)
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE id = ?
        """,
        (notification_id,)
    )

    db.commit()
    db.close()


def mark_all_notifications_read():

    user_email = st.session_state.get(
        "user_email",
        ""
    )

    if not user_email:
        return

    db = sqlite3.connect(WATCHLIST_DATABASE)
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE user_email = ?
        """,
        (user_email,)
    )

    db.commit()
    db.close()


def get_watchlist():

    db = sqlite3.connect(
        WATCHLIST_DATABASE
    )

    df = pd.read_sql_query(
        """
        SELECT *
        FROM watchlist
        ORDER BY added_at DESC
        """,
        db
    )

    db.close()

    return df


def normalize_product_url(url):

    """Normalize Books to Scrape product URLs to the /catalogue/ path."""

    url = (url or "").strip()

    if not url:
        return url

    if "books.toscrape.com" in url:
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)

        path = parsed.path

        if path.startswith("/catalogue/"):
            return urlunparse(parsed)

        if path.startswith("/"):
            path = path[1:]

        path = "catalogue/" + path

        return urlunparse((
            parsed.scheme or "https",
            parsed.netloc or "books.toscrape.com",
            "/" + path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    return url


def scrape_single_product(url):

    url = normalize_product_url(url)

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent":
                "PriceIntelligenceTracker/1.0"
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        title_tag = soup.find("h1")

        price_tag = soup.find(
            "p",
            class_="price_color"
        )

        if not title_tag or not price_tag:

            return (
                None,
                None,
                "Could not find product title/price."
            )

        title = title_tag.get_text(
            strip=True
        )

        price_text = (
            price_tag
            .get_text(strip=True)
            .replace("£", "")
            .replace("Â", "")
        )

        price = float(price_text)

        return (
            title,
            price,
            None
        )

    except Exception as error:

        return (
            None,
            None,
            str(error)
        )


def refresh_tracked_prices():
    """Scrape every product in the current user's watchlist and save a new history record."""
    watchlist = get_watchlist()

    if watchlist.empty:
        return 0, []

    db = sqlite3.connect(PRICE_DATABASE)
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prices (
            product TEXT,
            price REAL,
            date TEXT
        )
        """
    )

    refreshed = 0
    errors = []

    for _, item in watchlist.iterrows():
        title, price, error = scrape_single_product(item["url"])

        if error or price is None:
            errors.append(
                f"{item['product']}: {error or 'Price unavailable'}"
            )
            continue

        cursor.execute(
            """
            INSERT INTO prices (product, price, date)
            VALUES (?, ?, datetime('now', '+5 hours', '+30 minutes'))
            """,
            (title or item["product"], float(price))
        )
        refreshed += 1

    db.commit()
    db.close()

    # Keep the Notification Center synchronized with the newly stored prices.
    if refreshed:
        try:
            sync_alert_notifications()
        except Exception:
            pass

    return refreshed, errors


def add_product(
    url,
    target_price=0
):

    normalized_url = normalize_product_url(url)

    title, price, error = scrape_single_product(
        normalized_url
    )

    if error:

        return (
            False,
            error
        )

    db = sqlite3.connect(
        WATCHLIST_DATABASE
    )

    try:

        db.execute(
            """
            INSERT INTO watchlist
            (product, url, target_price)
            VALUES (?, ?, ?)
            """,
            (
                title,
                normalized_url,
                float(target_price or 0)
            )
        )

        db.commit()

    except sqlite3.IntegrityError:

        db.execute(
            """
            UPDATE watchlist
            SET product = ?,
                target_price = ?
            WHERE url = ?
            """,
            (
                title,
                float(target_price or 0),
                normalized_url
            )
        )

        db.commit()

    db.close()

    current_inr = (
        price *
        st.session_state.gbp_to_inr
    )

    return (
        True,
        f"{title} added. "
        f"Current price: ₹{current_inr:,.2f}"
    )


def remove_product(url):

    db = sqlite3.connect(
        WATCHLIST_DATABASE
    )

    db.execute(
        """
        DELETE FROM watchlist
        WHERE url = ?
        """,
        (url,)
    )

    db.commit()
    db.close()


def save_support_message(
    email,
    message
):

    db = sqlite3.connect(
        WATCHLIST_DATABASE
    )

    db.execute(
        """
        INSERT INTO support_messages
        (email, message)
        VALUES (?, ?)
        """,
        (
            email,
            message
        )
    )

    db.commit()
    db.close()


def get_price_status(
    product_df
):

    if product_df.empty:

        return (
            "No data",
            0
        )

    if len(product_df) < 2:

        return (
            "New",
            0
        )

    previous = float(
        product_df[
            "price_inr"
        ].iloc[-2]
    )

    latest = float(
        product_df[
            "price_inr"
        ].iloc[-1]
    )

    if previous == 0:

        return (
            "Stable",
            0
        )

    change = (
        (latest - previous)
        / previous
    ) * 100

    if change < 0:

        return (
            "Falling",
            change
        )

    if change > 0:

        return (
            "Rising",
            change
        )

    return (
        "Stable",
        0
    )


# ============================================================
# PRICE DATABASE
# ============================================================

def load_price_data():

    if not os.path.exists(
        PRICE_DATABASE
    ):

        return pd.DataFrame()

    try:

        db = sqlite3.connect(
            PRICE_DATABASE
        )

        df = pd.read_sql_query(
            """
            SELECT
                product,
                price,
                date
            FROM prices
            ORDER BY date ASC
            """,
            db
        )

        db.close()

        if df.empty:

            return df

        rate = st.session_state.get(
            "gbp_to_inr",
            DEFAULT_GBP_TO_INR
        )

        df["price_inr"] = (
            df["price"] * rate
        )

        df["date"] = pd.to_datetime(
            df["date"]
        )

        return df

    except Exception as error:

        st.error(
            "Unable to load price database: "
            + str(error)
        )

        return pd.DataFrame()


# ============================================================
# PRODUCT SUMMARY
# ============================================================

def get_product_summary(df):

    if df.empty:

        return pd.DataFrame()

    summary = (
        df.groupby("product")
        .agg(
            current_price=(
                "price_inr",
                "last"
            ),
            lowest_price=(
                "price_inr",
                "min"
            ),
            average_price=(
                "price_inr",
                "mean"
            ),
            records=(
                "price_inr",
                "count"
            )
        )
        .reset_index()
    )

    return summary

    # ============================================================
# USER DATABASE
# ============================================================

def create_users_table():

    db = sqlite3.connect(
        USERS_DATABASE
    )

    cursor = db.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    db.commit()
    db.close()


# ============================================================
# PASSWORD HASH
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# CREATE ACCOUNT
# ============================================================

def create_account(
    name,
    email,
    password
):

    db = sqlite3.connect(
        USERS_DATABASE
    )

    cursor = db.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                hash_password(password)
            )
        )

        db.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        db.close()


# ============================================================
# LOGIN
# ============================================================

def login_user(
    email,
    password
):

    db = sqlite3.connect(
        USERS_DATABASE
    )

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT name, email
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email,
            hash_password(password)
        )
    )

    user = cursor.fetchone()

    db.close()

    return user


# ============================================================
# CHECK EMAIL
# ============================================================

def email_exists(email):

    db = sqlite3.connect(
        USERS_DATABASE
    )

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    result = cursor.fetchone()

    db.close()

    return result is not None


# ============================================================
# UPDATE PASSWORD
# ============================================================

def update_password(
    email,
    new_password
):

    db = sqlite3.connect(
        USERS_DATABASE
    )

    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password = ?
        WHERE email = ?
        """,
        (
            hash_password(new_password),
            email
        )
    )

    db.commit()
    db.close()


# ============================================================
# GENERATE OTP
# ============================================================

def generate_otp():

    return str(
        secrets.randbelow(900000) + 100000
    )


# ============================================================
# SEND OTP EMAIL
# ============================================================

def send_otp_email(
    email,
    otp
):

    if not EMAIL_SENDER or not EMAIL_PASSWORD:

        return False

    message = EmailMessage()

    message["Subject"] = (
        "Price Intelligence - Password Reset OTP"
    )

    message["From"] = EMAIL_SENDER
    message["To"] = email

    message.set_content(
        f"""
Price Intelligence

Your password reset OTP is:

{otp}

This OTP is valid for 10 minutes.

If you did not request this password reset,
you can safely ignore this email.
"""
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

            server.send_message(
                message
            )

        return True

    except Exception as error:

        print(
            "OTP error:",
            error
        )

        return False


# ============================================================
# LOGIN PAGE
# ============================================================
def load_css():

    st.markdown(
        """
        <style>

        .stApp {
            background:
                radial-gradient(
                    circle at top left,
                    rgba(90, 70, 180, 0.25),
                    transparent 35%
                ),
                radial-gradient(
                    circle at bottom right,
                    rgba(20, 120, 180, 0.20),
                    transparent 35%
                ),
                #070b14;
        }

        .brand {
            text-align: center;
            margin-top: 35px;
            margin-bottom: 30px;
        }

        .brand-icon {
            font-size: 42px;
            margin-bottom: 8px;
        }

        .brand-name {
            font-size: 30px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }

        .brand-sub {
            color: #9ca3af;
            font-size: 14px;
            margin-top: 6px;
        }

        .dashboard-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .dashboard-subtitle {
            color: #9ca3af;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 21px;
            font-weight: 650;
            margin-top: 15px;
            margin-bottom: 15px;
        }

        [data-testid="stSidebar"] {
            background: rgba(10, 14, 25, 0.95);
        }

        </style>
        """,
        unsafe_allow_html=True
    )

def show_login():

    load_css()

    st.markdown(
        """
<div class="brand">
    <div class="brand-icon">💎</div>
    <div class="brand-name">
        Price Intelligence
    </div>
    <div class="brand-sub">
        Smart price tracking powered by AI
    </div>
</div>
        """,
        unsafe_allow_html=True
    )

    login_tab, signup_tab = st.tabs(
        [
            "🔐 Login",
            "✨ Create Account"
        ]
    )

    # ========================================================
    # LOGIN
    # ========================================================

    with login_tab:

        email = st.text_input(
            "Email",
            key="login_email",
            placeholder="Enter your email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
            placeholder="Enter your password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            user = login_user(
                email.strip().lower(),
                password
            )

            if user:

                st.session_state.logged_in = True

                st.session_state.user_name = (
                    user[0]
                )

                st.session_state.user_email = (
                    user[1]
                )

                st.rerun()

            else:

                st.error(
                    "Invalid email or password."
                )

        if st.button(
            "Forgot Password?",
            use_container_width=True
        ):

            st.session_state.forgot_password = True

            st.session_state.otp_sent = False

            st.session_state.otp_verified = False

            st.session_state.reset_email = ""

            st.session_state.reset_otp = ""

            st.session_state.otp_expiry = None

            st.rerun()


    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    with signup_tab:

        name = st.text_input(
            "Full Name",
            key="signup_name",
            placeholder="Enter your name"
        )

        email = st.text_input(
            "Email",
            key="signup_email",
            placeholder="Enter your email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="signup_password",
            placeholder="Create a password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm",
            placeholder="Confirm your password"
        )

        if st.button(
            "Create Account",
            use_container_width=True
        ):

            name = name.strip()

            email = (
                email
                .strip()
                .lower()
            )

            if (
                not name
                or not email
                or not password
            ):

                st.error(
                    "Please fill all fields."
                )

            elif password != confirm_password:

                st.error(
                    "Passwords do not match."
                )

            elif create_account(
                name,
                email,
                password
            ):

                st.success(
                    "Account created successfully! "
                    "You can now login."
                )

            else:

                st.error(
                    "An account with this email "
                    "already exists."
                )


# ============================================================
# FORGOT PASSWORD
# ============================================================

def show_forgot_password():

    load_css()

    st.markdown(
        """
<div class="brand">
    <div class="brand-icon">🔐</div>
    <div class="brand-name">
        Reset Password
    </div>
    <div class="brand-sub">
        Verify your email to reset your password
    </div>
</div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # SEND OTP
    # ========================================================

    if not st.session_state.otp_sent:

        email = st.text_input(
            "Email Address",
            placeholder="Enter your registered email"
        )

        if st.button(
            "Send OTP",
            use_container_width=True
        ):

            email = email.strip().lower()

            if not email:

                st.error(
                    "Please enter your email."
                )

            elif not email_exists(email):

                st.error(
                    "No account found with this email."
                )

            else:

                otp = generate_otp()

                sent = send_otp_email(
                    email,
                    otp
                )

                if sent:

                    st.session_state.reset_email = email

                    st.session_state.reset_otp = otp

                    st.session_state.otp_expiry = (
                        datetime.now()
                        + timedelta(minutes=10)
                    )

                    st.session_state.otp_sent = True

                    st.success(
                        "OTP sent successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Could not send OTP. "
                        "Check your email configuration."
                    )


        if st.button(
            "← Back to Login",
            use_container_width=True
        ):

            st.session_state.forgot_password = False

            st.session_state.otp_sent = False

            st.session_state.otp_verified = False

            st.rerun()


    # ========================================================
    # VERIFY OTP
    # ========================================================

    else:

        st.info(
            f"OTP sent to "
            f"{st.session_state.reset_email}"
        )

        otp = st.text_input(
            "Enter 6-digit OTP",
            max_chars=6,
            placeholder="123456"
        )


        if not st.session_state.otp_verified:

            if st.button(
                "Verify OTP",
                use_container_width=True
            ):

                if (
                    st.session_state.otp_expiry
                    and datetime.now()
                    > st.session_state.otp_expiry
                ):

                    st.error(
                        "OTP has expired. "
                        "Please request a new OTP."
                    )

                    st.session_state.otp_sent = False

                elif otp == st.session_state.reset_otp:

                    st.session_state.otp_verified = True

                    st.success(
                        "OTP verified successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        "Invalid OTP."
                    )


        # ====================================================
        # NEW PASSWORD
        # ====================================================

        else:

            st.success(
                "Email verified. "
                "You can now create a new password."
            )

            new_password = st.text_input(
                "New Password",
                type="password",
                placeholder="Enter new password"
            )

            confirm_new_password = st.text_input(
                "Confirm New Password",
                type="password",
                placeholder="Confirm new password"
            )

            if st.button(
                "Reset Password",
                use_container_width=True
            ):

                if not new_password:

                    st.error(
                        "Please enter a new password."
                    )

                elif new_password != confirm_new_password:

                    st.error(
                        "Passwords do not match."
                    )

                elif len(new_password) < 6:

                    st.error(
                        "Password must contain at least "
                        "6 characters."
                    )

                else:

                    update_password(
                        st.session_state.reset_email,
                        new_password
                    )

                    st.success(
                        "🎉 Password reset successfully! "
                        "You can now login."
                    )

                    st.session_state.forgot_password = False

                    st.session_state.otp_sent = False

                    st.session_state.otp_verified = False

                    st.session_state.reset_email = ""

                    st.session_state.reset_otp = ""

                    st.session_state.otp_expiry = None


# ============================================================
# SIDEBAR
# ============================================================

def show_sidebar():

    load_css()

    with st.sidebar:

        st.markdown(
            """
<div class="sidebar-brand">
    <div class="sidebar-icon">💎</div>
    <div class="sidebar-title">
        Price Intelligence
    </div>
    <div class="sidebar-subtitle">
        AI Price Tracking
    </div>
</div>
            """,
            unsafe_allow_html=True
        )

        st.divider()

        st.markdown(
            f"👋 **{st.session_state.user_name}**"
        )

        st.caption(
            st.session_state.user_email
        )

        st.divider()

        st.subheader("Navigation")

        page = st.radio(
            "Go to",
            [
                "🏠 Home",
                "🔍 Search & Add",
                "📦 Tracked Products",
                "📋 Product Details",
                "🏆 Best Deals",
                "🔔 Notifications",
                "🤖 AI Assistant",
                "📊 Analytics",
                "🚨 Alerts",
                "💬 Support",
                "⚙️ Settings"
            ],
            label_visibility="collapsed"
        )

        st.divider()

        if st.button(
            "🚪 Logout",
            use_container_width=True
        ):

            st.session_state.logged_in = False

            st.session_state.user_name = ""

            st.session_state.user_email = ""

            st.rerun()

    return page

    # ============================================================
# HOME DASHBOARD
# ============================================================

def show_home():

    st.markdown(
        '<div class="dashboard-title">🏠 Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle"'
        '>Monitor prices, trends and smart buying opportunities.'
        '</div>',
        unsafe_allow_html=True
    )

    refresh_col1, refresh_col2 = st.columns([1, 3])

    with refresh_col1:
        if st.button(
            "🔄 Refresh Prices Now",
            use_container_width=True,
            type="primary",
            key="home_refresh_prices"
        ):
            with st.spinner("Fetching latest prices..."):
                refreshed, errors = refresh_tracked_prices()

            if refreshed:
                st.success(
                    f"✅ Updated {refreshed} tracked product(s) and added new history records."
                )
            else:
                st.warning(
                    "No tracked prices could be refreshed right now."
                )

            if errors:
                for error in errors:
                    st.caption(f"⚠️ {error}")

            st.rerun()

    with refresh_col2:
        st.caption(
            "Manual refresh scrapes the tracked demo products and stores a new timestamped price-history record."
        )

    df = load_price_data()

    if df.empty:

        st.info(
            "No price data is available yet."
        )

        return

    summary = get_product_summary(df)

    if summary.empty:

        st.info(
            "No tracked products found."
        )

        return

    # ========================================================
    # PRODUCT SELECTOR
    # ========================================================

    products = summary["product"].tolist()

    selected_product = st.selectbox(
        "Select Product",
        products
    )

    product_df = df[
        df["product"] == selected_product
    ].copy()

    product_df = product_df.sort_values(
        "date"
    )

    latest_price = float(
        product_df["price_inr"].iloc[-1]
    )

    lowest_price = float(
        product_df["price_inr"].min()
    )

    average_price = float(
        product_df["price_inr"].mean()
    )

    records = len(product_df)

    status, change = get_price_status(
        product_df
    )

    # ========================================================
    # METRICS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Current Price",
            f"₹{latest_price:,.2f}"
        )

    with col2:

        st.metric(
            "Lowest Price",
            f"₹{lowest_price:,.2f}"
        )

    with col3:

        st.metric(
            "Average Price",
            f"₹{average_price:,.2f}"
        )

    with col4:

        st.metric(
            "Price Trend",
            status,
            f"{change:+.2f}%"
        )

    st.divider()

    # ========================================================
    # PRICE HISTORY
    # ========================================================

    st.markdown(
        '<div class="section-title">📈 Price History</div>',
        unsafe_allow_html=True
    )

    chart_df = product_df[
        ["date", "price_inr"]
    ].copy()

    chart_df = chart_df.set_index(
        "date"
    )

    if st.session_state.graph_type == "Bar":

        st.bar_chart(
            chart_df["price_inr"]
        )

    elif st.session_state.graph_type == "Area":

        st.area_chart(
            chart_df["price_inr"]
        )

    else:

        st.line_chart(
            chart_df["price_inr"]
        )

    # ========================================================
    # PRICE ANALYSIS
    # ========================================================

    st.markdown(
        '<div class="section-title">💡 Smart Price Insight</div>',
        unsafe_allow_html=True
    )

    if latest_price <= lowest_price:

        st.success(
            "🔥 Current price is the lowest "
            "recorded price for this product."
        )

    elif latest_price < average_price:

        st.success(
            "💚 Current price is below "
            "the historical average."
        )

    elif latest_price > average_price:

        st.warning(
            "⚠️ Current price is above "
            "the historical average."
        )

    else:

        st.info(
            "➡️ Current price is close to "
            "the historical average."
        )

    # ========================================================
    # BASIC BUYING ADVICE
    # ========================================================

    difference = (
        latest_price - average_price
    )

    if average_price > 0:

        difference_percent = (
            difference / average_price
        ) * 100

    else:

        difference_percent = 0

    if difference_percent <= -5:

        st.success(
            "🟢 Good buying opportunity: "
            "the current price is at least "
            "5% below its historical average."
        )

    elif difference_percent >= 5:

        target = (
            latest_price * 0.95
        )

        st.info(
            f"⏳ Consider waiting for a better deal. "
            f"A 5% lower target would be around "
            f"₹{target:,.2f}."
        )

    else:

        st.info(
            "🟡 The current price is close to "
            "its historical average."
        )

    st.caption(
        f"Tracking records: {records}"
    )


# ============================================================
# PRODUCT SEARCH
# ============================================================

@st.cache_data(ttl=600, show_spinner=False)
def search_books_catalog(query, max_pages=10):
    """Search the permitted Books to Scrape catalog."""

    query = query.strip().lower()

    if not query:
        return []

    base_url = "https://books.toscrape.com/"
    catalogue_base = "https://books.toscrape.com/catalogue/"
    results = []

    for page_number in range(1, max_pages + 1):

        page_url = (
            f"https://books.toscrape.com/catalogue/"
            f"page-{page_number}.html"
        )

        try:
            response = requests.get(
                page_url,
                timeout=10,
                headers={
                    "User-Agent":
                    "PriceIntelligenceTracker/1.0"
                }
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for card in soup.select("article.product_pod"):

            title_tag = card.select_one("h3 a")
            price_tag = card.select_one("p.price_color")

            if not title_tag or not price_tag:
                continue

            title = title_tag.get("title") or title_tag.get_text(strip=True)
            title = title.strip()

            if query not in title.lower():
                continue

            price_text = (
                price_tag.get_text(strip=True)
                .replace("£", "")
                .replace("Â", "")
                .strip()
            )

            try:
                price_gbp = float(price_text)
            except ValueError:
                continue

            href = title_tag.get("href", "").strip()
            if not href:
                continue

            if href.startswith("http://") or href.startswith("https://"):
                product_url = href
            else:
                # Books to Scrape uses relative product links.
                # Force them into the valid /catalogue/ path.
                product_url = urljoin(catalogue_base, href.lstrip("/"))
                product_url = normalize_product_url(product_url)

            results.append({
                "title": title,
                "price_gbp": price_gbp,
                "url": product_url
            })

    return results


def show_search_add():

    load_css()

    st.markdown(
        '<div class="dashboard-title">'
        '🔍 Search & Add Products'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Search the permitted demo catalog, compare prices and add products to your watchlist.'
        '</div>',
        unsafe_allow_html=True
    )

    st.info(
        "🔎 Product search currently uses Books to Scrape for permitted testing. "
        "The app does not bypass CAPTCHA or anti-bot protection."
    )

    # ========================================================
    # SEARCH CONTROLS
    # ========================================================

    search_col, page_col, sort_col = st.columns([3, 1, 1])

    with search_col:
        query = st.text_input(
            "Search products",
            placeholder="Try: light, velvet, sharp...",
            key="product_search_query"
        )

    with page_col:
        search_pages = st.selectbox(
            "Search depth",
            [3, 5, 10],
            index=1,
            format_func=lambda x: f"{x} pages",
            key="search_depth"
        )

    with sort_col:
        sort_option = st.selectbox(
            "Sort results",
            [
                "Relevance",
                "Price: Low to High",
                "Price: High to Low",
                "Name: A to Z"
            ],
            key="search_sort"
        )

    search_button = st.button(
        "🔍 Search Products",
        use_container_width=True,
        type="primary",
        key="search_products_button"
    )

    if search_button:

        if not query.strip():
            st.warning("Please enter a product name to search.")
        else:
            with st.spinner("Searching permitted product pages..."):
                results = search_books_catalog(
                    query,
                    search_pages
                )

            st.session_state.search_results = results
            st.session_state.search_query_used = query.strip()

    # ========================================================
    # RESULTS
    # ========================================================

    results = st.session_state.get(
        "search_results",
        []
    )

    if results:

        if sort_option == "Price: Low to High":
            results = sorted(
                results,
                key=lambda item: item["price_gbp"]
            )
        elif sort_option == "Price: High to Low":
            results = sorted(
                results,
                key=lambda item: item["price_gbp"],
                reverse=True
            )
        elif sort_option == "Name: A to Z":
            results = sorted(
                results,
                key=lambda item: item["title"].lower()
            )

        st.subheader(
            f"📚 Results ({len(results)})"
        )

        watchlist = get_watchlist()
        tracked_urls = set(
            watchlist["url"].tolist()
        ) if not watchlist.empty else set()

        for index, product in enumerate(results):

            price_gbp = float(
                product["price_gbp"]
            )

            price_inr = (
                price_gbp
                * st.session_state.gbp_to_inr
            )

            is_tracked = product["url"] in tracked_urls

            st.markdown("---")

            result_col, action_col = st.columns([4, 1.5])

            with result_col:
                st.markdown(
                    f"### {product['title']}"
                )

                st.write(
                    f"💷 **£{price_gbp:.2f}**  "
                    f"≈ **₹{price_inr:,.2f}**"
                )

                if is_tracked:
                    st.success(
                        "✅ Already in your watchlist"
                    )

                st.caption(
                    product["url"]
                )

            with action_col:

                target_price = st.number_input(
                    "Target (£)",
                    min_value=0.0,
                    value=0.0,
                    step=1.0,
                    key=f"search_target_{index}"
                )

                button_label = (
                    "🔄 Update"
                    if is_tracked
                    else "➕ Add"
                )

                if st.button(
                    button_label,
                    use_container_width=True,
                    key=f"search_add_{index}"
                ):

                    ok, message = add_product(
                        product["url"],
                        target_price
                    )

                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(
                            f"Could not add product: {message}"
                        )

    elif search_button:
        st.warning(
            "No matching products found in the searched catalog pages."
        )

    # ========================================================
    # SEARCH AGAIN / CLEAR
    # ========================================================

    if results and st.button(
        "🧹 Clear Search Results",
        key="clear_search_results"
    ):
        st.session_state.search_results = []
        st.session_state.search_query_used = ""
        st.rerun()

    st.divider()

    # ========================================================
    # DIRECT URL FALLBACK
    # ========================================================

    st.subheader(
        "🔗 Add by Product URL"
    )

    st.caption(
        "Use this when you already know the permitted product page URL."
    )

    direct_url = st.text_input(
        "Product URL",
        placeholder=(
            "https://books.toscrape.com/catalogue/..."
        ),
        key="direct_product_url"
    )

    direct_target = st.number_input(
        "Target Price (GBP, optional)",
        min_value=0.0,
        value=0.0,
        step=1.0,
        key="direct_target_price"
    )

    if st.button(
        "➕ Add / Update Product",
        use_container_width=True,
        key="direct_add_product"
    ):

        if not direct_url.strip():
            st.error(
                "Please enter a product URL."
            )
        else:
            with st.spinner("Checking product page..."):
                ok, message = add_product(
                    direct_url,
                    direct_target
                )

            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(
                    f"Could not add product: {message}"
                )

    # ========================================================
    # CURRENT WATCHLIST
    # ========================================================

    st.divider()

    st.subheader(
        "📋 Your Watchlist"
    )

    watchlist = get_watchlist()

    if watchlist.empty:
        st.info(
            "No products added yet. Search above to start tracking products."
        )
        return

    for _, row in watchlist.iterrows():

        c1, c2 = st.columns([4, 1])

        with c1:
            target = float(
                row["target_price"] or 0
            )

            target_text = (
                f" • 🎯 Target £{target:,.2f}"
                if target > 0
                else ""
            )

            st.write(
                f"**{row['product']}**"
                f"{target_text}"
            )

            st.caption(
                row["url"]
            )

        with c2:
            if st.button(
                "🗑️ Remove",
                key=f"remove_{row['id']}"
            ):
                remove_product(
                    row["url"]
                )
                st.success(
                    "Product removed."
                )
                st.rerun()


# ============================================================
# SMART DEAL SCORE
# ============================================================

def calculate_deal_score(
    current_price,
    average_price,
    lowest_price,
    recent_change_percent,
    target_price=0
):
    score = 50

    if average_price > 0:
        difference = ((average_price - current_price) / average_price) * 100
        if difference >= 20:
            score += 25
        elif difference >= 10:
            score += 15
        elif difference >= 5:
            score += 8
        elif difference < 0:
            score -= 15

    if lowest_price > 0:
        difference = ((current_price - lowest_price) / lowest_price) * 100
        if difference <= 5:
            score += 15
        elif difference <= 10:
            score += 8
        elif difference >= 30:
            score -= 10

    if recent_change_percent < -5:
        score += 10
    elif recent_change_percent < 0:
        score += 5
    elif recent_change_percent > 5:
        score -= 10

    if target_price > 0:
        if current_price <= target_price:
            score += 15
        elif current_price <= target_price * 1.05:
            score += 5
        elif current_price > target_price * 1.20:
            score -= 10

    score = max(0, min(100, round(score)))

    if score >= 80:
        label = "🟢 Excellent Deal"
        advice = "BUY"
    elif score >= 65:
        label = "🟢 Good Deal"
        advice = "CONSIDER"
    elif score >= 45:
        label = "🟡 Fair Price"
        advice = "CONSIDER"
    else:
        label = "🔴 Poor Deal"
        advice = "WAIT"

    return score, label, advice


# ============================================================
# TRACKED PRODUCTS
# ============================================================

def show_tracked_products():

    load_css()

    st.markdown(
        '<div class="dashboard-title">'
        '📦 Tracked Products'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Track your products and understand whether the current price is a good deal.'
        '</div>',
        unsafe_allow_html=True
    )

    df = load_price_data()

    if df.empty:
        st.info("No tracked price data available.")
        return

    summary = get_product_summary(df)

    if summary.empty:
        st.info("No products found.")
        return

    watchlist = get_watchlist()

    for _, row in summary.iterrows():

        product_name = row["product"]
        current_price = float(row["current_price"])
        lowest_price = float(row["lowest_price"])
        average_price = float(row["average_price"])
        records = int(row["records"])

        product_history = df[
            df["product"] == product_name
        ].sort_values("date")

        if len(product_history) >= 2:
            previous_price = float(
                product_history["price_inr"].iloc[-2]
            )
            if previous_price != 0:
                recent_change = (
                    (current_price - previous_price)
                    / previous_price
                ) * 100
            else:
                recent_change = 0
        else:
            recent_change = 0

        target_price = 0

        if not watchlist.empty:
            matching = watchlist[
                watchlist["product"] == product_name
            ]

            if not matching.empty:
                target_gbp = float(
                    matching.iloc[0]["target_price"] or 0
                )

                if target_gbp > 0:
                    target_price = (
                        target_gbp
                        * st.session_state.gbp_to_inr
                    )

        score, deal_label, advice = calculate_deal_score(
            current_price,
            average_price,
            lowest_price,
            recent_change,
            target_price
        )

        st.markdown("---")
        st.markdown(f"### 📚 {product_name}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Current Price",
                f"₹{current_price:,.2f}"
            )

        with col2:
            st.metric(
                "Historical Average",
                f"₹{average_price:,.2f}"
            )

        with col3:
            st.metric(
                "Lowest Price",
                f"₹{lowest_price:,.2f}"
            )

        with col4:
            st.metric(
                "Price Records",
                records
            )

        st.markdown(
            f"### 🧠 Smart Deal Score: {score}/100"
        )

        st.progress(score / 100)

        if advice == "BUY":
            st.success(
                f"{deal_label}  •  **{advice}**"
            )
        elif advice == "CONSIDER":
            st.warning(
                f"{deal_label}  •  **{advice}**"
            )
        else:
            st.error(
                f"{deal_label}  •  **{advice}**"
            )

        if recent_change < 0:
            st.write(
                f"📉 Recent price movement: "
                f"**{abs(recent_change):.2f}% decrease**"
            )
        elif recent_change > 0:
            st.write(
                f"📈 Recent price movement: "
                f"**{recent_change:.2f}% increase**"
            )
        else:
            st.write(
                "➡️ Recent price movement: **Stable**"
            )

        if target_price > 0:
            if current_price <= target_price:
                st.success(
                    f"🎯 Target price reached! "
                    f"Current: ₹{current_price:,.2f} "
                    f"• Target: ₹{target_price:,.2f}"
                )
            else:
                difference = current_price - target_price
                st.info(
                    f"🎯 Target: ₹{target_price:,.2f} "
                    f"• Current price is "
                    f"₹{difference:,.2f} above target."
                )
        else:
            st.caption(
                "🎯 No target price set for this product."
            )

        if current_price <= lowest_price:
            st.success(
                "🔥 Current price is at the "
                "lowest recorded level."
            )
        elif current_price < average_price:
            st.success(
                "💚 Current price is below "
                "the historical average."
            )
        elif current_price > average_price:
            st.warning(
                "⚠️ Current price is above "
                "the historical average."
            )
        else:
            st.info(
                "➡️ Current price is around "
                "the historical average."
            )


# ============================================================
# AI PRICE ASSISTANT
# ============================================================

def ai_welcome_reply(message):

    text = message.strip()

    if not text:

        return (
            "Please ask me something about "
            "your tracked products."
        )

    # ========================================================
    # LOAD REAL PRICE DATA
    # ========================================================

    df = load_price_data()

    lower = text.lower()

    matched_product = None

    if not df.empty:

        product_names = (
            df["product"]
            .dropna()
            .unique()
            .tolist()
        )

        # Exact / partial product matching

        for product_name in product_names:

            product_lower = (
                product_name.lower()
            )

            if product_lower in lower:

                matched_product = product_name

                break

        # Word-based fallback

        if matched_product is None:

            words = [
                word.strip(
                    ".,?!"
                )
                for word in lower.split()
                if len(word) >= 4
            ]

            best_match = None
            best_score = 0

            for product_name in product_names:

                product_words = set(
                    product_name.lower().split()
                )

                score = sum(
                    1
                    for word in words
                    if word in product_words
                )

                if score > best_score:

                    best_score = score

                    best_match = product_name

            if best_score >= 2:

                matched_product = best_match


    # ========================================================
    # PRICE QUESTION
    # ========================================================

    price_keywords = [
        "price",
        "cost",
        "current",
        "latest",
        "how much",
        "buy"
    ]

    asks_price = any(
        keyword in lower
        for keyword in price_keywords
    )

    if matched_product and asks_price:

        product_df = df[
            df["product"]
            == matched_product
        ].sort_values(
            "date"
        )

        latest = float(
            product_df[
                "price_inr"
            ].iloc[-1]
        )

        lowest = float(
            product_df[
                "price_inr"
            ].min()
        )

        average = float(
            product_df[
                "price_inr"
            ].mean()
        )

        status, change = get_price_status(
            product_df
        )

        return (
            f"💰 **{matched_product}**\n\n"
            f"Current price: "
            f"₹{latest:,.2f}\n\n"
            f"Lowest recorded price: "
            f"₹{lowest:,.2f}\n\n"
            f"Historical average: "
            f"₹{average:,.2f}\n\n"
            f"Trend: {status} "
            f"({change:+.2f}%)"
        )


    # ========================================================
    # GENERAL PRODUCT QUESTION
    # ========================================================

    if matched_product:

        product_df = df[
            df["product"]
            == matched_product
        ].sort_values(
            "date"
        )

        latest = float(
            product_df[
                "price_inr"
            ].iloc[-1]
        )

        lowest = float(
            product_df[
                "price_inr"
            ].min()
        )

        average = float(
            product_df[
                "price_inr"
            ].mean()
        )

        status, change = get_price_status(
            product_df
        )

        context = (
            f"Tracked product: {matched_product}\n"
            f"Current price: ₹{latest:,.2f}\n"
            f"Lowest price: ₹{lowest:,.2f}\n"
            f"Average price: ₹{average:,.2f}\n"
            f"Trend: {status}\n"
            f"Change: {change:+.2f}%"
        )

    else:

        context = (
            "No specific product was matched."
        )


    # ========================================================
    # OPENAI RESPONSE
    # ========================================================

    if OPENAI_API_KEY and OpenAI:

        try:

            client = OpenAI(
                api_key=OPENAI_API_KEY
            )

            response = client.responses.create(
                model="gpt-5.6-luna",
                input=(
                    "You are the AI assistant inside "
                    "Price Intelligence Tracker.\n\n"
                    "Help the user understand tracked "
                    "products, prices, trends, alerts, "
                    "analytics and settings.\n\n"
                    "Use the database context below when "
                    "answering product questions.\n\n"
                    f"DATABASE CONTEXT:\n{context}\n\n"
                    f"USER MESSAGE:\n{text}\n\n"
                    "Reply briefly, clearly and naturally. "
                    "Do not invent prices."
                )
            )

            answer = (
                response
                .output_text
                .strip()
            )

            if answer:

                return answer

        except Exception as error:

            print(
                "AI error:",
                error
            )


    # ========================================================
    # LOCAL FALLBACK
    # ========================================================

    if (
        "hello" in lower
        or "hi" in lower
        or lower == "hey"
    ):

        return (
            "Hi! 👋 I can help you with "
            "prices, alerts, products, "
            "analytics and settings."
        )

    if "alert" in lower:

        return (
            "🔔 Alerts notify you when a "
            "tracked price drops enough "
            "to cross your configured threshold."
        )

    if (
        "product" in lower
        or "track" in lower
    ):

        return (
            "📦 Use Search & Add to start "
            "monitoring a permitted product page."
        )

    if "price" in lower:

        return (
            "💰 I can check the price of a "
            "product already available in "
            "your price database."
        )

    return (
        "🤖 I can help with products, "
        "prices, alerts, analytics and "
        "settings. What would you like to know?"
    )


# ============================================================
# PRODUCT DETAILS PAGE
# ============================================================

def show_product_details():

    load_css()

    st.markdown(
        '<div class="dashboard-title">📋 Product Details</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Explore detailed price history, statistics, target price and deal quality for a tracked product.'
        '</div>',
        unsafe_allow_html=True
    )

    df = load_price_data()

    if df.empty:
        st.info("No tracked price data available.")
        return

    products = df["product"].dropna().drop_duplicates().tolist()

    if not products:
        st.info("No products found.")
        return

    selected_product = st.selectbox(
        "Select product",
        products,
        key="product_details_selector"
    )

    product_df = df[df["product"] == selected_product].copy()
    product_df = product_df.sort_values("date")

    if product_df.empty:
        st.info("No history available for this product.")
        return

    current_price = float(product_df["price_inr"].iloc[-1])
    lowest_price = float(product_df["price_inr"].min())
    highest_price = float(product_df["price_inr"].max())
    average_price = float(product_df["price_inr"].mean())
    records = len(product_df)

    if records >= 2:
        previous_price = float(product_df["price_inr"].iloc[-2])
        if previous_price != 0:
            recent_change = ((current_price - previous_price) / previous_price) * 100
        else:
            recent_change = 0
    else:
        recent_change = 0

    target_price = 0
    watchlist = get_watchlist()

    if not watchlist.empty:
        matching = watchlist[watchlist["product"] == selected_product]
        if not matching.empty:
            target_gbp = float(matching.iloc[0]["target_price"] or 0)
            if target_gbp > 0:
                target_price = target_gbp * st.session_state.gbp_to_inr

    score, deal_label, advice = calculate_deal_score(
        current_price,
        average_price,
        lowest_price,
        recent_change,
        target_price
    )

    st.divider()
    st.markdown(f"### 📚 {selected_product}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Current Price", f"₹{current_price:,.2f}")
    with c2:
        st.metric("Lowest Price", f"₹{lowest_price:,.2f}")
    with c3:
        st.metric("Average Price", f"₹{average_price:,.2f}")
    with c4:
        st.metric("Highest Price", f"₹{highest_price:,.2f}")

    st.markdown(f"### 🧠 Smart Deal Score: {score}/100")
    st.progress(score / 100)

    if advice == "BUY":
        st.success(f"{deal_label} • **{advice}**")
    elif advice == "CONSIDER":
        st.warning(f"{deal_label} • **{advice}**")
    else:
        st.error(f"{deal_label} • **{advice}**")

    if recent_change < 0:
        st.write(f"📉 Recent movement: **{abs(recent_change):.2f}% decrease**")
    elif recent_change > 0:
        st.write(f"📈 Recent movement: **{recent_change:.2f}% increase**")
    else:
        st.write("➡️ Recent movement: **Stable**")

    if target_price > 0:
        if current_price <= target_price:
            st.success(
                f"🎯 Target reached • Current ₹{current_price:,.2f} • Target ₹{target_price:,.2f}"
            )
        else:
            st.info(
                f"🎯 Target ₹{target_price:,.2f} • "
                f"₹{current_price - target_price:,.2f} above target"
            )
    else:
        st.caption("🎯 No target price set for this product.")

    st.divider()
    st.subheader("📈 Price History")

    history_chart = product_df[["date", "price_inr"]].copy()
    history_chart["date"] = pd.to_datetime(history_chart["date"])
    history_chart = history_chart.set_index("date")
    history_chart.columns = ["Price (INR)"]

    st.line_chart(history_chart, use_container_width=True)

    st.subheader("📊 Price Statistics")

    stat1, stat2, stat3 = st.columns(3)

    with stat1:
        st.metric("Price Records", records)
    with stat2:
        st.metric("Distance from Lowest", f"₹{current_price - lowest_price:,.2f}")
    with stat3:
        st.metric("Difference vs Average", f"₹{current_price - average_price:,.2f}")

    st.subheader("🕒 Recent Price Records")

    # load_price_data() keeps the original GBP value in the `price` column.
    # The old version incorrectly expected a `price_gbp` column, which caused
    # KeyError: ["price_gbp"] not in index.
    recent_history = product_df[["date", "price", "price_inr"]].sort_values(
        "date", ascending=False
    ).head(10).copy()

    recent_history["price"] = recent_history["price"].map(
        lambda x: f"£{float(x):,.2f}"
    )
    recent_history["price_inr"] = recent_history["price_inr"].map(
        lambda x: f"₹{float(x):,.2f}"
    )

    recent_history.columns = ["Date", "Price (GBP)", "Price (INR)"]

    st.dataframe(recent_history, use_container_width=True, hide_index=True)


# ============================================================
# BEST DEALS PAGE
# ============================================================

def show_best_deals():

    st.markdown(
        '<div class="dashboard-title">🏆 Best Deals</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Rank your tracked products by Smart Deal Score and find better buying opportunities.'
        '</div>',
        unsafe_allow_html=True
    )

    df = load_price_data()

    if df.empty:
        st.info("No price data available yet. Add products and collect price history first.")
        return

    summary = get_product_summary(df)

    if summary.empty:
        st.info("No tracked products found.")
        return

    watchlist = get_watchlist()
    target_map = {}

    if not watchlist.empty:
        for _, item in watchlist.iterrows():
            target_map[item["product"]] = float(item["target_price"] or 0)

    deals = []

    for _, row in summary.iterrows():
        product_name = row["product"]
        current = float(row["current_price"])
        average = float(row["average_price"])
        lowest = float(row["lowest_price"])

        history = df[df["product"] == product_name].sort_values("date")
        previous = float(history["price_inr"].iloc[-2]) if len(history) >= 2 else current
        recent_change = ((current - previous) / previous) * 100 if previous else 0
        target = target_map.get(product_name, 0)

        score, label, action = calculate_deal_score(
            current_price=current,
            average_price=average,
            lowest_price=lowest,
            recent_change_percent=recent_change,
            target_price=target
        )

        deals.append({
            "product": product_name,
            "current": current,
            "average": average,
            "lowest": lowest,
            "target": target,
            "recent_change": recent_change,
            "score": score,
            "label": label,
            "action": action
        })

    deals.sort(key=lambda item: item["score"], reverse=True)

    st.subheader(f"🏆 {len(deals)} Tracked Deals")

    for rank, deal in enumerate(deals, start=1):
        st.markdown("---")
        c1, c2 = st.columns([4, 1.3])

        with c1:
            st.markdown(f"### #{rank} 📚 {deal['product']}")
            st.write(
                f"**Current:** ₹{deal['current']:,.2f}  |  "
                f"**Average:** ₹{deal['average']:,.2f}  |  "
                f"**Lowest:** ₹{deal['lowest']:,.2f}"
            )

            trend = (
                "📉 Falling" if deal["recent_change"] < 0
                else "📈 Rising" if deal["recent_change"] > 0
                else "➡️ Stable"
            )

            st.write(
                f"{deal['label']} • **{deal['action']}**  |  "
                f"Recent movement: **{trend}**"
            )

            if deal["target"] > 0:
                gap = deal["current"] - deal["target"]
                if gap <= 0:
                    st.success(f"🎯 Target reached: ₹{deal['target']:,.2f}")
                else:
                    st.caption(
                        f"🎯 Target: ₹{deal['target']:,.2f} • "
                        f"₹{gap:,.2f} above target"
                    )
            else:
                st.caption("🎯 No target price set")

        with c2:
            st.metric("Deal Score", f"{deal['score']}/100")

    st.divider()
    st.caption(
        "Deal Score combines current price, historical average, lowest recorded price, "
        "recent movement and target price. It is a decision aid, not financial advice."
    )


# ============================================================
# AI ASSISTANT PAGE
# ============================================================

def show_ai_assistant():

    st.markdown(
        '<div class="dashboard-title">'
        '🤖 AI Price Assistant'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Ask about your tracked products, prices, alerts or dashboard.'
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # WELCOME MESSAGE
    # ========================================================

    if not st.session_state.ai_messages:

        welcome = (
            f"Welcome, "
            f"{st.session_state.user_name}! 👋 "
            "I’m your Price Intelligence assistant. "
            "How can I help?"
        )

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": welcome
            }
        )


    # ========================================================
    # DISPLAY MESSAGES
    # ========================================================

    for msg in st.session_state.ai_messages:

        if msg["role"] == "user":

            st.markdown(
                f"**You**  \n"
                f"{msg['content']}"
            )

        else:

            st.markdown(
                f"**🤖 AI Assistant**  \n"
                f"{msg['content']}"
            )

        st.divider()


    # ========================================================
    # CHAT INPUT
    # ========================================================

    prompt = st.chat_input(
        "Ask about a tracked product..."
    )

    if prompt:

        st.session_state.ai_messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        reply = ai_welcome_reply(
            prompt
        )

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        st.rerun()


# ============================================================
# ANALYTICS
# ============================================================

def show_analytics():

    st.markdown(
        '<div class="dashboard-title">'
        '📊 Analytics'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Understand your tracked price history and trends.'
        '</div>',
        unsafe_allow_html=True
    )

    df = load_price_data()

    if df.empty:

        st.info(
            "No analytics data available yet."
        )

        return

    summary = get_product_summary(
        df
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Tracked Products",
            len(summary)
        )

    with col2:

        st.metric(
            "Total Price Records",
            len(df)
        )

    with col3:

        overall_average = float(
            df["price_inr"].mean()
        )

        st.metric(
            "Overall Average",
            f"₹{overall_average:,.2f}"
        )

    st.divider()

    st.subheader(
        "📈 Product Price Comparison"
    )

    chart_data = summary[
        [
            "product",
            "current_price"
        ]
    ].copy()

    chart_data = chart_data.set_index(
        "product"
    )

    st.bar_chart(
        chart_data["current_price"]
    )

    st.subheader(
        "📋 Product Statistics"
    )

    table = summary.copy()

    table["current_price"] = (
        table["current_price"]
        .map(
            lambda x:
            f"₹{x:,.2f}"
        )
    )

    table["lowest_price"] = (
        table["lowest_price"]
        .map(
            lambda x:
            f"₹{x:,.2f}"
        )
    )

    table["average_price"] = (
        table["average_price"]
        .map(
            lambda x:
            f"₹{x:,.2f}"
        )
    )

    table.columns = [
        "Product",
        "Current Price",
        "Lowest Price",
        "Average Price",
        "Records"
    ]

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ALERTS
# ============================================================

def sync_alert_notifications():
    """Create notifications for currently active target/historical alerts."""

    # --------------------------------------------------------
    # Target-price alerts
    # --------------------------------------------------------
    watchlist = get_watchlist()

    if not watchlist.empty:
        for _, item in watchlist.iterrows():
            target_price = float(item["target_price"] or 0)

            if target_price <= 0:
                continue

            title, current_price, error = scrape_single_product(item["url"])

            if error or current_price is None:
                continue

            current_inr = current_price * st.session_state.gbp_to_inr
            target_inr = target_price * st.session_state.gbp_to_inr

            if current_price <= target_price:
                message = (
                    f"Current price: £{current_price:.2f} "
                    f"(₹{current_inr:,.2f}) • "
                    f"Target: £{target_price:.2f} "
                    f"(₹{target_inr:,.2f})"
                )

                add_notification(
                    "target",
                    item["product"],
                    message,
                    f"target|{item['product']}|{current_price:.2f}|{target_price:.2f}"
                )

    # --------------------------------------------------------
    # Historical-average alerts
    # --------------------------------------------------------
    df = load_price_data()

    if df.empty:
        return

    summary = get_product_summary(df)
    threshold = st.session_state.alert_threshold

    for _, row in summary.iterrows():
        current = float(row["current_price"])
        average = float(row["average_price"])

        if average == 0:
            continue

        difference = ((current - average) / average) * 100

        if difference <= -threshold:
            message = (
                f"Current price: ₹{current:,.2f} • "
                f"{abs(difference):.2f}% below historical average"
            )

            add_notification(
                "historical",
                row["product"],
                message,
                f"historical_below|{row['product']}|{current:.2f}|{average:.2f}|{threshold:g}"
            )

        elif difference >= threshold:
            message = (
                f"Current price: ₹{current:,.2f} • "
                f"{difference:.2f}% above historical average"
            )

            add_notification(
                "historical",
                row["product"],
                message,
                f"historical_above|{row['product']}|{current:.2f}|{average:.2f}|{threshold:g}"
            )


def show_alerts():

    # Keep Notifications and Alerts synchronized.
    sync_alert_notifications()

    st.markdown(
        '<div class="dashboard-title">'
        '🚨 Alerts'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Monitor target prices and historical price changes.'
        '</div>',
        unsafe_allow_html=True
    )

    # ========================================================
    # TARGET PRICE ALERTS
    # ========================================================

    st.subheader("🎯 Target Price Alerts")

    watchlist = get_watchlist()
    target_alert_found = False

    if watchlist.empty:

        st.info(
            "No products are in your watchlist yet. "
            "Search & Add products and set a target price to use target alerts."
        )

    else:

        for _, item in watchlist.iterrows():

            target_price = float(item["target_price"] or 0)

            if target_price <= 0:
                continue

            title, current_price, error = scrape_single_product(
                item["url"]
            )

            if error or current_price is None:
                st.warning(
                    f"⚠️ Could not check **{item['product']}** right now."
                )
                continue

            current_inr = (
                current_price
                * st.session_state.gbp_to_inr
            )

            target_inr = (
                target_price
                * st.session_state.gbp_to_inr
            )

            if current_price <= target_price:

                target_alert_found = True

                target_message = (
                    f"Current price: £{current_price:.2f} "
                    f"(₹{current_inr:,.2f}) • "
                    f"Target: £{target_price:.2f} "
                    f"(₹{target_inr:,.2f})"
                )

                add_notification(
                    "target",
                    item["product"],
                    target_message,
                    f"target|{item['product']}|{current_price:.2f}|{target_price:.2f}"
                )

                st.success(
                    f"🎯 **Target reached: {item['product']}**\n\n"
                    f"Current price: **£{current_price:.2f}** "
                    f"(₹{current_inr:,.2f})\n\n"
                    f"Your target: **£{target_price:.2f}** "
                    f"(₹{target_inr:,.2f})"
                )

            else:

                remaining_gbp = current_price - target_price
                remaining_inr = (
                    remaining_gbp
                    * st.session_state.gbp_to_inr
                )

                st.info(
                    f"🔔 **{item['product']}**\n\n"
                    f"Current: **£{current_price:.2f}** (₹{current_inr:,.2f})  "
                    f"| Target: **£{target_price:.2f}** (₹{target_inr:,.2f})  "
                    f"| ₹{remaining_inr:,.2f} above target"
                )

        if not target_alert_found:
            st.caption(
                "No target price has been reached yet."
            )

    st.divider()

    # ========================================================
    # HISTORICAL PRICE ALERTS
    # ========================================================

    st.subheader("📊 Historical Price Alerts")

    df = load_price_data()

    if df.empty:

        st.info(
            "No historical price data available yet."
        )

        return

    summary = get_product_summary(df)

    threshold = st.session_state.alert_threshold
    found_alert = False

    for _, row in summary.iterrows():

        current = float(row["current_price"])
        average = float(row["average_price"])

        if average == 0:
            continue

        difference = (
            (current - average)
            / average
        ) * 100

        if difference <= -threshold:

            found_alert = True

            historical_message = (
                f"Current price: ₹{current:,.2f} • "
                f"{abs(difference):.2f}% below historical average"
            )

            add_notification(
                "historical",
                row["product"],
                historical_message,
                f"historical_below|{row['product']}|{current:.2f}|{average:.2f}|{threshold:g}"
            )

            st.success(
                f"🚨 **{row['product']}** is "
                f"{abs(difference):.2f}% below its historical average.\n\n"
                f"Current price: ₹{current:,.2f}"
            )

        elif difference >= threshold:

            found_alert = True

            historical_message = (
                f"Current price: ₹{current:,.2f} • "
                f"{difference:.2f}% above historical average"
            )

            add_notification(
                "historical",
                row["product"],
                historical_message,
                f"historical_above|{row['product']}|{current:.2f}|{average:.2f}|{threshold:g}"
            )

            st.warning(
                f"⚠️ **{row['product']}** is "
                f"{difference:.2f}% above its historical average.\n\n"
                f"Current price: ₹{current:,.2f}"
            )

    if not found_alert:

        st.info(
            "✅ No significant price alerts "
            f"at the current {threshold:g}% threshold."
        )


# ============================================================
# NOTIFICATION CENTER
# ============================================================

def show_notifications():

    # Refresh the notification store whenever this page is opened.
    sync_alert_notifications()

    st.markdown(
        '<div class="dashboard-title">'
        '🔔 Notifications'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'View, manage and review your price alerts in one place.'
        '</div>',
        unsafe_allow_html=True
    )

    notifications = get_notifications()
    unread = get_notifications(unread_only=True)

    top1, top2, top3 = st.columns(3)

    with top1:
        st.metric("🔔 Total Alerts", len(notifications))

    with top2:
        st.metric("🟣 Unread", len(unread))

    with top3:
        st.metric(
            "✅ Read",
            max(len(notifications) - len(unread), 0)
        )

    if len(unread) > 0:
        if st.button(
            "✅ Mark All as Read",
            use_container_width=True,
            key="mark_all_notifications"
        ):
            mark_all_notifications_read()
            st.rerun()

    st.divider()

    filter_option = st.selectbox(
        "Show",
        [
            "All Notifications",
            "Unread Only",
            "Read Only"
        ],
        key="notification_filter"
    )

    if filter_option == "Unread Only":
        display_df = unread
    elif filter_option == "Read Only":
        display_df = notifications[notifications["is_read"] == 1]
    else:
        display_df = notifications

    if display_df.empty:
        st.success(
            "🎉 No notifications in this view."
        )
        return

    for _, row in display_df.iterrows():

        is_read = int(row["is_read"]) == 1

        if row["alert_type"] == "target":
            icon = "🎯"
            label = "Target Price"
        elif row["alert_type"] == "historical":
            icon = "📊"
            label = "Historical Price"
        else:
            icon = "🔔"
            label = "Price Alert"

        status = "✓ Read" if is_read else "● Unread"

        st.markdown("---")

        left, right = st.columns([5, 1.3])

        with left:
            st.markdown(
                f"### {icon} {row['product']}"
            )
            st.caption(
                f"{label} • {status} • {row['created_at']}"
            )
            if is_read:
                st.write(row["message"])
            else:
                st.info(row["message"])

        with right:
            if not is_read:
                if st.button(
                    "✓ Read",
                    use_container_width=True,
                    key=f"read_notification_{row['id']}"
                ):
                    mark_notification_read(
                        int(row["id"])
                    )
                    st.rerun()


# ============================================================
# SUPPORT
# ============================================================

def show_support():

    st.markdown(
        '<div class="dashboard-title">'
        '💬 Support'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Send feedback or report an issue with the application.'
        '</div>',
        unsafe_allow_html=True
    )

    email = st.text_input(
        "Email",
        value=st.session_state.user_email
    )

    message = st.text_area(
        "How can we help?",
        placeholder="Describe your issue or feedback..."
    )

    if st.button(
        "📨 Send Message",
        use_container_width=True
    ):

        if not message.strip():

            st.error(
                "Please enter a message."
            )

        else:

            save_support_message(
                email.strip(),
                message.strip()
            )

            st.success(
                "✅ Your support message has been saved."
            )


# ============================================================
# SETTINGS
# ============================================================

def show_settings():

    st.markdown(
        '<div class="dashboard-title">'
        '⚙️ Settings'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="dashboard-subtitle">'
        'Customize the appearance and price-tracking behaviour.'
        '</div>',
        unsafe_allow_html=True
    )

    st.subheader(
        "🎨 Appearance"
    )

    theme = st.selectbox(
        "Theme",
        [
            "Midnight",
            "Ocean",
            "Forest",
            "Slate"
        ],
        index=[
            "Midnight",
            "Ocean",
            "Forest",
            "Slate"
        ].index(
            st.session_state.theme
        )
    )

    font = st.selectbox(
        "Font",
        [
            "Inter",
            "Poppins",
            "Roboto",
            "System"
        ],
        index=[
            "Inter",
            "Poppins",
            "Roboto",
            "System"
        ].index(
            st.session_state.font
        )
    )

    graph_type = st.selectbox(
        "Graph Type",
        [
            "Line",
            "Area",
            "Bar"
        ],
        index=[
            "Line",
            "Area",
            "Bar"
        ].index(
            st.session_state.graph_type
        )
    )

    wallpaper = st.selectbox(
        "Wallpaper",
        [
            "Premium Aurora",
            "Deep Space",
            "Minimal Dark"
        ],
        index=[
            "Premium Aurora",
            "Deep Space",
            "Minimal Dark"
        ].index(
            st.session_state.wallpaper
        )
    )

    st.subheader(
        "💱 Currency"
    )

    gbp_to_inr = st.number_input(
        "GBP → INR",
        min_value=1.0,
        value=float(
            st.session_state.gbp_to_inr
        ),
        step=1.0
    )

    st.subheader(
        "🔄 Auto Refresh"
    )

    auto_refresh = st.selectbox(
        "Refresh interval",
        [
            0,
            30,
            60,
            120,
            300
        ],
        index=[
            0,
            30,
            60,
            120,
            300
        ].index(
            st.session_state.auto_refresh
        ),
        format_func=lambda x:
            "Off"
            if x == 0
            else f"{x} seconds"
    )

    st.subheader(
        "🚨 Alert Threshold"
    )

    alert_threshold = st.slider(
        "Price change threshold (%)",
        min_value=1,
        max_value=20,
        value=int(
            st.session_state.alert_threshold
        )
    )

    # ========================================================
    # SAVE SETTINGS
    # ========================================================

    if st.button(
        "💾 Apply Settings",
        use_container_width=True
    ):

        st.session_state.theme = theme

        st.session_state.font = font

        st.session_state.graph_type = (
            graph_type
        )

        st.session_state.wallpaper = (
            wallpaper
        )

        st.session_state.gbp_to_inr = (
            gbp_to_inr
        )

        st.session_state.auto_refresh = (
            auto_refresh
        )

        st.session_state.alert_threshold = (
            alert_threshold
        )

        st.success(
            "✅ Settings updated."
        )

        st.rerun()


    st.divider()

    st.subheader(
        "ℹ️ Project Information"
    )

    st.write(
        "Price Intelligence Tracker"
    )

    st.caption(
        "Python • SQLite • Streamlit • "
        "BeautifulSoup • AI"
    )

    st.caption(
        "Current currency display uses "
        "the configured GBP → INR rate."
    )


# ============================================================
# MAIN APP
# ============================================================

def main():

    create_users_table()

    create_watchlist_table()

    create_notifications_table()

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    if not st.session_state.logged_in:

        if st.session_state.forgot_password:

            show_forgot_password()

        else:

            show_login()

        return


    # ========================================================
    # AUTO REFRESH
    # ========================================================

    if (
        st.session_state.auto_refresh > 0
        and st_autorefresh is not None
    ):

        refresh_count = st_autorefresh(
            interval=(
                st.session_state.auto_refresh
                * 1000
            ),
            key="price_refresh"
        )

        # Do not scrape immediately after login.
        # The first autorefresh event only initializes the counter;
        # price scraping starts on the next scheduled refresh.
        if "last_price_refresh_count" not in st.session_state:
            st.session_state.last_price_refresh_count = refresh_count
        elif refresh_count != st.session_state.last_price_refresh_count:
            st.session_state.last_price_refresh_count = refresh_count
            refreshed, errors = refresh_tracked_prices()

            if refreshed:
                st.toast(
                    f"🔄 {refreshed} price(s) refreshed automatically.",
                    icon="📈"
                )


    # ========================================================
    # SIDEBAR
    # ========================================================

    page = show_sidebar()


    # ========================================================
    # PAGE ROUTING
    # ========================================================

    if page == "🏠 Home":

        show_home()

    elif page == "🔍 Search & Add":

        show_search_add()

    elif page == "📦 Tracked Products":

        show_tracked_products()

    elif page == "📋 Product Details":

        show_product_details()

    elif page == "🏆 Best Deals":

        show_best_deals()

    elif page == "🔔 Notifications":

        show_notifications()

    elif page == "🤖 AI Assistant":

        show_ai_assistant()

    elif page == "📊 Analytics":

        show_analytics()

    elif page == "🚨 Alerts":

        show_alerts()

    elif page == "💬 Support":

        show_support()

    elif page == "⚙️ Settings":

        show_settings()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    main()