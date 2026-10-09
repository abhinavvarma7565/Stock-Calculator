import numpy as np


def calc(allotment, iniprice, fnlprice, buycmm, sellcmm, cptlgain):
    # fnlprice can be one price or a numpy array of prices (sim.py does that)
    if allotment <= 0 or iniprice <= 0:
        raise ValueError('shares and initial price must be more than 0')

    proceeds = allotment * fnlprice
    ttlshareprice = allotment * iniprice
    cmm = buycmm + sellcmm

    gain = proceeds - ttlshareprice - cmm

    # tax is only on a gain, no refund on a loss
    tocg = np.maximum(gain, 0) * cptlgain / 100
    cost = ttlshareprice + cmm + tocg

    netprft = proceeds - cost
    roi = netprft * 100 / cost

    # sell price that gets back the buy price and both commissions
    brkeven = iniprice + cmm / allotment

    res = dict(proceeds=proceeds, ttlshareprice=ttlshareprice, buycmm=buycmm,
               sellcmm=sellcmm, cmm=cmm, gain=gain, tocg=tocg, cost=cost,
               netprft=netprft, roi=roi, brkeven=brkeven)

    # one price in, plain floats out
    if np.ndim(fnlprice) == 0:
        res = {k: float(v) for k, v in res.items()}
    return res
