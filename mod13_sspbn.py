## imports
import requests
import pandas as pd
import os
import io
import pygal
from pygal.style import *
import unittest

class TestStockVisualizerInputs(unittest.TestCase):

    def test_symbol_validation(self):
        self.assertTrue(validate_symbol("GOOGL"))
        self.assertTrue(validate_symbol("IBM"))
        
        self.assertFalse(validate_symbol("Googl"))
        self.assertFalse(validate_symbol("TOOLONGNAME"))
        self.assertFalse(validate_symbol("123"))
        self.assertFalse(validate_symbol("a  b"))

    def test_chart_type_validation(self):
        self.assertTrue(validate_chart_type("1"))
        self.assertTrue(validate_chart_type("2"))
        
        self.assertFalse(validate_chart_type("3"))
        self.assertFalse(validate_chart_type("a"))

    def test_time_series_validation(self):
        self.assertTrue(validate_time_series("1"))
        self.assertTrue(validate_time_series("2"))
        self.assertTrue(validate_time_series("3"))
        self.assertTrue(validate_time_series("4"))
        
        self.assertFalse(validate_time_series("5"))
        self.assertFalse(validate_time_series("0"))

    def test_date_validation(self):
        self.assertTrue(validate_date("2023-01-01"))
        self.assertTrue(validate_date("2000-12-31"))
        
        self.assertFalse(validate_date("01-01-2023"))
        self.assertFalse(validate_date("2023/01/01"))
        self.assertFalse(validate_date("2023-13-01"))
        self.assertFalse(validate_date("abcd-ef-gh"))


# function to fetch data through API connection using user input
def fetch_data_through_api(symbol, api_key, function, interval = None):
    url = "https://www.alphavantage.co/query"
    
    # parameters for the request
    params = {
        "function": function,  
        "symbol": symbol,
        "outputsize": "full",
        "datatype": "csv",
        "apikey": api_key
    }
    
    if function == "TIME_SERIES_INTRADAY":
        params["interval"] = interval or "60min"
    
    try:
        # make the request
        response = requests.get(url, params=params)
        response.raise_for_status()  # will raise an error if the request failed
        
        df = pd.read_csv(io.StringIO(response.text))
        
        expected_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        if not expected_cols.issubset(df.columns):
            print("\n***********************\nUnexpected data format from API.\n***********************\n")
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
        
        # now the timestamp is the index, so we can do df.loc[start_date:end_date] with our dataframe
        df = df.set_index('timestamp')
        df = df.sort_index()
        
        return df
    except requests.exceptions.RequestException:
        print("\nAPI Request failed.")
    except Exception as e:
        print(f"\nFailed to process data: {e}")
        
    return None

def validate_symbol(symbol):
    return symbol.isalpha() and symbol.isupper() and 1 <= len(symbol) <= 7

def validate_chart_type(chart_num):
    return chart_num in ["1", "2"]

def validate_time_series(time_series_option):
    return time_series_option in ["1", "2", "3", "4"]

def validate_date(date_str):
    timestamp = pd.to_datetime(date_str, format='%Y-%m-%d', errors='coerce')
    return not pd.isna(timestamp)

# function to get and validate user input
def get_user_input():
    print("Stock Data Visualizer\n-------------------------")
    
    # get stock symbol
    # i dont see a way to query the db to see if the symbol is in there, will just have to TRY/CATCH and see if it works lol
    while True:
        symbol = input("\nEnter the stock symbol you are looking for: ")
        if validate_symbol(symbol):
            break
        else:
            print("Invalid symbol. Must be 1-7 letters.")
    
    chart_type = ""
    while True:
        print("\nChart Types\n---------------------")
        print("1. Bar")
        print("2. Line\n")
        chart_num = input("Enter the chart type you want (1, 2): ")
        
        if validate_chart_type(chart_num):
            if chart_num == "1": 
                chart_type = "Bar"
            if chart_num == "2": 
                chart_type = "Line"
            break
        else:
            print("Enter a 1 or 2 for chart type")
    
    # get time series choice
    time_series = ""
    interval = None
    while(True):    
        print("\nSelect the Time Series of the chart you want to generate\n-------------------------------------")
        print("1. Intraday")
        print("2. Daily")
        print("3. Weekly")
        print("4. Monthly")
        
        time_series_option = input("\nEnter time series option (1, 2, 3, 4): ")

        if validate_time_series(time_series_option):
            if time_series_option == "1":
                time_series = "TIME_SERIES_INTRADAY"
                while(True): 
                    print("\nSelect the time interval for the chart\n-------------------------------------")
                    print("1. 1 minute")
                    print("2. 5 minutes")
                    print("3. 15 minutes")
                    print("4. 30 minutes")
                    print("5. 60 minutes")
                    interval_option = input("Enter interval option (1, 2, 3, 4, 5): ")
                    if interval_option == "1":
                        interval = "1min"
                    elif interval_option == "2":
                        interval = "5min"
                    elif interval_option == "3":
                        interval = "15min"
                    elif interval_option == "4":
                        interval = "30min"
                    elif interval_option == "5":
                        interval = "60min"
                    else:
                        print("Please enter 1, 2, 3, 4, or 5 for interval option.")
                        continue
                    break

            elif time_series_option == "2":
                time_series = "TIME_SERIES_DAILY"
            elif time_series_option == "3":
                time_series = "TIME_SERIES_WEEKLY"
            elif time_series_option == "4":
                time_series = "TIME_SERIES_MONTHLY"        
            break
    
    # get start and end dates, make sure start date < end date
    while True:
        start_date_str = input("\nEnter the start date (YYYY-MM-DD): ")
        if not validate_date(start_date_str):
            print("Invalid Start Date format. Please use YYYY-MM-DD.")
            continue
           
        start_date = pd.to_datetime(start_date_str)
        
        if start_date < pd.Timestamp("2000-01-01"):
            print("Start date must be after 2000-01-01.")
            continue
            
        end_date_str = input("\nEnter the end date (YYYY-MM-DD): ")
        if not validate_date(end_date_str):
            print("Invalid End Date format. Please use YYYY-MM-DD.")
            continue
        
        end_date = pd.to_datetime(end_date_str)
        
        if start_date < end_date:
            break
        else:
            print("Start date must be earlier than end date.")
            
    return symbol, chart_type, time_series, interval, start_date, end_date
    
