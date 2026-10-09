# Stock Calculator

A small Flask web app for stock trades. The calculator works out the real profit (or loss) on a trade after commissions and capital gains tax. The simulator runs thousands of random price paths to show the range of things that could happen if you hold a position for a while.

**Author:** Abhinav Varma ([@abhinavvarmaoath](https://github.com/abhinavvarmaoath))

## Calculator

Fill in the details of a trade and the app gives you a report with:

- proceeds from the sale
- total cost (purchase price + commissions + tax)
- tax on the capital gain
- net profit
- return on investment (ROI)
- the sell price you need to break even

Inputs: stock symbol, number of shares, initial (buy) price, final (sell) price, buy commission, sell commission and the capital gains tax rate (%).

How it's worked out:

- proceeds = shares x final price
- gain = proceeds - purchase price - buy and sell commission
- tax = tax rate x gain (nothing if it's a loss, no refund is assumed)
- net profit = gain - tax
- ROI = net profit / total cost (purchase + commissions + tax)
- break-even price = initial price + total commission / shares

## Simulator

Enter a position and how long you'd hold it (1 month to 1 year). The simulator runs 10,000 random price paths and puts every one of them through the same maths as the calculator, so you get:

- the chance of making a profit after commissions and tax
- the expected and median net profit, the likely range (5th to 95th percentile) and the bad case (average of the worst 5% of runs)
- a chart of where the price could go: median, middle 50% and middle 90% of runs, and the break-even price
- a histogram of net profit, with losses in red and profits in blue
- a table view of both charts, and arrow key support on them

The price today and the volatility are worked out from the last 2 years of daily closes (yfinance, so it needs internet). If the lookup fails you can type them in under Advanced.

What it assumes:

- 252 trading days in a year
- expected yearly return is 0% unless you set it, so no view on which way the price goes
- normal random daily moves (geometric Brownian motion), or resampled past daily moves which keeps the big days a real stock has. Both are scaled to the same volatility
- commissions as entered, tax only on a gain
- it shows what could happen if prices behave like the model. It is not a prediction and not financial advice, and the numbers move a little each run because the runs are random

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
- `sim.py` - the Monte Carlo simulation
- `prices.py` - price history lookup
- `templates/` - the pages
- `static/` - styles and the chart code (plain svg)
- `tests/` - pytest tests

## Roadmap

- price forecasts with a backtest scoreboard
- agentic AI assistant for trade analysis
