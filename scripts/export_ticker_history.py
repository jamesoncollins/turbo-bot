import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import yfinance as yf

from handlers.ticker_handler import (
    RECENT_INTRADAY_INTERVAL,
    RECENT_INTRADAY_PERIOD,
    clean_price_history,
    fetch_price_history,
    get_history_options,
    keep_latest_session,
)


def export_frame(frame, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index_label="DateTime")


def export_ticker(symbol, duration, output_dir):
    stock = yf.Ticker(symbol)
    history_options = get_history_options(duration)

    raw_daily = stock.history(**history_options)
    clean_daily = clean_price_history(raw_daily)
    raw_intraday = stock.history(
        period=RECENT_INTRADAY_PERIOD,
        interval=RECENT_INTRADAY_INTERVAL,
        auto_adjust=False,
    )
    clean_intraday = clean_price_history(raw_intraday)
    latest_intraday = keep_latest_session(clean_intraday)
    selected = fetch_price_history(stock, history_options)

    ticker_dir = output_dir / symbol.upper()
    frames = {
        "raw_daily": raw_daily,
        "clean_daily": clean_daily,
        "raw_intraday": raw_intraday,
        "clean_intraday": clean_intraday,
        "latest_intraday": latest_intraday,
        "selected_for_plot": selected,
    }
    for name, frame in frames.items():
        export_frame(frame, ticker_dir / f"{name}.csv")

    summary_path = ticker_dir / "summary.txt"
    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write(f"symbol={symbol.upper()}\n")
        summary.write(f"duration={duration}\n")
        summary.write(f"history_options={history_options}\n")
        for name, frame in frames.items():
            summary.write(f"\n{name}\n")
            summary.write(f"rows={len(frame)}\n")
            if frame.empty:
                continue
            summary.write(f"first_index={frame.index[0]}\n")
            summary.write(f"last_index={frame.index[-1]}\n")
            columns = [column for column in ("Close", "Volume") if column in frame.columns]
            if columns:
                summary.write(frame[columns].tail(10).to_string())
                summary.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Export yfinance ticker history diagnostics.")
    parser.add_argument("symbols", nargs="+", help="Ticker symbols to export")
    parser.add_argument("--duration", default="1y", help="Duration to inspect, e.g. 10d, 1mo, 1y")
    parser.add_argument("--output-dir", default=None, help="Directory for exported CSV files")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        output_dir = REPO_ROOT / "tmp" / f"ticker_history_{stamp}"

    for symbol in args.symbols:
        export_ticker(symbol, args.duration, output_dir)

    print(output_dir)


if __name__ == "__main__":
    main()
