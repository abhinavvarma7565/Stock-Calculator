import types

import numpy as np
import pandas as pd
import pytest

import prices


def fakeyf(monkeypatch, df=None, boom=None):
    # stand in for yfinance so the tests don't need the internet
    calls = []

    class Ticker:
        def __init__(self, sym):
            calls.append(sym)

        def history(self, **kw):
            if boom:
                raise boom
            return df

    monkeypatch.setitem(__import__('sys').modules, 'yfinance', types.SimpleNamespace(Ticker=Ticker))
    return calls


@pytest.fixture(autouse=True)
def fresh_cache():
    prices.cache.clear()


def closes(n, nan_at=None):
    c = 100 + np.arange(n, dtype=float)
    if nan_at is not None:
        c[nan_at] = np.nan
    return pd.DataFrame({'Close': c})


def test_history_gives_clean_closes(monkeypatch):
    fakeyf(monkeypatch, df=closes(100, nan_at=5))
    c = prices.history('ABC')
    assert len(c) == 99
    assert not np.isnan(c).any()
    assert c[-1] == 199


def test_history_is_cached(monkeypatch):
    calls = fakeyf(monkeypatch, df=closes(100))
    prices.history('ABC')
    prices.history('ABC')
    assert calls == ['ABC']
    prices.history('XYZ')
    assert calls == ['ABC', 'XYZ']


def test_cache_expires(monkeypatch):
    calls = fakeyf(monkeypatch, df=closes(100))
    prices.history('ABC')
    when, c = prices.cache['ABC']
    prices.cache['ABC'] = (when - prices.ttl - 1, c)
    prices.history('ABC')
    assert calls == ['ABC', 'ABC']


def test_network_error(monkeypatch):
    fakeyf(monkeypatch, boom=ConnectionError('no route to host'))
    with pytest.raises(prices.PriceError) as e:
        prices.history('ABC')
    assert "Couldn't get prices for ABC" in str(e.value)
    assert 'no route' not in str(e.value)       # raw error text isn't shown to the user


def test_unknown_symbol(monkeypatch):
    fakeyf(monkeypatch, df=pd.DataFrame())
    with pytest.raises(prices.PriceError) as e:
        prices.history('NOPE')
    assert 'No price history found for NOPE' in str(e.value)


def test_not_enough_history(monkeypatch):
    fakeyf(monkeypatch, df=closes(30))
    with pytest.raises(prices.PriceError) as e:
        prices.history('NEW')
    assert 'Not enough price history' in str(e.value)


def test_failed_lookups_are_not_cached(monkeypatch):
    fakeyf(monkeypatch, boom=ConnectionError())
    with pytest.raises(prices.PriceError):
        prices.history('ABC')
    assert 'ABC' not in prices.cache


def test_stats():
    # made up prices with a known 30% yearly vol
    r = np.random.default_rng(4).normal(0, 0.30 / np.sqrt(252), 5000)
    c = 50 * np.exp(np.cumsum(r))
    last, vol, hist = prices.stats(c)
    assert last == pytest.approx(c[-1])
    assert vol == pytest.approx(0.30, rel=0.05)
    assert len(hist) == len(c) - 1
