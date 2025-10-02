CREATE TABLE historical_prices (
    ticker VARCHAR(10),
    price_date DATE,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    close_price DECIMAL(10, 2),
    volume BIGINT,
    PRIMARY KEY (ticker, price_date)
);

CREATE TABLE historical_volatility (
    ticker VARCHAR(10),
    price_date DATE,
    implied_volatility DECIMAL(8, 4),
    PRIMARY KEY (ticker, price_date)
);