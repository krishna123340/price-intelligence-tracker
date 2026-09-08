import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_insights(product_df, alert_threshold=5):

    if product_df.empty:
        return {
            "trend": "N/A",
            "summary": "No price data available.",
            "insights": []
        }

    latest_price = float(product_df["price_inr"].iloc[-1])

    if len(product_df) >= 2:
        previous_price = float(product_df["price_inr"].iloc[-2])
    else:
        previous_price = latest_price

    lowest_price = float(product_df["price_inr"].min())
    highest_price = float(product_df["price_inr"].max())
    average_price = float(product_df["price_inr"].mean())

    if previous_price != 0:
        change_percent = ((latest_price - previous_price) / previous_price) * 100
    else:
        change_percent = 0

    if change_percent < 0:
        trend = "📉 Falling"
    elif change_percent > 0:
        trend = "📈 Rising"
    else:
        trend = "➡️ Stable"

    prompt = f"""
Analyze this product price data.

Latest price: ₹{latest_price:.2f}
Previous price: ₹{previous_price:.2f}
Price change: {change_percent:.2f}%
Lowest recorded price: ₹{lowest_price:.2f}
Highest recorded price: ₹{highest_price:.2f}
Historical average: ₹{average_price:.2f}
Alert threshold: {alert_threshold}%

Give a short practical buying insight.

Return exactly 3 bullet points.
"""

    try:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        ai_text = response.output_text.strip()

    except Exception as e:
        ai_text = f"AI analysis unavailable: {e}"

    summary = f"Current trend: {trend}. Price changed by {change_percent:+.2f}%."

    insights = [
        ai_text
    ]

    if latest_price <= lowest_price:
        insights.append("💰 The current price is at the lowest recorded level.")

    if latest_price < average_price:
        insights.append("🟢 The current price is below the historical average.")
    elif latest_price > average_price:
        insights.append("🔴 The current price is above the historical average.")

    return {
        "trend": trend,
        "summary": summary,
        "insights": insights
    }
