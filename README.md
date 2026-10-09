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

## Run it

```
pip install flask
python app.py
```

Then open http://localhost:8080

## Files

- `app.py` - routes and the calculations
- `templates/index.html` - input form
- `templates/index2.html` - report page

## Roadmap

- predictive analysis (price forecasts, profit simulations)
- agentic AI assistant for trade analysis
