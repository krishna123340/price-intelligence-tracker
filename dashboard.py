import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st_autorefresh(
    interval=60000,
    key="price_refresh"
)
st.title("📊 Price Intelligence Tracker")

# Alert Threshold
alert_threshold = st.slider(
    "🚨 Alert Threshold (%)",
    min_value=1,
    max_value=20,
    value=5
)

# Connect to database
db = sqlite3.connect("prices.db")

df = pd.read_sql_query("""
SELECT product, price, date
FROM prices
ORDER BY date
""", db)

db.close()


# --------------------------------
# PRICE DROP ALERTS
# --------------------------------

st.subheader("🚨 Price Drop Alerts")

drop_products = []

for product_name in df["product"].unique():

    product_rows = df[df["product"] == product_name]

    if len(product_rows) < 2:
        continue

    latest = product_rows.iloc[-1]["price"]
    previous = product_rows.iloc[-2]["price"]

    if latest < previous:

        drop = ((previous - latest) / previous) * 100

        if drop >= alert_threshold:

            if drop >= 10:
                alert_message = (
                    f"🚨 BIG PRICE DROP: {product_name} — {drop:.2f}%"
                )

            else:
                alert_message = (
                    f"⚠️ PRICE DROP: {product_name} — {drop:.2f}%"
                )

            drop_products.append(alert_message)

if drop_products:

    for alert in drop_products:
        st.error(alert)

else:
    st.success("✅ No price drops detected")

    # --------------------------------
# DASHBOARD METRICS
# --------------------------------

total_products = df["product"].nunique()
average_price = df["price"].mean()
active_drops = len(drop_products)

col1, col2, col3 = st.columns(3)

col1.metric(
    "🛍️ Total Products",
    total_products
)

col2.metric(
    "💰 Average Price",
    f"£{average_price:.2f}"
)

col3.metric(
    "🚨 Active Drops",
    active_drops
)


# --------------------------------
# PRODUCTS
# --------------------------------

st.subheader("🛍️ Products")

product_summary = []

for product_name in df["product"].unique():

    product_rows = df[df["product"] == product_name]

    if len(product_rows) < 2:
        continue

    current = product_rows.iloc[-1]["price"]
    previous = product_rows.iloc[-2]["price"]

    change = ((current - previous) / previous) * 100

    if current < previous:
        status = "📉 Price Dropped"

    elif current > previous:
        status = "📈 Price Increased"

    else:
        status = "➡️ Unchanged"

    product_summary.append({
        "Product": product_name,
        "Current Price": f"£{current:.2f}",
        "Previous Price": f"£{previous:.2f}",
        "Change": f"{change:.2f}%",
        "Status": status
    })

summary_df = pd.DataFrame(product_summary)

st.dataframe(
    summary_df,
    use_container_width=True
)


# --------------------------------
# PRICE HISTORY
# --------------------------------

st.subheader("📊 Price History")

product = st.selectbox(
    "🔎 Select a product",
    sorted(df["product"].unique())
)

product_data = df[df["product"] == product]
if len(product_data) < 2:
    st.info("⏳ Price history ke liye kam se kam 2 records chahiye.")
    st.stop()

current_price = product_data.iloc[-1]["price"]

previous_price = product_data.iloc[-2]["price"]

last_updated = product_data.iloc[-1]["date"]

price_change = (
    (current_price - previous_price)
    / previous_price
) * 100


# Price status

if current_price < previous_price:

    st.success(
        f"📉 Price dropped by £{previous_price - current_price:.2f}"
    )

elif current_price > previous_price:

    st.warning(
        f"📈 Price increased by £{current_price - previous_price:.2f}"
    )

else:

    st.info("➡️ Price unchanged!")


# Current price

st.metric(
    "💰 Current Price",
    f"£{current_price:.2f}"
)
# Best and highest price

lowest_price = product_data["price"].min()
highest_price = product_data["price"].max()

col1, col2 = st.columns(2)

col1.metric(
    "🏆 Lowest Price",
    f"£{lowest_price:.2f}"
)

col2.metric(
    "📈 Highest Price",
    f"£{highest_price:.2f}"
)

# Price change

st.metric(
    "📉 Price Change",
    f"{price_change:.2f}%"
)


# Last updated

formatted_time = pd.to_datetime(last_updated).strftime(
    "%d %b %Y, %I:%M %p"
)

st.write(
    "🕐 Last Updated:",
    formatted_time
)

# --------------------------------
# PRICE GRAPH
# --------------------------------

fig = px.line(
    product_data,
    x="date",
    y="price",
    title=f"📈 Price History: {product}",
    markers=True,
    labels={
        "date": "Date & Time",
        "price": "Price (£)"
    }
)

st.plotly_chart(
    fig,
    use_container_width=True
)