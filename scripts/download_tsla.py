"""Download real Yahoo Finance TSLA OHLCV; never substitute sample data."""
import json
import logging
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'outputs' / 'tsla'
out.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.WARNING, handlers=[logging.StreamHandler(), logging.FileHandler(out / 'download.log', mode='w')])
yf.config.debug.hide_exceptions = False
report = {'ticker': 'TSLA', 'start': '2021-10-17', 'end_exclusive': '2026-10-17', 'interval': '1d', 'auto_adjust': False, 'yfinance_version': yf.__version__}
try:
    data = yf.Ticker('TSLA').history(start=report['start'], end=report['end_exclusive'], interval='1d', auto_adjust=False, actions=False, timeout=30)
    if data.empty:
        raise RuntimeError('Yahoo Finance returned no historical rows.')
    data = data[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    assert data.index.is_unique and data.index.is_monotonic_increasing
    assert not data.isna().any().any(), 'Missing OHLCV values'
    data.index = data.index.tz_localize(None)
    data.index.name = 'Date'
    csv = out / 'TSLA_5y_daily_OHLCV.csv'
    data.to_csv(csv, date_format='%Y-%m-%d')
    check = pd.read_csv(csv, index_col='Date', parse_dates=True)
    check.index = check.index.as_unit(data.index.unit)
    pd.testing.assert_frame_equal(data, check, check_freq=False, check_dtype=False)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(data.index, data['Close'], linewidth=1)
    ax.set(title='TSLA daily closing price — 5 years', xlabel='Date', ylabel='Closing price (USD)')
    ax.grid(alpha=0.25)
    fig.tight_layout()
    png = out / 'TSLA_5y_closing_prices.png'
    fig.savefig(png, dpi=160)
    plt.close(fig)
    assert png.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
    report.update(status='success', trading_sessions=len(data), first_session=str(data.index[0].date()), latest_session=str(data.index[-1].date()), latest_close_usd=float(data['Close'].iloc[-1]), csv_verified=True, png_verified=True)
except Exception as exc:
    logging.exception('TSLA download or verification failed')
    report.update(status='error', error_type=type(exc).__name__, error=str(exc), trading_sessions_downloaded=0, latest_close_usd=None)
finally:
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
if report['status'] != 'success':
    sys.exit(1)
