import unittest

import pandas as pd

from handlers.ticker_handler import clean_history_for_plot


class TickerHandlerTest(unittest.TestCase):
    def test_clean_history_for_plot_drops_trailing_zero_close(self):
        hist = pd.DataFrame(
            {"Close": [10.0, 11.0, 0.0]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_history_for_plot(hist)

        self.assertEqual(cleaned["Close"].tolist(), [10.0, 11.0])
        self.assertEqual(cleaned.index[-1], pd.Timestamp("2026-06-15"))

    def test_clean_history_for_plot_drops_missing_close(self):
        hist = pd.DataFrame(
            {"Close": [10.0, None, 12.0]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_history_for_plot(hist)

        self.assertEqual(cleaned["Close"].tolist(), [10.0, 12.0])

    def test_clean_history_for_plot_drops_zero_volume_placeholders(self):
        hist = pd.DataFrame(
            {"Close": [20320.33, 21425.08, 13.69], "Volume": [0, 0, 9986045]},
            index=pd.to_datetime(["2026-06-12", "2026-06-15", "2026-06-16"]),
        )

        cleaned = clean_history_for_plot(hist)

        self.assertEqual(cleaned["Close"].tolist(), [13.69])
        self.assertEqual(cleaned["Volume"].tolist(), [9986045])


if __name__ == "__main__":
    unittest.main()
