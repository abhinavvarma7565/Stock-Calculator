import numpy as np

from calc import calc


def paths(curprice, vol, drift, ndays, hist=None, npaths=10000, seed=None):
    # random price paths, one per row. column 0 is today's price.
    # vol and drift are yearly (0.25 = 25%), 252 trading days in a year
    if curprice <= 0 or vol < 0 or ndays < 1 or npaths < 1:
        raise ValueError('need a price above 0, vol of 0 or more, and at least 1 day and 1 path')

    rng = np.random.default_rng(seed)
    dt = 1 / 252
    mu = (drift - 0.5 * vol ** 2) * dt      # daily drift of the log price

    if hist is None:
        step = vol * np.sqrt(dt) * rng.standard_normal((npaths, ndays))
    else:
        # past daily returns, same vol as above but keeps the fat tails
        h = hist - hist.mean()
        sd = h.std(ddof=1)
        h = h * (vol * np.sqrt(dt) / sd) if sd > 0 else h * 0
        step = rng.choice(h, size=(npaths, ndays))

    p = curprice * np.exp(np.cumsum(mu + step, axis=1))
    return np.hstack([np.full((npaths, 1), float(curprice)), p])


def nicestep(x):
    # 1, 2, 2.5, 5 or 10 times a power of ten: the first one that is at least x
    p = 10 ** np.floor(np.log10(x))
    for m in (1, 2, 2.5, 5, 10):
        if m * p >= x:
            return float(m * p)


def run(curprice, vol, drift, ndays, allotment, iniprice, buycmm, sellcmm, cptlgain,
        hist=None, npaths=10000, seed=None):
    p = paths(curprice, vol, drift, ndays, hist, npaths, seed)

    # sell on the last day: every path goes through the same maths as the calculator
    res = calc(allotment, iniprice, p[:, -1], buycmm, sellcmm, cptlgain)
    netprft = res['netprft']

    lo, med, hi = np.percentile(netprft, [5, 50, 95])
    k = max(1, int(npaths * 0.05))
    worst = np.sort(netprft)[:k].mean()         # average of the worst 5% of runs

    # price bands over time, for the fan chart
    pc = np.round(np.percentile(p, [5, 25, 50, 75, 95], axis=0), 2)

    # profit histogram of the middle 98% so a few huge wins don't squash it.
    # edges sit on round numbers so $0 is always an edge (no bar mixes loss and profit)
    a, b = np.percentile(netprft, [1, 99])
    w = nicestep((b - a) / 40) if b > a else 1.0
    counts, edges = np.histogram(netprft, bins=np.arange(np.floor(a / w), np.floor(b / w) + 2) * w)

    return dict(
        curprice=curprice, vol=vol, drift=drift, ndays=ndays, npaths=npaths,
        now=calc(allotment, iniprice, curprice, buycmm, sellcmm, cptlgain),
        brkeven=res['brkeven'],
        pprofit=float((netprft > 0).mean()),
        expprft=float(netprft.mean()),
        medprft=float(med), lo=float(lo), hi=float(hi), worst=float(worst),
        fan=dict(days=list(range(ndays + 1)), p5=pc[0].tolist(), p25=pc[1].tolist(),
                 p50=pc[2].tolist(), p75=pc[3].tolist(), p95=pc[4].tolist()),
        bins=dict(edges=np.round(edges, 6).tolist(), counts=counts.tolist()),
    )
