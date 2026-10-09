import math

import numpy as np
import pytest

import sim
from calc import calc

pos = dict(allotment=100, iniprice=10, buycmm=5, sellcmm=5, cptlgain=15)


def kurt(p):
    # excess kurtosis of the daily log returns, 0 for a normal curve
    r = np.diff(np.log(p), axis=1).ravel()
    z = (r - r.mean()) / r.std()
    return (z ** 4).mean() - 3


def test_flat_when_no_vol_and_no_drift():
    p = sim.paths(100, vol=0, drift=0, ndays=21, npaths=50, seed=1)
    assert p.shape == (50, 22)
    assert np.allclose(p, 100)


def test_drift_only():
    p = sim.paths(100, vol=0, drift=0.10, ndays=252, npaths=5, seed=1)
    assert p[:, -1] == pytest.approx(100 * math.exp(0.10))


def test_first_column_is_the_current_price():
    p = sim.paths(42.5, vol=0.3, drift=0.05, ndays=10, npaths=100, seed=1)
    assert (p[:, 0] == 42.5).all()


def test_average_end_price_follows_the_drift():
    p = sim.paths(100, vol=0.3, drift=0.08, ndays=252, npaths=200000, seed=7)
    assert p[:, -1].mean() / 100 == pytest.approx(math.exp(0.08), abs=0.005)


@pytest.mark.parametrize('hist', [None, np.random.default_rng(3).standard_t(4, 500) * 0.01])
def test_daily_moves_have_the_vol_we_asked_for(hist):
    p = sim.paths(100, vol=0.25, drift=0, ndays=252, hist=hist, npaths=2000, seed=5)
    r = np.diff(np.log(p), axis=1)
    assert r.std() * math.sqrt(252) == pytest.approx(0.25, rel=0.02)


def test_resampling_keeps_the_fat_tails():
    hist = np.random.default_rng(3).standard_t(3, 750) * 0.01
    normal = sim.paths(100, vol=0.3, drift=0, ndays=63, npaths=5000, seed=2)
    resampled = sim.paths(100, vol=0.3, drift=0, ndays=63, hist=hist, npaths=5000, seed=2)
    assert abs(kurt(normal)) < 0.3
    assert kurt(resampled) > 1


def test_same_seed_same_paths():
    a = sim.paths(100, 0.3, 0.05, 30, npaths=100, seed=11)
    b = sim.paths(100, 0.3, 0.05, 30, npaths=100, seed=11)
    c = sim.paths(100, 0.3, 0.05, 30, npaths=100, seed=12)
    assert (a == b).all()
    assert not (a == c).all()


@pytest.mark.parametrize('curprice, vol, ndays, npaths', [(0, 0.3, 10, 10), (-5, 0.3, 10, 10),
                                                         (10, -0.1, 10, 10), (10, 0.3, 0, 10),
                                                         (10, 0.3, 10, 0)])
def test_bad_inputs(curprice, vol, ndays, npaths):
    with pytest.raises(ValueError):
        sim.paths(curprice, vol, 0, ndays, npaths=npaths)


def test_chance_of_profit_matches_the_formula():
    # normal model: the chance the end price is above break-even is known exactly
    curprice, vol, drift, ndays = 11.0, 0.30, 0.04, 126
    r = sim.run(curprice, vol, drift, ndays, npaths=200000, seed=9, **pos)
    brk = calc(100, 10, 1, 5, 5, 15)['brkeven']
    t = ndays / 252
    z = (math.log(brk / curprice) - (drift - 0.5 * vol ** 2) * t) / (vol * math.sqrt(t))
    exact = 0.5 * math.erfc(z / math.sqrt(2))       # 1 - normal cdf
    assert r['pprofit'] == pytest.approx(exact, abs=0.01)
    assert r['brkeven'] == pytest.approx(brk)


def test_flat_market_gives_the_calculator_answer():
    r = sim.run(15, 0, 0, 63, npaths=100, seed=1, **pos)
    want = calc(100, 10, 15, 5, 5, 15)['netprft']
    assert r['pprofit'] == 1
    assert r['expprft'] == pytest.approx(want)
    assert r['lo'] == pytest.approx(want)
    assert r['hi'] == pytest.approx(want)
    assert r['now']['netprft'] == pytest.approx(want)


def test_flat_market_under_water_never_profits():
    r = sim.run(9, 0, 0, 63, npaths=100, seed=1, **pos)
    assert r['pprofit'] == 0
    assert r['worst'] == pytest.approx(calc(100, 10, 9, 5, 5, 15)['netprft'])


def test_numbers_are_in_order():
    r = sim.run(50, 0.4, 0.0, 63, npaths=5000, seed=3,
                allotment=10, iniprice=48, buycmm=1, sellcmm=1, cptlgain=20)
    assert r['worst'] <= r['lo'] <= r['medprft'] <= r['hi']
    assert 0 < r['pprofit'] < 1
    f = r['fan']
    assert len(f['days']) == 64
    for key in ('p5', 'p25', 'p50', 'p75', 'p95'):
        assert len(f[key]) == 64
        assert f[key][0] == 50
    for a, b in [('p5', 'p25'), ('p25', 'p50'), ('p50', 'p75'), ('p75', 'p95')]:
        assert all(x <= y for x, y in zip(f[a], f[b]))
    assert len(r['bins']['edges']) == len(r['bins']['counts']) + 1
    assert 0.97 * 5000 <= sum(r['bins']['counts']) <= 5000


def test_histogram_edges_are_round_and_include_zero():
    r = sim.run(50, 0.4, 0.0, 63, npaths=5000, seed=3,
                allotment=10, iniprice=48, buycmm=1, sellcmm=1, cptlgain=20)
    e = r['bins']['edges']
    w = e[1] - e[0]
    assert 0 in e                       # no bar mixes loss and profit
    assert all(b - a == pytest.approx(w) for a, b in zip(e, e[1:]))
    assert all(x / w == pytest.approx(round(x / w)) for x in e)     # multiples of the step
    assert 15 <= len(r['bins']['counts']) <= 42


def test_histogram_when_every_run_ends_the_same():
    r = sim.run(15, 0, 0, 63, npaths=100, seed=1, **pos)
    assert len(r['bins']['edges']) == len(r['bins']['counts']) + 1 >= 2
    assert sum(r['bins']['counts']) == 100


@pytest.mark.parametrize('x, want', [(0.7, 1), (1, 1), (1.2, 2), (2.2, 2.5), (3, 5), (7, 10),
                                     (13, 20), (0.034, 0.05), (480, 500)])
def test_nicestep(x, want):
    assert sim.nicestep(x) == pytest.approx(want)


def test_loss_is_capped_by_what_you_put_in():
    # a stock can't go below 0, so the worst you can lose is purchase price + commissions
    r = sim.run(10, 1.5, 0, 252, npaths=5000, seed=4, **pos)
    assert r['worst'] >= -(100 * 10 + 10) - 1e-6
