import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# ==========================================
# CONFIGURATION
# ==========================================

DATABASE = "prices.db"

GBP_TO_INR = 128


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Price Intelligence Tracker",
    page_icon="📊",
    layout="wide"
)


# ==========================================
# AUTO REFRESH
# ==========================================

st_autorefresh(
    interval=60000,
    key="price_tracker_refresh"
)


# ==========================================
# TITLE
# ==========================================

st.title("📊 Price Intelligence Tracker")

st.caption(
    "Automated Price Monitoring & Smart Alert System"
)


# ==========================================
# ALERT THRESHOLD
# ==========================================

alert_threshold = st.slider(
    "🚨 Alert Threshold (%)",
    min_value=1,
    max_value=20,
    value=5
)


# ==========================================
# LOAD DATABASE
# ==========================================

db = sqlite3.connect(DATABASE)

df = pd.read_sql_query(
    """
    SELECT product, price, date
    FROM prices
    ORDER BY date ASC
    """,
    db
)

db.close()


# ==========================================
# CHECK DATABASE
# ==========================================

if df.empty:

    st.warning(
        "⚠️ No price data available yet."
    )

    st.stop()


# ==========================================
# DATA PREPARATION
# ==========================================

df["date"] = pd.to_datetime(
    df["date"]
)

df["price_inr"] = (
    df["price"] * GBP_TO_INR
)


# ==========================================
# LATEST PRICE FOR EACH PRODUCT
# ==========================================

latest_df = (
    df.sort_values("date")
    .groupby(
        "product",
        as_index=False
    )
    .tail(1)
)


# ==========================================
# KPI CALCULATIONS
# ==========================================

total_products = (
    latest_df["product"].nunique()
)

average_price = (
    latest_df["price_inr"].mean()
)

lowest_price = (
    latest_df["price_inr"].min()
)


# ==========================================
# PRICE CHANGE ANALYSIS
# ==========================================

drop_products = []

summary_data = []


for product in latest_df["product"]:

    product_history = (
        df[df["product"] == product]
        .sort_values("date")
    )

    latest_price = (
        product_history.iloc[-1]["price"]
    )

    if len(product_history) >= 2:

        previous_price = (
            product_history.iloc[-2]["price"]
        )

    else:

        previous_price = latest_price


    # --------------------------------------
    # Calculate percentage change
    # --------------------------------------

    if previous_price != 0:

        change_percent = (
            (latest_price - previous_price)
            / previous_price
        ) * 100

    else:

        change_percent = 0


    # --------------------------------------
    # Determine status
    # --------------------------------------

    if change_percent < 0:

        drop_percent = abs(
            change_percent
        )

        status = (
            "📉 Price Dropped"
        )

        if drop_percent >= alert_threshold:

            drop_products.append(
                {
                    "product": product,
                    "drop": drop_percent
                }
            )

    elif change_percent > 0:

        status = (
            "📈 Price Increased"
        )

    else:

        status = (
            "➡️ Unchanged"
        )


    # --------------------------------------
    # Save summary
    # --------------------------------------

    summary_data.append(
        {
            "Product": product,
            "Current Price": (
                latest_price * GBP_TO_INR
            ),
            "Previous Price": (
                previous_price * GBP_TO_INR
            ),
            "Change": change_percent,
            "Status": status
        }
    )


# ==========================================
# SUMMARY DATAFRAME
# ==========================================

summary_df = pd.DataFrame(
    summary_data
)


# ==========================================
# ACTIVE DROPS
# ==========================================

active_drops = len(
    drop_products
)


# ==========================================
# PRICE DROP ALERTS
# ==========================================

st.header("🚨 Price Drop Alerts")


if active_drops == 0:

    st.success(
        "✅ No price drops detected"
    )

else:

    for item in drop_products:

        st.error(
            f"📉 {item['product']} "
            f"price dropped by "
            f"{item['drop']:.2f}%"
        )


# ==========================================
# KPI CARDS
# ==========================================

col1, col2, col3, col4 = st.columns(4)


col1.metric(
    "🛍️ Total Products",
    total_products
)


