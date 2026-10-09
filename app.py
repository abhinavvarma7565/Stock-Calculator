import math
import re

from flask import Flask, render_template, request, redirect, url_for

from calc import calc

app = Flask(__name__)

# key, label, lowest, can it be the lowest, highest, required
calcfields = [
    ('allotment', 'Number of shares', 0, False, 1e9, True),
    ('iniprice', 'Initial share price', 0, False, 1e7, True),
    ('fnlprice', 'Final share price', 0, True, 1e7, True),
    ('buycmm', 'Buy commission', 0, True, 1e7, True),
    ('sellcmm', 'Sell commission', 0, True, 1e7, True),
    ('cptlgain', 'Capital gain tax rate', 0, True, 100, True),
]


@app.template_filter()
def money(x):
    x = round(float(x), 2)
    return ('-' if x < 0 else '') + '${:,.2f}'.format(abs(x))


@app.template_filter()
def pct(x):
    return '{:.2f}%'.format(float(x))


def getnum(form, key, label, low, lowok, high, need, errs):
    raw = form.get(key, '').strip().replace(',', '')
    if raw == '':
        if need:
            errs.append(label + ' is required')
        return None
    try:
        val = float(raw)
    except ValueError:
        val = math.nan
    if not math.isfinite(val):
        errs.append(label + ' must be a number')
        return None
    if val < low or (val == low and not lowok):
        errs.append('{} must be {} {:g}'.format(label, 'at least' if lowok else 'more than', low))
        return None
    if val > high:
        errs.append('{} must be {:,.10g} or less'.format(label, high))
        return None
    return val


def getfields(form, fields, errs):
    vals = {}
    for key, label, low, lowok, high, need in fields:
        vals[key] = getnum(form, key, label, low, lowok, high, need, errs)
    return vals


def getsym(form, errs):
    sym = form.get('stksymbol', '').strip().upper()
    if not re.fullmatch(r'[A-Z0-9.\-]{1,10}', sym):
        errs.append('Stock symbol must be 1 to 10 letters or numbers, like AAPL or BRK-B')
        return None
    return sym


@app.route('/')
def index():
    return render_template('index.html', form={}, errs=[])


@app.route('/post', methods=['GET', 'POST'])
def report():
    if request.method == 'GET':
        return redirect(url_for('index'))

    errs = []
    stksymbol = getsym(request.form, errs)
    vals = getfields(request.form, calcfields, errs)
    if errs:
        return render_template('index.html', form=request.form, errs=errs), 400

    res = calc(**vals)
    return render_template('index2.html', stksymbol=stksymbol, **res)


if __name__ == '__main__':
    app.run(port=8080)
