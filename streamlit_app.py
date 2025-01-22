import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

st.title("Significant Candle & Support/Resistance Detector")

st.write("This app downloads 60 days of daily OHLCV data, calculates ATR, "
         "and identifies 'significant candles' plus unbroken support/resistance levels.")

# 1. User Inputs: Ticker symbol & Date
ticker = st.text_input("Enter Ticker Symbol", value="AAPL")
selected_date = st.date_input("Select a Date", value=datetime.date.today())

# 2. Download 60 days of daily OHLCV data from yfinance
#    We'll consider the selected date as the end date.
start_date = selected_date - datetime.timedelta(days=60)
end_date = selected_date

# Download data from yfinance
data = yf.download(ticker, start=start_date, end=end_date, interval="1d")

# If no data is returned, handle gracefully
if data.empty:
    st.error("No data found. Please try a different ticker or date range.")
    st.stop()

# 3. Calculate the Average True Range (ATR) over a 14-day rolling window
#    True Range (TR) = max(High - Low, abs(High - Previous Close), abs(Low - Previous Close))
data["H-L"] = data["High"] - data["Low"]
data["H-PC"] = (data["High"] - data["Close"].shift(1)).abs()
data["L-PC"] = (data["Low"] - data["Close"].shift(1)).abs()
data["TR"] = data[["H-L", "H-PC", "L-PC"]].max(axis=1)
data["ATR"] = data["TR"].rolling(window=14).mean()

# Drop initial NaN values where the rolling ATR is not available
data.dropna(subset=["ATR"], inplace=True)

# 4. Identify "significant" candles:
#    Criteria: The day's True Range > 1.2 * that day's ATR
significant_candles = data[data["TR"] > 1.2 * data["ATR"]]

# 5. Find unbroken support/resistance based on these candles:
#    - A candle's High is a resistance if no subsequent day’s High exceeds it.
#    - A candle's Low is a support if no subsequent day’s Low goes below it.
#
#    We'll check from the candle's date up to the selected_date.
resistance_levels = []
support_levels = []

for candle_date, row in significant_candles.iterrows():
    candle_high = row["High"]
    candle_low = row["Low"]
    
    # Subset data from the day after this candle to the selected_date
    subsequent_data = data.loc[candle_date + pd.Timedelta(days=1): end_date]
    
    # Check if the candle_high was broken (any High > candle_high)
    if not (subsequent_data["High"] > candle_high).any():
        resistance_levels.append((candle_date, candle_high))
    
    # Check if the candle_low was broken (any Low < candle_low)
    if not (subsequent_data["Low"] < candle_low).any():
        support_levels.append((candle_date, candle_low))

# 6. Display results

# Show full dataset in an expandable container
with st.expander("See Downloaded OHLCV Data"):
    st.dataframe(data[["Open","High","Low","Close","Volume","ATR"]].style.format(precision=2))

st.subheader("Significant Candles (TR > 1.2 × ATR)")
if significant_candles.empty:
    st.write("No significant candles found in this period.")
else:
    st.dataframe(significant_candles[["Open","High","Low","Close","Volume","TR","ATR"]].style.format(precision=2))

st.subheader("Unbroken Resistance Levels")
if resistance_levels:
    for r_date, r_level in resistance_levels:
        st.write(f"Date: {r_date.date()}, Level: {r_level:.2f}")
else:
    st.write("No unbroken resistance levels found.")

st.subheader("Unbroken Support Levels")
if support_levels:
    for s_date, s_level in support_levels:
        st.write(f"Date: {s_date.date()}, Level: {s_level:.2f}")
else:
    st.write("No unbroken support levels found.")

st.write("---")
st.write("For more information on Streamlit, check out [docs.streamlit.io](https://docs.streamlit.io).")
