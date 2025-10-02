import streamlit as st
import numpy as np
import plotly.express as px
import pandas as pd
import yfinance as yf
import datetime as datetime
import mysql.connector
from mysql.connector import Error
import option_pricer_cpp as opc
import os

# DB configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'financial_data'
}

# Stock tickers
TICKERS_TO_TRACK = ["NVDA", "AAPL", "TSLA", "SPY", "MSFT", "GOOGL", "AMZN", "COIN"]

# Connects to MySQL DB and fetches IV data for tickers returning a panda dataframe
def fetch_all_historical_iv():
    connection = None
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            one_year_ago = datetime.date.today() - datetime.timedelta(days=365)
            sql_query = "SELECT * FROM historical_volatility WHERE price_date >= %s"

            df = pd.read_sql(sql_query, connection, params=(one_year_ago,))
            return df
    except Error as e:
        st.error(f"Database Error: Could not fetch historical IV data. {e}")
        return pd.DataFrame()
    finally:
        if connection and connection.is_connected():
            connection.close()

# Fetches the best expiration date for a given ticker (nearest to 30 days in the future)
def get_best_expiration_date(ticker: str):
    stock = yf.Ticker(ticker)
    date_today = datetime.date.today()

    best_date_found = None
    smallest_diff = float('inf')

    for date in stock.options:
        current_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        diff_in_days = (current_date - date_today).days
        target_diff = abs(diff_in_days - 30)

        if target_diff < smallest_diff:
            smallest_diff = target_diff
            best_date_found = date
    return best_date_found

# Fetches option chain for a given ticker on a given day
def get_option_chain(ticker, best_date_found):
    stock = yf.Ticker(ticker)
    return stock.option_chain(best_date_found)

def get_current_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history().iloc[0]

# Calculates the greeks of an option
def greek_calculation(r, s0, k, t, sigma, option_type):
    op_enum_type = opc.OptionType.Call if (option_type == "Call") else opc.OptionType.Put
    option = opc.Option(r, s0, k, t, sigma, op_enum_type)
    return {
        "price": option.price(), "delta": option.delta(), "gamma": option.gamma(),
        "vega": option.vega(), "theta": option.theta(), "rho": option.rho()
    }

# Plots a graph the greeks against the underlying price
def sensitivity_analysis_calc(r, s0, k, t, sigma, option_type, analysis_selection):
    op_enum_type = opc.OptionType.Call if (option_type == "Call") else opc.OptionType.Put
    price_range = np.linspace(s0 * 0.2, s0 * 1.8, 100)
    results = []

    for price in price_range:
        temp_option = opc.Option(r, price, k, t, sigma, op_enum_type)
        analysis_type_data = getattr(temp_option, analysis_selection.lower())()
        price_plot = [price, analysis_type_data]
        results.append(price_plot)

    df = pd.DataFrame.from_records(results, columns=["Underlying Price ($)", analysis_selection])
    fig = px.line(df, x="Underlying Price ($)", y=analysis_selection, title=f"{analysis_selection} vs Underlying Price", height=400, template="streamlit")
    return fig

# Main streamlit dashboard
if __name__ == "__main__":
    st.set_page_config(layout="wide")
    st.title("High-Performance Options Pricer (C++ Engine)")

    # Sidebar to take in option inputs
    with st.sidebar:
        st.sidebar.header("Option Parameters")
        option_type = st.selectbox("Option type",("Call","Put"))
        s0 = st.number_input("Underlying Price (S₀)", min_value=0.1, value=100.0, step=0.5)
        k = st.number_input("Strike Price (k)", min_value=0.1, value=100.0, step=0.5)
        t = st.number_input("Time to Expiration (T in years)", min_value=0.0, value=1.0, step=0.01)
        r = st.slider("Risk-free rate (r)", min_value=0.0, max_value=0.25, value=0.046, step=0.001, format="%.3f")
        sigma = st.slider("Volatility (σ)", min_value=0.1, max_value=1.50, value=0.20, step=0.001, format="%.3f")

    # Greeks Calculator UI
    try:
        st.header("Calculated Option Values")
        greek_values = greek_calculation(r, s0, k, t, sigma, option_type)

        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${greek_values['price']:,.2f}")
        c2.metric("Delta", f"{greek_values['delta']:.4f}")
        c3.metric("Gamma", f"{greek_values['gamma']:.4f}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Vega", f"{greek_values['vega']:.4f}")
        c5.metric("Theta", f"{greek_values['theta']:.4f}")
        c6.metric("Rho", f"{greek_values['rho']:.4f}")
    except Exception as e:
        st.error(f"An error occurred during calculation: {e}")

    # Sensitivity Analysis UI
    st.header("Sensitivity Analysis")
    analysis_selection = st.selectbox("Select a value to analyse:", ("Price", "Delta", "Gamma", "Vega", "Theta", "Rho"))
    sensitivity_fig = sensitivity_analysis_calc(r, s0, k, t, sigma, option_type, analysis_selection)
    st.plotly_chart(sensitivity_fig, use_container_width=True)

    # IV RANKER UI
    st.header("Implied Volatility (IV) Ranker")

    # Fetch all historical IV data from the database
    iv_data_df = fetch_all_historical_iv()

    if not iv_data_df.empty:
        iv_rank_results = []

        for ticker in TICKERS_TO_TRACK:
            ticker_df = iv_data_df[iv_data_df['ticker'] == ticker]

            if not ticker_df.empty:
                # Find the min, max, and current IV
                iv_min = ticker_df['implied_volatility'].min()
                iv_max = ticker_df['implied_volatility'].max()
                current_iv = ticker_df['implied_volatility'].iloc[-1]

                if (iv_max - iv_min) > 0:
                    iv_rank = (current_iv - iv_min) / (iv_max - iv_min) * 100
                else:
                    iv_rank = 50.0 # Default to 50 if there's no range yet

                iv_rank_results.append({
                    "Ticker": ticker,
                    "Current IV": f"{current_iv:.2%}",
                    "IV Rank": f"{iv_rank:.1f}%",
                    "52-Wk Low": f"{iv_min:.2%}",
                    "52-Wk High": f"{iv_max:.2%}"
                })
        results_df = pd.DataFrame(iv_rank_results)
        st.dataframe(results_df, use_container_width=True)
    else:
        st.info("Historical IV data is not yet available. Please run the 'update_daily_iv.py' script.")
