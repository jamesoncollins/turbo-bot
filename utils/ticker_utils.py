from utils.misc_utils import *
import yfinance as yf
import re
import matplotlib.pyplot as plt

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

def extract_ticker_symbols(input_string):
    """
    Extract ticker symbols from a string if they are prefixed with '$', including optional duration.

    Parameters:
        input_string (str): The input string to parse.

    Returns:
        list of tuples: A list of tuples where each tuple contains a ticker symbol and a duration.
    """
    matches = re.findall(r'\$(\w+)(?:\.(\w+))?', input_string)
    return [(symbol, duration if duration else "1y") for symbol, duration in matches]

def plot_stock_data_base64(ticker_symbols):
    """
    Plot the historical closing prices for a list of ticker symbols and return the plot as a base64 string.

    Parameters:
        ticker_symbols (list of tuples): A list of tuples where each tuple contains a stock ticker symbol and a duration.

    Returns:
        str: The base64 string of the generated plot.
    """
    plt.figure(figsize=(10, 6))

    for ticker_symbol, duration in ticker_symbols:
        try:
            # Fetch historical market data
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(period=duration)

            # Plot closing prices
            plt.plot(hist.index, hist["Close"], label=f"{ticker_symbol.upper()} ({duration})")
        except Exception as e:
            print(f"An error occurred while fetching data for {ticker_symbol}: {e}")

    # Add labels, title, and legend
    plt.xlabel("Date")
    plt.ylabel("Closing Price (USD)")
    plt.title("Historical Closing Prices")
    plt.legend()
    plt.grid()

    # Save the plot to a temporary file and convert to base64
    filename = "temp_plot.png"
    plt.savefig(filename)
    plt.close()

    # Convert file to base64
    base64_string = file_to_base64(filename)
    return base64_string

if __name__ == "__main__":
    # Prompt the user for input containing ticker symbols
    input_text = input("Enter a string containing stock ticker symbols prefixed with '$' (e.g., '$AMD.1y $AAPL.6mo'): ").strip()

    # Extract ticker symbols and durations from the input string
    tickers = extract_ticker_symbols(input_text)

    if tickers:
        summary = get_stock_summary([symbol for symbol, _ in tickers])
        print(summary)

        # Generate base64 plot
        base64_plot = plot_stock_data_base64(tickers)
        print("Base64 Plot:", base64_plot)
    else:
        print(None)
