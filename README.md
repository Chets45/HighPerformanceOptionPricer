# High-Performance Options Pricer & IV Ranker

A comprehensive options analysis suite featuring a C++ calculation engine for high-speed pricing and risk analysis, with a Python/Streamlit front-end for data handling and visualisation.

![High-Performance Options Pricer Dashboard](./assets.option_pricer_dashboard.png)

## Features

- **High-Speed Calculations:** Core Black-Scholes and Greeks calculations, including an iterative implied volatility solver, are written in C++ and exposed to Python using `pybind11` for maximum performance.
- **IV Rank Scanner:** Scans a user-defined list of stocks to find opportunities where option premiums are historically cheap or expensive relative to their 52-week range.
- **Interactive UI:** A web-based interface built with Streamlit for intuitive analysis of option Greeks and sensitivity profiles.
- **Robust Data Pipeline:** Automatically fetches and caches daily stock price and implied volatility data in a local MySQL database to ensure fast and reliable analysis.

## Frameworks and Tools

- **Backend:** C++, pybind11
- **Frontend & Data:** Python, Streamlit, Pandas, yfinance
- **Database:** MySQL
- **Build System:** CMake

---

## Local Setup and Installation

### 1. Prerequisites

First, you'll need the foundational tools for C++ development, Python, and a database.

#### For macOS

The easiest way to get set up on a Mac is with [Homebrew](https://brew.sh/).

- **Xcode Command Line Tools:** Provides the C++ compiler.
  ```bash
  xcode-select --install
  ```
  
- **Homebrew and other tools:**
  ```bash
  brew install cmake mysql python
  ```

### 2. Clone & Build the Project

Clone the repository and compile the C++ engine. The build system is configured to automatically place the compiled module in the correct directory.

```bash
# Clone the repository and navigate into it
git clone https://github.com/Chets45/HighPerformanceOptionPricer.git
cd HighPerformanceOptionPricer

# Create a build directory
cmake -S . -B build

# Build the module
cmake --build build
```
### 3. Setting the Database up

#### **Start the MySQL Service:**

```bash
brew services start mysql
```

#### **Secure your database:**
```bash
mysql_secure_installation
```

#### **Set your password:**
```bash
export DB_PASSWORD="your_mysql_root_password"
```

#### **Create the Tables:**
```bash
mysql -u root -p"$DB_PASSWORD" < sql/schema.sql
```


### 4. Set Up the Python Environment

Using a virtual environment is highly recommended to keep dependencies clean.

```bash
# Navigate to the python directory
cd python

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate

# Install all the required packages
pip install -r requirements.txt

```
---

## Usage

With everything set up, you're ready to run the application.

### Initial Setup (Run Once)

To get started, you need to populate your database with the last year's worth of historical data. This script is designed to be run **only once**.

**Note:** This process will take several minutes as it performs thousands of calculations.

```bash
# From inside the 'python/' directory
python backfill_iv_data.py
````

### 2. Launch UI

```bash
streamlit run OptionPricerUI.py
```


### Daily Updates

These scripts are used to perform the daily incremental updates to the database, ensuring the data remains current. They should be run in order after the market closes each day.

```bash
# 1. Update the daily stock prices
python update_stock_prices.py

# 2. Calculate and store today's implied volatility
python update_daily_iv.py
```
---


## License

This project is licensed under the MIT License.

Copyright (c) 2025 Chetas Hirani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


