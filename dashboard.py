import os
import sqlite3
import base64

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from ai_insights import generate_insights


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Price Intelligence Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CONFIG
# ============================================================

DATABASE = "prices.db"

GBP_TO_INR = 128

AUTO_REFRESH_SECONDS = 60


# ============================================================
# AUTO REFRESH
# ============================================================

st_autorefresh(
    interval=AUTO_REFRESH_SECONDS * 1000,
    key="price_tracker_refresh"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not os.path.exists(DATABASE):

        return pd.DataFrame(
            columns=[
                "product",
                "price",
                "date"
            ]
        )

    db = sqlite3.connect(DATABASE)

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

    if not df.empty:

        df["date"] = pd.to_datetime(
            df["date"]
        )

        df["price_inr"] = (
            df["price"] * GBP_TO_INR
        )

    return df


df = load_data()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📊 Price Intelligence")

    st.caption(
        "Smart price monitoring dashboard"
    )

    st.divider()

    st.subheader("🎨 Appearance")

    theme = st.selectbox(
        "Theme",
        [
            "Midnight",
            "Ocean",
            "Minimal"
        ]
    )

    selected_font = st.selectbox(
        "🔤 Dashboard Font",
        [
            "Inter",
            "Poppins",
            "Arial"
        ]
    )

    st.subheader("📈 Graph")

    graph_type = st.selectbox(
        "Graph Type",
        [
            "Line",
            "Area",
            "Bar"
        ]
    )

    st.subheader("🚨 Alerts")

    alert_threshold = st.slider(
        "Alert Threshold (%)",
        min_value=1,
        max_value=20,
        value=5
    )

    st.divider()

    st.subheader("🖼️ Background")

    wallpaper_option = st.selectbox(
        "Wallpaper",
        [
            "Premium Aurora",
            "Custom Wallpaper",
            "None"
        ]
    )

    custom_wallpaper = None

    if wallpaper_option == "Custom Wallpaper":

        custom_wallpaper = st.file_uploader(
            "Upload wallpaper",
            type=[
                "png",
                "jpg",
                "jpeg",
                "webp"
            ]
        )

    st.divider()

    st.caption(
        f"💱 GBP → INR: ₹{GBP_TO_INR}"
    )

    st.caption(
        f"🔄 Auto refresh: {AUTO_REFRESH_SECONDS}s"
    )


# ============================================================
# THEME
# ============================================================

if theme == "Midnight":

    accent = "#38bdf8"
    accent_2 = "#8b5cf6"

    background = """
        radial-gradient(
            circle at 10% 10%,
            rgba(56,189,248,0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(139,92,246,0.20),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #050816 0%,
            #0b1024 48%,
            #111936 100%
        )
    """

    card_background = (
        "rgba(15,23,42,0.72)"
    )

    text_color = "#f8fafc"

    muted_color = "#94a3b8"

    chart_fill = (
        "rgba(56,189,248,0.13)"
    )


elif theme == "Ocean":

    accent = "#22d3ee"
    accent_2 = "#0ea5e9"

    background = """
        radial-gradient(
            circle at 10% 10%,
            rgba(34,211,238,0.18),
            transparent 30%
        ),
        radial-gradient(
            circle at 90% 20%,
            rgba(14,165,233,0.20),
            transparent 35%
        ),
        linear-gradient(
            135deg,
            #02131c 0%,
            #06232e 50%,
            #071b2c 100%
        )
    """

    card_background = (
        "rgba(4,30,43,0.74)"
    )

    text_color = "#ecfeff"

    muted_color = "#94a3b8"

    chart_fill = (
        "rgba(34,211,238,0.13)"
    )


else:

    accent = "#2563eb"
    accent_2 = "#7c3aed"

    background = """
        linear-gradient(
            135deg,
            #f8fafc 0%,
            #eef2ff 50%,
            #e0e7ff 100%
        )
    """

    card_background = (
        "rgba(255,255,255,0.82)"
    )

    text_color = "#0f172a"

    muted_color = "#64748b"

    chart_fill = (
        "rgba(37,99,235,0.10)"
    )


# ============================================================
# FONT
# ============================================================

font_urls = {

    "Inter":
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",

    "Poppins":
        "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap"

}


font_import = ""

if selected_font != "Arial":

    font_import = (
        f"@import url('{font_urls[selected_font]}');"
    )


# ============================================================
# WALLPAPER
# ============================================================

background_css = background


if wallpaper_option == "Custom Wallpaper":

    image_data = None

    if custom_wallpaper is not None:

        image_data = custom_wallpaper.read()

    elif os.path.exists(
        "assets/wallpaper.png"
    ):

        with open(
            "assets/wallpaper.png",
            "rb"
        ) as image_file:

            image_data = image_file.read()

    if image_data:

        encoded_image = base64.b64encode(
            image_data
        ).decode()

        background_css = f"""
        linear-gradient(
            rgba(5,8,22,0.72),
            rgba(5,8,22,0.80)
        ),
        url("data:image/png;base64,{encoded_image}")
        """


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    {font_import}

    .stApp {{
        background: {background_css};
        background-size: cover;
        background-attachment: fixed;
        color: {text_color};
    }}

    [data-testid="stSidebar"] {{
        background: rgba(3,7,18,0.94);
        border-right:
            1px solid
            rgba(255,255,255,0.08);
    }}

    [data-testid="stSidebar"] * {{
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            sans-serif !important;
    }}

    [data-testid="stAppViewContainer"] .main {{
        font-family:
            '{selected_font}',
            Arial,
            sans-serif;
    }}

    [data-testid="stAppViewContainer"] .main p,
    [data-testid="stAppViewContainer"] .main h1,
    [data-testid="stAppViewContainer"] .main h2,
    [data-testid="stAppViewContainer"] .main h3,
    [data-testid="stAppViewContainer"] .main label,
    [data-testid="stAppViewContainer"] .main button {{
        font-family:
            '{selected_font}',
            Arial,
            sans-serif !important;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}

    [data-testid="stMetric"] {{
        background: {card_background};
        border:
            1px solid
            rgba(255,255,255,0.10);
        border-radius: 18px;
        padding: 18px 20px;
        min-height: 125px;
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        box-shadow:
            0 12px 35px
            rgba(0,0,0,0.20);
    }}

    [data-testid="stMetricLabel"] {{
        color: {muted_color} !important;
    }}

    [data-testid="stMetricValue"] {{
        font-weight: 800;
    }}

    [data-testid="stDataFrame"] {{
        border-radius: 14px;
        overflow: hidden;
    }}

    [data-testid="stAlert"] {{
        border-radius: 14px;
    }}

    footer {{
        visibility: hidden;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "📊 Price Intelligence Tracker"
)

st.caption(
    "Automated price monitoring • Historical analytics • Smart alerts"
)


# ============================================================
# EMPTY DATABASE
# ============================================================

if df.empty:

    st.warning(
        "⚠️ No price data found in prices.db."
    )

    st.stop()


# ============================================================
# PRODUCT SELECTOR
# ============================================================

products = sorted(
    df["product"]
    .dropna()
    .unique()
)

selected_product = st.selectbox(
    "🛍️ Select Product",
    products
)


product_df = df[
    df["product"] == selected_product
].copy()


product_df = product_df.sort_values(
    "date"
).reset_index(drop=True)


# ============================================================
# CALCULATIONS
# ============================================================

latest_price = float(
    product_df["price_inr"].iloc[-1]
)


if len(product_df) >= 2:

    previous_price = float(
        product_df["price_inr"].iloc[-2]
    )

else:

    previous_price = latest_price


if previous_price != 0:

    change_percent = (
        (
            latest_price
            - previous_price
        )
        / previous_price
    ) * 100

else:

    change_percent = 0


lowest_price = float(
    product_df["price_inr"].min()
)

highest_price = float(
    product_df["price_inr"].max()
)

average_price = float(
    product_df["price_inr"].mean()
)

total_records = len(product_df)


# ============================================================
# AI INSIGHTS
# ============================================================

ai_result = generate_insights(
    product_df,
    alert_threshold
)


# ============================================================
# OVERVIEW
# ============================================================

st.subheader(
    "📊 Overview"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "CURRENT PRICE",
        f"₹{latest_price:,.2f}"
    )

    st.caption(
        "Latest recorded price"
    )


with col2:

    st.metric(
        "PRICE CHANGE",
        f"{change_percent:+.2f}%"
    )

    st.caption(
        ai_result["trend"]
    )


with col3:

    st.metric(
        "LOWEST PRICE",
        f"₹{lowest_price:,.2f}"
    )

    st.caption(
        "Historical minimum"
    )


with col4:

    st.metric(
        "AVERAGE PRICE",
        f"₹{average_price:,.2f}"
    )

    st.caption(
        f"Across {total_records} records"
    )


# ============================================================
# ALERT STATUS
# ============================================================

if (
    change_percent < 0
    and abs(change_percent)
    >= alert_threshold
):

    st.success(
        f"🚨 Alert threshold reached — "
        f"price dropped "
        f"{abs(change_percent):.2f}%."
    )

elif change_percent < 0:

    st.info(
        f"📉 Price dropped "
        f"{abs(change_percent):.2f}%, "
        f"below the "
        f"{alert_threshold}% threshold."
    )

elif change_percent > 0:

    st.warning(
        f"📈 Price increased "
        f"{change_percent:.2f}%."
    )

else:

    st.info(
        "➡️ Price has not changed."
    )


# ============================================================
# AI PRICE INSIGHTS
# ============================================================

st.subheader(
    "🤖 AI Price Insights"
)


ai_col1, ai_col2 = st.columns(
    [1, 2]
)


with ai_col1:

    st.metric(
        "PRICE TREND",
        ai_result["trend"]
    )


with ai_col2:

    st.info(
        f"💡 {ai_result['summary']}"
    )


st.markdown(
    "#### 🔎 Smart Analysis"
)


for insight in ai_result["insights"]:

    st.write(
        insight
    )


# ============================================================
# PRICE HISTORY
# ============================================================

st.subheader(
    "📈 Price History"
)


x_values = product_df["date"]

y_values = product_df["price_inr"]


fig = go.Figure()


# ============================================================
# GRAPH GLOW
# ============================================================

if graph_type in [
    "Line",
    "Area"
]:

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",

            line=dict(
                color=accent,
                width=10
            ),

            opacity=0.08,

            hoverinfo="skip",

            showlegend=False
        )
    )


# ============================================================
# LINE
# ============================================================

if graph_type == "Line":

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,

            mode="lines",

            name="Price",

            line=dict(
                color=accent,
                width=3,
                shape="linear"
            ),

            hovertemplate=(
                "<b>%{x|%d %b %Y %H:%M}</b>"
                "<br>Price: ₹%{y:,.2f}"
                "<extra></extra>"
            )
        )
    )


