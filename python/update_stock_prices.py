import datetime
import mysql.connector
import yfinance as yf
from dateutil.relativedelta import relativedelta
from mysql.connector import Error
import os

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD'),
    'database': 'financial_data'
}

db_column_map = {
    'Open': 'open_price',
    'High': 'high_price',
    'Low': 'low_price',
    'Close': 'close_price',
    'Volume': 'volume'
}

tickers = ["NVDA", "AAPL", "TSLA", "SPY", "MSFT", "GOOGL", "AMZN", "COIN"]

def update_stock_data(ticker: str):
    sql_select = "SELECT MAX(price_date) FROM historical_prices WHERE ticker = %s"
    cursor.execute(sql_select, (ticker,))
    result = cursor.fetchone()

    if result and result[0] is not None:
        last_date = result[0]
        start_date = last_date + datetime.timedelta(days=1)
    else:
        start_date = datetime.date.today() - relativedelta(years=1)

    if start_date <= datetime.date.today():
        pd_financial = yf.download(ticker, start_date)

        if not pd_financial.empty:
            pd_financial = pd_financial.rename(columns=db_column_map)
            print(f"Downloaded {len(pd_financial)} new rows for {ticker}...")

            sql_insert = ("INSERT INTO historical_prices (ticker, price_date, open_price, high_price, low_price, close_price, volume)"
                          "VALUES (%s, %s, %s, %s, %s, %s, %s)")

            ordered_columns = ['open_price', 'high_price', 'low_price', 'close_price', 'volume']
            pd_financial_ordered = pd_financial[ordered_columns]

            for index, row in pd_financial_ordered.iterrows():
                # Get a plain Python list of the row's values
                row_values = row.tolist()

                data_tuple = (
                    ticker,
                    index.date(),
                    row_values[0],  # open_price
                    row_values[1],  # high_price
                    row_values[2],  # low_price
                    row_values[3],  # close_price
                    int(row_values[4])   # volume
                )
                cursor.execute(sql_insert, data_tuple)

            connection.commit()
            print("Data successfully committed to the database.")
        else:
            print("No new data to download.")
    else:
        print("Database is already up to date.")

connection = None
cursor = None

try:
    connection = mysql.connector.connect(**db_config)

    if connection.is_connected():
        print("Successfully connected to DB")
        cursor = connection.cursor()

        for ticker in tickers:
            update_stock_data(ticker)

except Error as e:
    print(f"Error connecting or writing to MySQL: {e}")

finally:
    if connection and connection.is_connected():
        if cursor:
            cursor.close()
        connection.close()
        print("MySQL connection is closed")
