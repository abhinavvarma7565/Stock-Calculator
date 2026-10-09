import numpy as np
import pytest

from calc import calc


def test_gain():
    # 100 shares, bought at 10, sold at 15, 5 + 5 commission, 15% tax
    r = calc(100, 10, 15, 5, 5, 15)
    assert r['proceeds'] == 1500
    assert r['ttlshareprice'] == 1000
    assert r['gain'] == 490
    assert r['tocg'] == pytest.approx(73.5)
    assert r['cost'] == pytest.approx(1083.5)
    assert r['netprft'] == pytest.approx(416.5)
    assert r['roi'] == pytest.approx(38.4402, abs=1e-4)
    assert r['brkeven'] == pytest.approx(10.10)


def test_loss_has_no_tax():
    r = calc(100, 15, 10, 5, 5, 15)
    assert r['tocg'] == 0
    assert r['netprft'] == pytest.approx(-510)
    assert r['roi'] == pytest.approx(-510 * 100 / 1510)
    assert r['brkeven'] == pytest.approx(15.10)


def test_zero_tax_rate():
    r = calc(100, 10, 15, 5, 5, 0)
    assert r['tocg'] == 0
    assert r['netprft'] == pytest.approx(490)


def test_decimals():
    # 144.375 in, 128.625 out, 9.90 commission -> gain 5.85, tax 1.17
    r = calc(10.5, 12.25, 13.75, 4.95, 4.95, 20)
    assert r['gain'] == pytest.approx(5.85)
    assert r['tocg'] == pytest.approx(1.17)
    assert r['netprft'] == pytest.approx(4.68)


@pytest.mark.parametrize('allotment, iniprice, buycmm, sellcmm, cptlgain', [
    (100, 10, 5, 5, 15),
    (3.5, 250.25, 4.95, 9.9, 24),
    (1000, 0.5, 0, 12, 35),
])
def test_break_even_is_zero_profit(allotment, iniprice, buycmm, sellcmm, cptlgain):
    brk = calc(allotment, iniprice, iniprice, buycmm, sellcmm, cptlgain)['brkeven']
    r = calc(allotment, iniprice, brk, buycmm, sellcmm, cptlgain)
    assert r['netprft'] == pytest.approx(0, abs=1e-9)
    assert r['tocg'] == pytest.approx(0, abs=1e-9)


def test_break_even_is_above_buy_price_when_there_are_commissions():
    assert calc(100, 10, 15, 5, 5, 15)['brkeven'] > 10
    assert calc(100, 10, 15, 0, 0, 15)['brkeven'] == pytest.approx(10)


def test_array_of_prices():
    prices = np.array([5.0, 10.0, 15.0])
    r = calc(100, 10, prices, 5, 5, 15)
    assert r['netprft'] == pytest.approx([-510, -10, 416.5])
    # same as doing them one by one
    for i, p in enumerate(prices):
        assert r['roi'][i] == pytest.approx(calc(100, 10, p, 5, 5, 15)['roi'])


def test_one_price_gives_plain_floats():
    r = calc(100, 10, 15, 5, 5, 15)
    assert all(type(v) is float for v in r.values())


@pytest.mark.parametrize('allotment, iniprice', [(0, 10), (-5, 10), (100, 0), (100, -1)])
def test_bad_shares_or_price(allotment, iniprice):
    with pytest.raises(ValueError):
        calc(allotment, iniprice, 15, 5, 5, 15)
