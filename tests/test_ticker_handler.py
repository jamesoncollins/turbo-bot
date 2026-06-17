from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from handlers.ticker_handler import (
    DEFAULT_DURATION,
    clean_history_for_plot,
    clean_price_history,
    duration_to_timedelta,
    extract_ticker_symbols,
    get_history_options,
    plot_stock_data_base64,
)


class TickerHandlerTest(unittest.TestCase):
    def test_extract_ticker_symbols_supports_arbitrary_duration_units(self):
        self.assertEqual(
            extract_ticker_symbols("compare $amd.10d $msft.6w $goog.18mo $spy"),
            [
                ("amd", "10d"),
                ("msft", "6w"),
                ("goog", "18mo"),
                ("spy", DEFAULT_DURATION),
            ],
        )

    def test_duration_to_timedelta_supports_days_weeks_months_and_years(self):
        self.assertEqual(duration_to_timedelta("10d"), timedelta(days=10))
        self.assertEqual(duration_to_timedelta("6w"), timedelta(weeks=6))
        self.assertEqual(duration_to_timedelta("18mo"), timedelta(days=540))
        self.assertEqual(duration_to_timedelta("2y"), timedelta(days=730))

    def test_get_history_options_uses_requested_range_and_hourly_intraday(self):
        now = datetime(2026, 6, 15, tzinfo=timezone.utc)

        hourly_options = get_history_options("4d", now=now)
        self.assertEqual(
            hourly_options,
            {
                "start": now - timedelta(days=4),
                "end": now,
                "auto_adjust": False,
                "interval": "1h",
            },
        )

        daily_options = get_history_options("10d", now=now)
        self.assertEqual(
            daily_options,
            {
                "start": now - timedelta(days=10),
                "end": now,
                "auto_adjust": False,
            },
        )

    def test_clean_price_history_drops_trailing_zero_close(self):
        hist = pd.DataFrame(
            {"Close": [10.0, 11.0, 0.0]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_price_history(hist)

        self.assertEqual(cleaned["Close"].tolist(), [10.0, 11.0])
        self.assertEqual(cleaned.index[-1], pd.Timestamp("2026-06-15"))

    def test_clean_price_history_drops_missing_close(self):
        hist = pd.DataFrame(
            {"Close": [10.0, None, 12.0]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_price_history(hist)

        self.assertEqual(cleaned["Close"].tolist(), [10.0, 12.0])

    def test_clean_price_history_drops_zero_volume_placeholders(self):
        hist = pd.DataFrame(
            {"Close": [20320.33, 21425.08, 13.69], "Volume": [0, 0, 9986045]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_price_history(hist)

        self.assertEqual(cleaned["Close"].tolist(), [13.69])
        self.assertEqual(cleaned["Volume"].tolist(), [9986045])

    def test_clean_history_for_plot_aliases_clean_price_history(self):
        hist = pd.DataFrame({"Close": [10.0, 0.0]})

        self.assertEqual(clean_history_for_plot(hist)["Close"].tolist(), [10.0])

    @patch("handlers.ticker_handler.file_to_base64", return_value="encoded-plot")
    @patch("handlers.ticker_handler.plt")
    @patch("handlers.ticker_handler.yf.Ticker")
    def test_plot_uses_longest_requested_range_and_prices_in_legend(
        self,
        mock_ticker,
        mock_plt,
        mock_file_to_base64,
    ):
        hist = pd.DataFrame(
            {"Close": [10.0, 12.0]},
            index=pd.date_range("2026-06-01", periods=2, tz="UTC"),
        )
        ticker_instance = MagicMock()
        ticker_instance.history.return_value = hist
        mock_ticker.return_value = ticker_instance

        result = plot_stock_data_base64([("AMD", "10d")])

        self.assertEqual(result, "encoded-plot")
        history_kwargs = ticker_instance.history.call_args.kwargs
        self.assertEqual(set(history_kwargs), {"start", "end", "auto_adjust"})
        self.assertIs(history_kwargs["auto_adjust"], False)
        actual_range = history_kwargs["end"] - history_kwargs["start"]
        self.assertGreater(actual_range, timedelta(days=9, hours=23, minutes=59))
        self.assertLess(actual_range, timedelta(days=10, minutes=1))
        self.assertEqual(mock_ticker.call_count, 2)
        self.assertEqual(mock_plt.text.call_count, 0)
        labels = [call.kwargs["label"] for call in mock_plt.plot.call_args_list]
        self.assertEqual(labels, ["SPY ($10.00 -> $12.00)", "AMD ($10.00 -> $12.00)"])

    @patch("handlers.ticker_handler.file_to_base64", return_value="encoded-plot")
    @patch("handlers.ticker_handler.plt")
    @patch("handlers.ticker_handler.yf.Ticker")
    def test_plot_ignores_zero_close_rows_when_labeling_and_normalizing(
        self,
        mock_ticker,
        mock_plt,
        mock_file_to_base64,
    ):
        hist = pd.DataFrame(
            {"Close": [10.0, 11.0, 0.0]},
            index=pd.date_range("2026-06-01", periods=3, tz="UTC"),
        )
        ticker_instance = MagicMock()
        ticker_instance.history.return_value = hist
        mock_ticker.return_value = ticker_instance

        result = plot_stock_data_base64([("SPCM", "10d")])

        self.assertEqual(result, "encoded-plot")
        labels = [call.kwargs["label"] for call in mock_plt.plot.call_args_list]
        self.assertEqual(labels, ["SPY ($10.00 -> $11.00)", "SPCM ($10.00 -> $11.00)"])
        plotted_values = [call.args[1].tolist() for call in mock_plt.plot.call_args_list]
        for values in plotted_values:
            self.assertEqual(len(values), 2)
            self.assertAlmostEqual(values[0], 100.0)
            self.assertAlmostEqual(values[1], 110.0)


if __name__ == "__main__":
    unittest.main()
