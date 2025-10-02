import datetime
import mysql.connector
import yfinance as yf
from mysql.connector import Error
import option_pricer_cpp as opc
import os

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'financial_data'
}

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

def get_option_chain(ticker, best_date_found):
    stock = yf.Ticker(ticker)
    return stock.option_chain(best_date_found)

def get_time_to_expiration(date):
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    date_today = datetime.date.today()
    time_difference = date - date_today
    days_till_expiration = time_difference.days
    T = days_till_expiration / 365.25
    return T


connection = None
cursor = None

TICKERS_TO_TRACK = ["NVDA", "AAPL", "TSLA", "SPY", "MSFT", "GOOGL", "AMZN", "COIN"]

try:
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Successfully connected to DB")
        cursor = connection.cursor()

        for ticker in TICKERS_TO_TRACK:
            print(f"--- Processing {ticker} ---")
            current_stock_price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[0]
            r = 4.74 / 100
            best_date = get_best_expiration_date(ticker)
            option_chain = get_option_chain(ticker, best_date)

            calls_df = option_chain.calls.copy()
            puts_df = option_chain.puts.copy()

            calls_df = calls_df[calls_df['volume'] > 0]
            puts_df = puts_df[puts_df['volume'] > 0]

            if calls_df.empty or puts_df.empty:
                print(f"No liquid options found for {ticker}, skipping.")
                continue

            calls_df['distance'] = (calls_df['strike'] - current_stock_price).abs()
            puts_df['distance'] = (puts_df['strike'] - current_stock_price).abs()

            atm_call_index = calls_df['distance'].idxmin()
            atm_call = calls_df.loc[atm_call_index]

            atm_put_index = puts_df['distance'].idxmin()
            atm_put = puts_df.loc[atm_put_index]

            K_call = atm_call['strike']
            K_put = atm_put['strike']

            option_price_call = atm_call['lastPrice']
            option_price_put = atm_put['lastPrice']

            T = get_time_to_expiration(best_date)

            op_type_call = opc.OptionType.Call
            op_type_put = opc.OptionType.Put

            temp_call_option = opc.Option(r, current_stock_price, K_call, T, 0.5, op_type_call)
            call_iv = temp_call_option.implied_volatility(option_price_call)

            temp_put_option = opc.Option(r, current_stock_price, K_put, T, 0.5, op_type_put)
            put_iv = temp_put_option.implied_volatility(option_price_put)

            average_iv = (call_iv + put_iv) / 2
            print(f"Calculated Average IV for {ticker}: {average_iv:.4f}")

            todays_date = datetime.date.today()

            sql_insert = """
                         INSERT INTO historical_volatility (ticker, price_date, implied_volatility)
                         VALUES (%s, %s, %s)
                            ON DUPLICATE KEY UPDATE implied_volatility = VALUES(implied_volatility) \
                         """

            data_tuple = (ticker, todays_date, average_iv)

            cursor.execute(sql_insert, data_tuple)
        connection.commit()
        print("\nAll IV data successfully committed to the database.")
except Error as e:
    print(f"Error connecting or writing to MySQL: {e}")

finally:
    if connection and connection.is_connected():
        if cursor:
            cursor.close()
        connection.close()
        print("MySQL connection is closed")