col2.metric(
    "💰 Average Price",
    f"₹{average_price:,.2f}"
)


col3.metric(
    "🏆 Lowest Price",
    f"₹{lowest_price:,.2f}"
)


col4.metric(
    "🚨 Active Drops",
    active_drops
)


# ==========================================
# PRODUCTS
# ==========================================

st.header("🛍️ Products")


# Format values for display

display_df = summary_df.copy()


display_df["Current Price"] = (
    display_df["Current Price"]
    .apply(
        lambda x: f"₹{x:,.2f}"
    )
)


display_df["Previous Price"] = (
    display_df["Previous Price"]
    .apply(
        lambda x: f"₹{x:,.2f}"
    )
)


display_df["Change"] = (
    display_df["Change"]
    .apply(
        lambda x: f"{x:.2f}%"
    )
)


# ==========================================
# ROW HIGHLIGHTING
# ==========================================

def highlight_status(row):

    if "Price Dropped" in row["Status"]:

        return [
            "background-color: rgba(0, 255, 0, 0.15)"
        ] * len(row)

    elif "Price Increased" in row["Status"]:

        return [
            "background-color: rgba(255, 165, 0, 0.15)"
        ] * len(row)

    else:

        return [""] * len(row)


st.dataframe(
    display_df.style.apply(
        highlight_status,
        axis=1
    ),
    use_container_width=True,
    hide_index=True
)


# ==========================================
# PRICE HISTORY
# ==========================================

st.header("📊 Price History")


selected_product = st.selectbox(
    "Select Product",
    sorted(
        df["product"].unique()
    )
)


# ==========================================
# SELECTED PRODUCT DATA
# ==========================================

product_df = (
    df[
        df["product"]
        == selected_product
    ]
    .sort_values("date")
    .copy()
)


# ==========================================
# CURRENT / PREVIOUS PRICE
# ==========================================

current_price = (
    product_df.iloc[-1]["price"]
)

if len(product_df) >= 2:

    previous_price = (
        product_df.iloc[-2]["price"]
    )

else:

    previous_price = current_price


# ==========================================
# PRICE CHANGE
# ==========================================

if previous_price != 0:

    price_change = (
        (current_price - previous_price)
        / previous_price
    ) * 100

else:

    price_change = 0


# ==========================================
# PRICE STATISTICS
# ==========================================

history_low = (
    product_df["price_inr"].min()
)

history_high = (
    product_df["price_inr"].max()
)

last_updated = (
    product_df["date"].max()
)


# ==========================================
# HISTORY METRICS
# ==========================================

hcol1, hcol2, hcol3, hcol4 = st.columns(4)


hcol1.metric(
    "Current Price",
    f"₹{current_price * GBP_TO_INR:,.2f}"
)


hcol2.metric(
    "Previous Price",
    f"₹{previous_price * GBP_TO_INR:,.2f}"
)


hcol3.metric(
    "Lowest Price",
    f"₹{history_low:,.2f}"
)


hcol4.metric(
    "Highest Price",
    f"₹{history_high:,.2f}"
)


# ==========================================
# PRICE CHANGE INFORMATION
# ==========================================

if price_change < 0:

    st.success(
        f"📉 Price decreased by "
        f"{abs(price_change):.2f}%"
    )

elif price_change > 0:

    st.warning(
        f"📈 Price increased by "
        f"{price_change:.2f}%"
    )

else:

    st.info(
        "➡️ Price unchanged"
    )


# ==========================================
# PRICE HISTORY CHART
# ==========================================

chart_df = product_df.copy()


fig = px.line(
    chart_df,
    x="date",
    y="price_inr",
    markers=True,
    title=(
        f"Price History — "
        f"{selected_product}"
    ),
    labels={
        "date": "Date",
        "price_inr": "Price (INR)"
    }
)


fig.update_layout(
    hovermode="x unified"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ==========================================
# LAST UPDATED
# ==========================================

st.caption(
    f"🕒 Last updated: "
    f"{last_updated}"
)


st.caption(
    f"💱 GBP → INR Rate: "
    f"₹{GBP_TO_INR}"
)