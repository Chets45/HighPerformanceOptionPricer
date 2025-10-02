import datetime
import mysql.connector
import yfinance as yf
from mysql.connector import Error
import pandas as pd
import time
import option_pricer_cpp as opc
import os

# DB Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'financial_data'
}

TICKERS_TO_TRACK = ["NVDA", "AAPL", "TSLA", "SPY", "MSFT", "GOOGL", "AMZN", "COIN"]

def get_time_to_expiration(start_date, expiration_date_str):
    expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    time_difference = expiration_date - start_date
    return time_difference.days / 365.25

def backfill_iv_for_ticker(ticker, historical_prices_df, cursor):
    print(f"\n--- Starting backfill for {ticker} ---")

    op_type_call = opc.OptionType.Call
    op_type_put = opc.OptionType.Put
    r = 0.0474 # Fixed risk-free rate

    try:
        stock = yf.Ticker(ticker)
        available_options = stock.options
        if not available_options:
            print(f"No options available for {ticker}. Skipping ticker.")
            return
    except Exception as e:
        print(f"Could not fetch initial data for {ticker}. Skipping. Error: {e}")
        return

    # Loop through each historical day for which we have price data
    for index, row in historical_prices_df.iterrows():
        current_date = row['price_date']
        s0 = row['close_price']
        print(f"Processing {ticker} for date: {current_date.strftime('%Y-%m-%d')}")

        try:
            best_date_found = None
            smallest_diff = float('inf')

            for date_str in available_options:
                exp_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                if exp_date < current_date: continue

                diff_in_days = (exp_date - current_date).days
                target_diff = abs(diff_in_days - 30)
                if target_diff < smallest_diff:
                    smallest_diff = target_diff
                    best_date_found = date_str

            if not best_date_found:
                print("No suitable future expiration found. Skipping day.")
                continue

            option_chain = stock.option_chain(best_date_found)
            calls_df = option_chain.calls.copy()
            puts_df = option_chain.puts.copy()

            # Filter for options with some trading volume to improve data quality
            calls_df = calls_df[calls_df['volume'] > 0]
            puts_df = puts_df[puts_df['volume'] > 0]

            if calls_df.empty or puts_df.empty:
                print("  -> No liquid option chain data found for this date. Skipping.")
                continue

            # Find ATM options
            calls_df['distance'] = (calls_df['strike'] - s0).abs()
            puts_df['distance'] = (puts_df['strike'] - s0).abs()

            atm_call = calls_df.loc[calls_df['distance'].idxmin()]
            atm_put = puts_df.loc[puts_df['distance'].idxmin()]

            T = get_time_to_expiration(current_date, best_date_found)
            K_call, price_call = atm_call['strike'], atm_call['lastPrice']
            K_put, price_put = atm_put['strike'], atm_put['lastPrice']

            temp_call_opt = opc.Option(r, s0, K_call, T, 0.5, op_type_call)
            call_iv = temp_call_opt.implied_volatility(price_call)

            temp_put_opt = opc.Option(r, s0, K_put, T, 0.5, op_type_put)
            put_iv = temp_put_opt.implied_volatility(price_put)

            average_iv = (call_iv + put_iv) / 2

            if 0.01 < average_iv < 5.0:
                sql_insert = """
                             INSERT INTO historical_volatility (ticker, price_date, implied_volatility)
                             VALUES (%s, %s, %s)
                                 ON DUPLICATE KEY UPDATE implied_volatility = VALUES(implied_volatility) \
                             """
                data_tuple = (ticker, current_date, average_iv)
                cursor.execute(sql_insert, data_tuple)
                print(f"  -> Successfully calculated and stored IV: {average_iv:.4f}")
            else:
                print(f"  -> Calculated IV ({average_iv:.4f}) is an outlier. Skipping storage.")

        except Exception as e:
            print(f"  -> An error occurred, skipping this day. Error: {e}")
            continue

        # Delay to maintain a sustainable connection with yfinance
        time.sleep(0.5)

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**db_config)
    if connection.is_connected():
        print("Successfully connected to DB for backfilling process.")
        cursor = connection.cursor()

        print("Fetching all historical price data...")
        sql_query = "SELECT * FROM historical_prices"
        all_prices_df = pd.read_sql(sql_query, connection)
        all_prices_df['price_date'] = pd.to_datetime(all_prices_df['price_date']).dt.date
        print("Fetch complete.")

        for ticker in TICKERS_TO_TRACK:
            ticker_prices_df = all_prices_df[all_prices_df['ticker'] == ticker]
            backfill_iv_for_ticker(ticker, ticker_prices_df, cursor)

        connection.commit()
        print("\nBackfill process complete. All data has been committed.")

except Error as e:
    print(f"A database error occurred: {e}")

finally:
    if connection and connection.is_connected():
        if cursor:
            cursor.close()
        connection.close()
        print("MySQL connection is closed")