# ============================================================
# AREA
# ============================================================

elif graph_type == "Area":

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,

            mode="lines",

            name="Price",

            line=dict(
                color=accent,
                width=3,
                shape="linear"
            ),

            fill="tozeroy",

            fillcolor=chart_fill,

            hovertemplate=(
                "<b>%{x|%d %b %Y %H:%M}</b>"
                "<br>Price: ₹%{y:,.2f}"
                "<extra></extra>"
            )
        )
    )


# ============================================================
# BAR
# ============================================================

else:

    fig.add_trace(
        go.Bar(
            x=x_values,
            y=y_values,

            name="Price",

            marker=dict(
                color=accent
            ),

            hovertemplate=(
                "<b>%{x|%d %b %Y %H:%M}</b>"
                "<br>Price: ₹%{y:,.2f}"
                "<extra></extra>"
            )
        )
    )


# ============================================================
# CURRENT PRICE MARKER
# ============================================================

fig.add_trace(
    go.Scatter(
        x=[
            x_values.iloc[-1]
        ],

        y=[
            y_values.iloc[-1]
        ],

        mode="markers",

        name="Current",

        marker=dict(
            size=13,
            color=accent,

            line=dict(
                color="white",
                width=2
            )
        ),

        hovertemplate=(
            "<b>Current Price</b>"
            "<br>₹%{y:,.2f}"
            "<extra></extra>"
        )
    )
)


