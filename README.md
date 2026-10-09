# Stock Calculator

A small Flask web app that works out the real profit (or loss) on a stock trade after commissions and capital gains tax.

**Author:** Abhinav Varma ([@abhinavvarmaoath](https://github.com/abhinavvarmaoath))

## What it does

Fill in the details of a trade and the app gives you a report with:

- proceeds from the sale
- total cost (purchase price + commissions + tax)
- tax on the capital gain
- net profit
- return on investment (ROI)
- the sell price you need to break even

## Inputs

- stock symbol
- number of shares
- initial (buy) share price
- final (sell) share price
- buy commission
- sell commission
- capital gains tax rate (%)

## How it's worked out

- proceeds = shares x final price
- gain = proceeds - purchase price - buy and sell commission
- tax = tax rate x gain (nothing if it's a loss, no refund is assumed)
- net profit = gain - tax
- ROI = net profit / total cost (purchase + commissions + tax)
- break-even price = initial price + total commission / shares

## Run it

```
pip install -r requirements.txt
python app.py
```

Then open http://localhost:8080 (set `FLASK_DEBUG=1` first if you want auto reload).

## Tests

```
pytest
```

## Files

- `app.py` - routes and input checks
- `calc.py` - the trade maths
- `templates/` - the pages
- `static/style.css` - styles
- `tests/` - pytest tests

## Roadmap

- predictive analysis (price forecasts, profit simulations)
- agentic AI assistant for trade analysis
