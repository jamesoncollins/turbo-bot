from datetime import datetime, time as datetime_time, timedelta, timezone
from zoneinfo import ZoneInfo
from handlers.base_handler import BaseHandler
from utils.misc_utils import *
import yfinance as yf
import re
import matplotlib.pyplot as plt

DEFAULT_DURATION = "1y"
INTRADAY_THRESHOLD_DAYS = 5
MARKET_TIMEZONE = ZoneInfo("America/New_York")
EXTENDED_MARKET_OPEN = datetime_time(4, 0)
EXTENDED_MARKET_CLOSE = datetime_time(20, 0)


class TickerHandler(BaseHandler):

    def can_handle(self) -> bool:
        self.tickers = extract_ticker_symbols(self.input_str)
        return (len(self.tickers) > 0)

    def process_message(self, msg, attachments):
        if self.tickers:
            return {
                "message": get_stock_summary(convert_to_get_stock_summary_input(self.tickers)),
                "attachments": [plot_stock_data_base64(self.tickers)],
            }
        return []

    @staticmethod
    def get_name() -> str:
        return "TickerHandler"

    @staticmethod
    def get_help_text() -> str:
        retval = "Gets stock info for any ticker after '$'.  i.e. $amd. \n"
        retval += "Optionally add a duration, i.e. $amd.5y, $msft.10d, $spy.18mo.   \n"
        return retval


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
            stock = yf.Ticker(ticker_symbol)
            info = stock.info
            summary = (f"\nBasic Stock Information for {ticker_symbol.upper()}:\n"
                       f"----------------------------\n"
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
    """
    matches = re.findall(r'\$([a-zA-Z][\w-]*)(?:\.([a-zA-Z0-9]+))?', input_string)
    return [(symbol, duration.lower() if duration else DEFAULT_DURATION) for symbol, duration in matches]


def convert_to_get_stock_summary_input(ticker_tuples):
    return [symbol for symbol, _ in ticker_tuples]


def duration_to_timedelta(duration):
    """Convert a user supplied duration like 10d, 6w, 18mo, or 3y to a timedelta."""
    match = re.fullmatch(r'(\d+)(d|w|mo|m|y)', duration.lower())
    if not match:
        raise ValueError(f"Unsupported duration '{duration}'. Use a number followed by d, w, mo/m, or y.")

    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        raise ValueError("Duration must be greater than zero.")

    if unit == 'd':
        return timedelta(days=amount)
    if unit == 'w':
        return timedelta(weeks=amount)
    if unit in ('mo', 'm'):
        return timedelta(days=amount * 30)
    if unit == 'y':
        return timedelta(days=amount * 365)
    raise ValueError(f"Unsupported duration unit '{unit}'.")


def get_history_options(duration, now=None):
    """Build yfinance history options for arbitrary durations."""
    now = now or datetime.now(timezone.utc)
    delta = duration_to_timedelta(duration)
    options = {"start": now - delta, "end": now}
    if delta <= timedelta(days=INTRADAY_THRESHOLD_DAYS):
        options["interval"] = "1h"
        options["prepost"] = True
    return options


def is_intraday_history(history_options):
    return history_options.get("interval") == "1h"


def filter_extended_market_hours(hist):
    """Keep only pre-market, regular-market, and post-market rows for intraday charts."""
    if hist.empty:
        return hist

    eastern_index = hist.index
    if eastern_index.tz is None:
        eastern_index = eastern_index.tz_localize(timezone.utc)
    eastern_index = eastern_index.tz_convert(MARKET_TIMEZONE)

    market_hours_mask = [
        EXTENDED_MARKET_OPEN <= timestamp.time() <= EXTENDED_MARKET_CLOSE
        for timestamp in eastern_index
    ]
    filtered = hist.loc[market_hours_mask].copy()
    filtered.index = eastern_index[market_hours_mask]
    return filtered


def get_plot_segments(hist, intraday=False):
    """Split intraday plots by trading date so lines are not drawn overnight."""
    if not intraday:
        return [(hist.index, hist["Normalized"])]

    return [
        (daily_hist.index, daily_hist["Normalized"])
        for _, daily_hist in hist.groupby(hist.index.date)
        if not daily_hist.empty
    ]


def format_price(value):
    return f"${value:.2f}"


def plot_stock_data_base64(ticker_symbols):
    """
    Plot historical prices for a list of ticker symbols as percentage changes.

    Always includes $SPY. Uses the longest supplied duration for every ticker so each
    line is plotted over the same requested time range. Intraday ranges up to five
    days use hourly granularity.
    """
    plt.figure(figsize=(10, 6))

    tickers_to_plot = list(ticker_symbols)
    longest_duration = max(
        (duration for _, duration in tickers_to_plot),
        key=lambda duration: duration_to_timedelta(duration),
    )
    if not any(ticker_symbol.lower() == "spy" for ticker_symbol, _ in tickers_to_plot):
        tickers_to_plot.insert(0, ("SPY", longest_duration))

    history_options = get_history_options(longest_duration)
    intraday = is_intraday_history(history_options)

    plotted_any_series = False

    for ticker_symbol, _ in tickers_to_plot:
        try:
            stock = yf.Ticker(ticker_symbol)
            hist = stock.history(**history_options)
            if intraday:
                hist = filter_extended_market_hours(hist)
            if hist.empty:
                print(f"No historical data found for {ticker_symbol}")
                continue

            hist["Normalized"] = (hist["Close"] / hist["Close"].iloc[0]) * 100
            start_price = format_price(hist["Close"].iloc[0])
            end_price = format_price(hist["Close"].iloc[-1])
            label = f"{ticker_symbol.upper()} ({start_price} → {end_price})"
            label_pending = True
            for x_values, y_values in get_plot_segments(hist, intraday=intraday):
                plt.plot(x_values, y_values, label=label if label_pending else None)
                label_pending = False
                plotted_any_series = True
        except Exception as e:
            print(f"An error occurred while fetching data for {ticker_symbol}: {e}")

    plt.xlabel("Date")
    plt.ylabel("Normalized Price (%)")
    interval_description = "hourly" if intraday else "daily"
    plt.title(f"Historical Prices (Normalized, {longest_duration}, {interval_description})")
    if plotted_any_series:
        plt.legend()
    plt.grid()

    filename = "temp_plot.png"
    plt.savefig(filename)
    plt.close()

    return file_to_base64(filename)
