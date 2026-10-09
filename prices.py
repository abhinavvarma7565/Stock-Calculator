import time

import numpy as np

cache = {}          # symbol -> (time fetched, closes)
ttl = 15 * 60       # keep prices for 15 minutes so we don't keep hitting yahoo

tryagain = ' Try again, or enter the current price and volatility under Advanced.'


class PriceError(Exception):
    pass


def history(sym, years=2):
    # daily closes (adjusted for splits and dividends) as a numpy array
    hit = cache.get(sym)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]

    try:
        import yfinance as yf
        df = yf.Ticker(sym).history(period='{}y'.format(years), auto_adjust=True, timeout=10)
    except Exception:
        raise PriceError("Couldn't get prices for {} right now.".format(sym) + tryagain)

    if df is None or df.empty or 'Close' not in df:
        raise PriceError('No price history found for {}. Check the symbol.'.format(sym) + tryagain)

    closes = df['Close'].dropna().to_numpy(dtype=float)
    closes = closes[closes > 0]
    if len(closes) < 60:
        raise PriceError('Not enough price history for {} to work out volatility.'.format(sym) + tryagain)

    cache[sym] = (time.time(), closes)
    return closes


def stats(closes):
    # last price, yearly volatility and the daily log returns
    r = np.diff(np.log(closes))
    return float(closes[-1]), float(r.std(ddof=1) * np.sqrt(252)), r