# ============================================================
# GRAPH LAYOUT
# ============================================================

fig.update_layout(

    height=470,

    margin=dict(
        l=15,
        r=20,
        t=20,
        b=20
    ),

    paper_bgcolor="rgba(0,0,0,0)",

    plot_bgcolor="rgba(0,0,0,0)",

    font=dict(
        family=selected_font,
        color=text_color
    ),

    hovermode="x unified",

    hoverlabel=dict(
        bgcolor="rgba(8,15,30,0.96)",
        bordercolor=accent,

        font=dict(
            color="white",
            size=13
        )
    ),

    xaxis=dict(

        showgrid=True,

        gridcolor=(
            "rgba(148,163,184,0.10)"
        ),

        zeroline=False,

        showline=False,

        tickfont=dict(
            color=muted_color
        )
    ),

    yaxis=dict(

        title="Price (₹)",

        showgrid=True,

        gridcolor=(
            "rgba(148,163,184,0.10)"
        ),

        zeroline=False,

        showline=False,

        tickfont=dict(
            color=muted_color
        ),

        title_font=dict(
            color=muted_color
        ),

        tickprefix="₹",

        separatethousands=True
    ),

    legend=dict(

        orientation="h",

        yanchor="bottom",

        y=1.01,

        xanchor="right",

        x=1,

        font=dict(
            color=muted_color
        )
    ),

    dragmode="zoom"
)


