from utils.misc_utils import *
import yfinance as yf
import matplotlib.pyplot as plt
import re

# looks for any number of $xxxx
def find_ticker(text):
  #pattern = r"\$[a-zA-Z]{3,4}"
  pattern = r"\$([a-zA-Z]{1,4})"
  matches = re.findall(pattern, text)
  return matches

# plots recent closing price for a list of tickers, returns as base64 string
def get_recent_ticker_data(tickers):
    recent_data = yf.download(tickers, period="1y")            
    recent_data['Close'].plot()
    plt.savefig("//tmp//tick.png")
    return file_to_base64("//tmp//tick.png")

def get_stock_summary(ticker_symbols):
    """
    Fetch and return basic stock information for a list of ticker symbols.

    Parameters:
        ticker_symbols (list of str): A list of stock ticker symbols (e.g., ['AAPL', 'GOOGL']).

    Returns:
        str: A string containing the summary information for the provided ticker symbols.
    """
    results = []

    for ticker_symbol in ticker_symbols:
        try:
            # Fetch stock data
            stock = yf.Ticker(ticker_symbol)
            
            # Extract basic information
            info = stock.info

            # Prepare summary information
            summary = (f"\nBasic Stock Information for {ticker_symbol.upper()}:\n"
                       f"------------------------------------------------\n"
                       f"Company Name: {info.get('longName', 'N/A')}\n"
                       f"Sector: {info.get('sector', 'N/A')}\n"
                       f"Industry: {info.get('industry', 'N/A')}\n"
                       f"Country: {info.get('country', 'N/A')}\n"
                       f"Market Cap: {info.get('marketCap', 'N/A')}\n"
                       f"Dividend Yield: {info.get('dividendYield', 'N/A')}\n"
                       f"PE Ratio: {info.get('trailingPE', 'N/A')}\n"
                       f"Price-to-Book Ratio: {info.get('priceToBook', 'N/A')}\n"
                       f"52-Week High: {info.get('fiftyTwoWeekHigh', 'N/A')}\n"
                       f"52-Week Low: {info.get('fiftyTwoWeekLow', 'N/A')}\n"
                       f"CEO: {info.get('ceo', 'N/A')}")
            results.append(summary)
        
        except Exception as e:
            results.append(f"An error occurred while fetching data for {ticker_symbol}: {e}")

    return "\n".join(results)