# function to parse data and send data to graph
def get_data(symbol, chart_type, time_series, interval, start_date, end_date):
    API_KEY = os.getenv("ALPHAVANTAGE_API_KEY", "38Z6ROU8EAKF0E9C")

    df = fetch_data_through_api(symbol, API_KEY, time_series, interval)
    
    # if the data was not fetched for whatever reason, get_data should return None or may just be empty
    if df is None or df.empty:
        print("\n***********************\nNo data fetched. Please try a different symbol or date range.\n***********************\n")
        return None
    
    filtered_df = df.loc[start_date:end_date]
    
    print(f"\nFetched {len(df)} records for {symbol}.")
    print(f"Displaying data from {start_date.date()} to {end_date.date()}: {len(filtered_df)} records.")
    print(f"Will use {chart_type} chart\n")
    
    return filtered_df

# function to display graph to users browser
def display_data_to_user(df, symbol, chart_type, start_date, end_date):
    if df is None or df.empty:
        print("\n***********************\nNo data available to display.\n***********************\n")
        return
    
    if chart_type == "Line":
        create_line_chart(df, symbol, start_date, end_date)
    elif chart_type == "Bar":
        create_bar_chart(df, symbol, start_date, end_date)
    else:
        print("\n***********************\nUnsupported chart type\n***********************\n")

#function to create line chart
def create_line_chart(df, symbol, start_date, end_date):
    line_chart = pygal.Line(
        style=LightStyle, 
        x_label_rotation=20, 
        show_minor_x_labels=False,
        truncate_label=10,
        show_legend=True
    )
    line_chart.title = f"Stock Data for {symbol}: {start_date.date()} to {end_date.date()}"
    line_chart.x_labels = [x.strftime("%Y-%m-%d") for x in df.index]

    line_chart.add("Open", df['open'].tolist())
    line_chart.add("High", df['high'].tolist())
    line_chart.add("Low", df['low'].tolist())
    line_chart.add("Close", df['close'].tolist())

    line_chart.render_in_browser()

#function to create bar chart
def create_bar_chart(df, symbol, start_date, end_date):
    bar_chart = pygal.Bar(
        style=LightStyle, 
        x_label_rotation=20, 
        show_minor_x_labels=False,
        truncate_label=10,
        show_legend=True
    )
    bar_chart.title = f"Stock Data for {symbol}: {start_date.date()} to {end_date.date()}"
    bar_chart.x_labels = [x.strftime("%Y-%m-%d") for x in df.index]

    bar_chart.add("Open", df['open'].tolist())
    bar_chart.add("High", df['high'].tolist())
    bar_chart.add("Low", df['low'].tolist())
    bar_chart.add("Close", df['close'].tolist())

    bar_chart.render_in_browser()

def main():
    while(True):
        symbol, chart_type, time_series, interval, start_date, end_date = get_user_input()
        result = get_data(symbol, chart_type, time_series, interval, start_date, end_date)
        
        # handling error while fetching data so that it doesn't break the program
        if result is None:
            continue
        
        print("\nGenerating chart... Please wait.\n")
        display_data_to_user(result, symbol, chart_type, start_date, end_date)
        
        view_again = input("Would you like to view more stock data? Press 'y' to continue: ").lower()
        
        if view_again == "y":
            continue
        else:
            print("Hope you enjoyed!")
            break
    
if __name__ == "__main__":
    unittest.main(exit = False)
    main()  
