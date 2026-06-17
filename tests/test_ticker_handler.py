from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from handlers.ticker_handler import (
    DEFAULT_DURATION,
    duration_to_timedelta,
    extract_ticker_symbols,
    clean_price_history,
    get_history_options,
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
        "auto_adjust": False,
        "interval": "1h",
    }

    daily_options = get_history_options("10d", now=now)
    assert daily_options == {
        "start": now - timedelta(days=10),
        "end": now,
        "auto_adjust": False,
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
    assert set(history_kwargs) == {"start", "end", "auto_adjust"}
    assert history_kwargs["auto_adjust"] is False
    actual_range = history_kwargs["end"] - history_kwargs["start"]
    assert timedelta(days=9, hours=23, minutes=59) < actual_range < timedelta(days=10, minutes=1)
    assert mock_ticker.call_count == 2
    assert mock_plt.text.call_count == 0
    labels = [call.kwargs["label"] for call in mock_plt.plot.call_args_list]
    assert labels == ["SPY ($10.00 → $12.00)", "AMD ($10.00 → $12.00)"]


def test_clean_price_history_removes_zero_and_missing_close_values():
    hist = pd.DataFrame(
        {"Close": [10.0, None, 0.0, 12.0]},
        index=pd.date_range("2026-06-01", periods=4, tz="UTC"),
    )

    cleaned = clean_price_history(hist)

    assert cleaned["Close"].tolist() == [10.0, 12.0]


@patch("handlers.ticker_handler.file_to_base64", return_value="encoded-plot")
@patch("handlers.ticker_handler.plt")
@patch("handlers.ticker_handler.yf.Ticker")
def test_plot_ignores_zero_close_rows_when_labeling_and_normalizing(mock_ticker, mock_plt, mock_file_to_base64):
    hist = pd.DataFrame(
        {"Close": [10.0, 11.0, 0.0]},
        index=pd.date_range("2026-06-01", periods=3, tz="UTC"),
    )
    ticker_instance = MagicMock()
    ticker_instance.history.return_value = hist
    mock_ticker.return_value = ticker_instance

    result = plot_stock_data_base64([("SPCM", "10d")])

    assert result == "encoded-plot"
    labels = [call.kwargs["label"] for call in mock_plt.plot.call_args_list]
    assert labels == ["SPY ($10.00 → $11.00)", "SPCM ($10.00 → $11.00)"]
    plotted_values = [call.args[1].tolist() for call in mock_plt.plot.call_args_list]
    assert plotted_values[0] == pytest.approx([100.0, 110.0])
    assert plotted_values[1] == pytest.approx([100.0, 110.0])
