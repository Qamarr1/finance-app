import streamlit as st
import pandas as pd
import yfinance as yf
import altair as alt

#Styling
st.set_page_config(page_title="Stock Screener & Calculator", layout="wide")

# Custom theme styling (simple but clean)
st.markdown("""
    <style>
        body {
            background-color: #f8f9fa;
        }
        .stSlider > div:first-child {
            font-weight: 600;
        }
    </style>
""", unsafe_allow_html=True)

# Load your local stock data
@st.cache_data

def load_data():
    return pd.read_csv("financial_data_35_35_15_15_all_final.csv")

df = load_data()

# App title
st.title(" MEFIC Stock Screener ")

# Tabs for Screener and Ticker Evaluator
tabs = st.tabs(["Stock Screener", "Evaluate a Stock"])

# ---------------- Tab 1: Screener ----------------
with tabs[0]:
    st.sidebar.header(" Adjust Weights")
    w_pe = st.sidebar.slider("PE Score Weight", 0.0, 1.0, 0.35, key="pe", help="Lower PE means better value")
    w_roe = st.sidebar.slider("ROE Score Weight", 0.0, 1.0, 0.35, key="roe", help="Higher ROE means better profitability")
    w_roa = st.sidebar.slider("ROA Score Weight", 0.0, 1.0, 0.15, key="roa", help="Higher ROA means better asset efficiency")
    w_div = st.sidebar.slider("Dividend Score Weight", 0.0, 1.0, 0.15, key="div", help="Higher dividends are attractive to income investors")

    total = w_pe + w_roe + w_roa + w_div
    w_pe /= total
    w_roe /= total
    w_roa /= total
    w_div /= total

    df["Score"] = (
        w_pe * df["PE_Score"] +
        w_roe * df["ROE_Score"] +
        w_roa * df["ROA_Score"] +
        w_div * df["Dividend_Score"]
    )

    st.sidebar.header("Filter Criteria")
    min_score = st.sidebar.slider("Minimum Score", float(df["Score"].min()), float(df["Score"].max()), float(df["Score"].min()))
    max_pe = st.sidebar.slider("Max PE Ratio", float(df["PE Ratio TTM"].min()), float(df["PE Ratio TTM"].max()), float(df["PE Ratio TTM"].max()))
    min_roe = st.sidebar.slider("Min ROE", float(df["ROE"].min()), float(df["ROE"].max()), float(df["ROE"].min()))

    filtered_df = df[
        (df["Score"] >= min_score) &
        (df["PE Ratio TTM"] <= max_pe) &
        (df["ROE"] >= min_roe)
    ].copy()

    top_stock = filtered_df.sort_values("Score", ascending=False).iloc[0]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Scoring Stock")
        st.metric("Company", top_stock["Company Name"])
        st.metric("Score", round(top_stock["Score"], 2))
        st.metric("Price", f"${top_stock['Price']:.2f}")
        st.metric("Target", f"${top_stock['YTarget']:.2f}")

    with col2:
        st.subheader("Summary")
        st.write(f"• Filtered to **{len(filtered_df)}** stocks")
        st.write(f"• PE ≤ {max_pe}, ROE ≥ {min_roe}")
        st.write(f"• Score ≥ {min_score:.2f}")
        st.write(f"• Weighted: PE {round(w_pe*100)}%, ROE {round(w_roe*100)}%, ROA {round(w_roa*100)}%, Dividend {round(w_div*100)}%")

    st.subheader("Top 10 Stocks by Score")
    top_10 = filtered_df.sort_values("Score", ascending=False).head(10)
    chart = alt.Chart(top_10).mark_bar().encode(
        x=alt.X("Score:Q"),
        y=alt.Y("Ticker:N", sort='-x'),
        tooltip=["Company Name", "Score", "Price", "YTarget"]
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Filtered Stock Table")
    st.dataframe(filtered_df)
    csv = filtered_df.to_csv(index=False)
    st.download_button("Download Filtered CSV", csv, "filtered_stocks.csv", "text/csv")

# ---------------- Tab 2: Ticker Evaluator ----------------
with tabs[1]:
    st.subheader(" Evaluate a Stock")

    ticker_list = df['Ticker'].dropna().unique()
    ticker = st.selectbox("Select a stock to evaluate:", ticker_list)

    if ticker:
        stock_data = df[df['Ticker'] == ticker].iloc[0]

        st.write(f"### {stock_data['Company Name']} ({ticker})")
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Price", f"${stock_data['Price']:.2f}")
        col2.metric("PE Ratio (TTM)", stock_data["PE Ratio TTM"])
        col3.metric("Forward PE", stock_data["PE Forward"])

        col1, col2, col3 = st.columns(3)
        col1.metric("ROE", f"{stock_data['ROE']:.2f}%")
        col2.metric("ROA", f"{stock_data['ROA']:.2f}%")
        col3.metric("Dividend Yield", f"{stock_data['Dividend Paid']:.2f}%")

        st.write("#### Price Chart (1Y)")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        st.line_chart(hist["Close"])

        currency = st.selectbox("Select currency:", ["USD", "SAR"])
        st.write("#### Investment Return Calculator")
        invest_amount = st.number_input(f"Enter investment amount ({currency}):", min_value=100.0, step=100.0)

        if invest_amount and stock_data.get("Price"):
            shares = invest_amount / stock_data["Price"]
            target_price = stock_data.get("YTarget", stock_data["Price"])
            expected_value = shares * target_price
            gain = expected_value - invest_amount

            st.success(f"You could buy **{shares:.2f} shares**")
            st.info(f"Expected value at target price ({target_price}): **{expected_value:.2f} {currency}**")
            st.metric("Estimated Gain", f"{gain:.2f} {currency}", delta=f"{(gain/invest_amount)*100:.2f}%")


