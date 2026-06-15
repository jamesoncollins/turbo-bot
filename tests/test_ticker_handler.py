from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd

from handlers.ticker_handler import (
    DEFAULT_DURATION,
    duration_to_timedelta,
    extract_ticker_symbols,
    filter_extended_market_hours,
    get_history_options,
    get_plot_segments,
    plot_stock_data_base64,
)


def test_extract_ticker_symbols_supports_arbitrary_duration_units():
    assert extract_ticker_symbols("compare $amd.10d $msft.6w $goog.18mo $spy") == [
        ("amd", "10d"),
        ("msft", "6w"),
        ("goog", "18mo"),
        ("spy", DEFAULT_DURATION),
    ]


def test_duration_to_timedelta_supports_days_weeks_months_and_years():
    assert duration_to_timedelta("10d") == timedelta(days=10)
    assert duration_to_timedelta("6w") == timedelta(weeks=6)
    assert duration_to_timedelta("18mo") == timedelta(days=540)
    assert duration_to_timedelta("2y") == timedelta(days=730)


def test_get_history_options_uses_requested_range_and_hourly_intraday():
    now = datetime(2026, 6, 15, tzinfo=timezone.utc)

    hourly_options = get_history_options("4d", now=now)
    assert hourly_options == {
        "start": now - timedelta(days=4),
        "end": now,
        "interval": "1h",
        "prepost": True,
    }

    daily_options = get_history_options("10d", now=now)
    assert daily_options == {
        "start": now - timedelta(days=10),
        "end": now,
    }


@patch("handlers.ticker_handler.file_to_base64", return_value="encoded-plot")
@patch("handlers.ticker_handler.plt")
@patch("handlers.ticker_handler.yf.Ticker")
def test_plot_uses_longest_requested_range_and_prices_in_legend(mock_ticker, mock_plt, mock_file_to_base64):
    hist = pd.DataFrame(
        {"Close": [10.0, 12.0]},
        index=pd.date_range("2026-06-01", periods=2, tz="UTC"),
    )
    ticker_instance = MagicMock()
    ticker_instance.history.return_value = hist
    mock_ticker.return_value = ticker_instance

    result = plot_stock_data_base64([("AMD", "10d")])

    assert result == "encoded-plot"
    history_kwargs = ticker_instance.history.call_args.kwargs
    assert set(history_kwargs) == {"start", "end"}
    actual_range = history_kwargs["end"] - history_kwargs["start"]
    assert timedelta(days=9, hours=23, minutes=59) < actual_range < timedelta(days=10, minutes=1)
    assert mock_ticker.call_count == 2
    assert mock_plt.text.call_count == 0
    labels = [call.kwargs["label"] for call in mock_plt.plot.call_args_list]
    assert labels == ["SPY ($10.00 → $12.00)", "AMD ($10.00 → $12.00)"]


def test_intraday_market_hours_are_filtered_and_split_by_trading_day():
    hist = pd.DataFrame(
        {"Close": [9.0, 10.0, 11.0, 12.0, 13.0, 14.0]},
        index=pd.to_datetime([
            "2026-06-15 03:00",
            "2026-06-15 04:00",
            "2026-06-15 19:00",
            "2026-06-15 21:00",
            "2026-06-16 04:00",
            "2026-06-16 20:00",
        ]).tz_localize("America/New_York"),
    )

    filtered = filter_extended_market_hours(hist)

    assert list(filtered["Close"]) == [10.0, 11.0, 13.0, 14.0]
    filtered["Normalized"] = (filtered["Close"] / filtered["Close"].iloc[0]) * 100
    segments = get_plot_segments(filtered, intraday=True)
    assert len(segments) == 2
    assert [len(x_values) for x_values, _ in segments] == [2, 2]