# ============================================================
# DISPLAY GRAPH
# ============================================================

with st.container(border=True):

    st.plotly_chart(
        fig,
        use_container_width=True,

        config={
            "displaylogo": False,
            "scrollZoom": True,
            "displayModeBar": True,

            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d"
            ]
        }
    )


# ============================================================
# PRICE STATISTICS
# ============================================================

st.subheader(
    "💰 Price Statistics"
)


left, right = st.columns(2)


# ============================================================
# STATISTICS
# ============================================================

with left:

    stats_df = pd.DataFrame(
        {
            "Metric": [
                "Current Price",
                "Previous Price",
                "Highest Price",
                "Lowest Price",
                "Average Price",
                "Total Records"
            ],

            "Value": [
                f"₹{latest_price:,.2f}",
                f"₹{previous_price:,.2f}",
                f"₹{highest_price:,.2f}",
                f"₹{lowest_price:,.2f}",
                f"₹{average_price:,.2f}",
                str(total_records)
            ]
        }
    )

    st.dataframe(
        stats_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TRACKER INFORMATION
# ============================================================

with right:

    first_date = (
        product_df["date"].iloc[0]
    )

    last_date = (
        product_df["date"].iloc[-1]
    )

    st.write(
        "**Product:**"
    )

    st.write(
        selected_product
    )

    st.write(
        "**Tracking Started:**"
    )

    st.write(
        first_date.strftime(
            "%d %b %Y %H:%M"
        )
    )

    st.write(
        "**Latest Update:**"
    )

    st.write(
        last_date.strftime(
            "%d %b %Y %H:%M"
        )
    )

    st.write(
        f"**Alert Threshold:** "
        f"{alert_threshold}%"
    )

    st.write(
        "**Currency:** GBP → INR"
    )


# ============================================================
# RECENT RECORDS
# ============================================================

st.subheader(
    "🕒 Recent Price Records"
)


recent_df = product_df[
    [
        "date",
        "price",
        "price_inr"
    ]
].copy()


recent_df = recent_df.sort_values(
    "date",
    ascending=False
).head(10)


recent_df["date"] = recent_df[
    "date"
].dt.strftime(
    "%d %b %Y %H:%M"
)


recent_df["price"] = recent_df[
    "price"
].apply(
    lambda x: f"£{x:,.2f}"
)


recent_df["price_inr"] = recent_df[
    "price_inr"
].apply(
    lambda x: f"₹{x:,.2f}"
)


recent_df.columns = [
    "Date",
    "Original Price",
    "INR Price"
]


st.dataframe(
    recent_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "📊 Price Intelligence Tracker • "
    "Automated Monitoring • "
    "AI Price Insights • "
    "Historical Analytics"
)