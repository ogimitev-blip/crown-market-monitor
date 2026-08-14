# Crown Market Monitor v2.0 — Trading Desk

Cloud-only Streamlit trading cockpit.

## New
- Trading Desk with IS0E focus card and portfolio action table
- Instrument Workbench with interactive candlesticks
- 15m / 1h / 1D selectable timeframes
- SMA 20/50/100/200, rolling VWAP, RSI, SuperTrend, Ichimoku
- Crown support/resistance and average cost drawn on chart when available
- Cross-Asset Lab with normalized performance and rolling correlations
- Portfolio page combining uploaded Crown results with live technical context
- IS0E is the prototype Gold/Miners transmission profile

## Crown integration
Upload the latest Crown Framework Results ZIP in the app sidebar.
The monitor reads:
- current portfolio snapshot
- portfolio review
- watchlist assessment / technical outputs
- canonical execution governance
- Event-Aware / research states

## Deploy
Replace the existing GitHub repository contents with this folder.
Keep the existing Streamlit FRED_API_KEY secret.
Streamlit Cloud should rebuild automatically.

## Important
This is a read-only decision/monitoring cockpit. It does not place broker orders.
Yahoo/yfinance market data can be delayed or unavailable and is treated as a monitoring feed, not execution-grade market data.


## v2.1 Ratio Lab
- Two independent asset dropdowns: numerator and denominator
- Presets for RSP/SPY, GLD/SPY, GDX/GLD, IS0E/GLD, SOXX/SPY, QQQ/RSP,
  XLF/ITB, XLY/XLP, HYG/LQD and other Crown relationships
- 3M / 6M / 1Y / 2Y / 5Y horizons
- Ratio chart with SMA 20/50/200
- 60-day ratio z-score
- 5D and 20D relative-strength change
- Normalized underlying-price comparison
- 20-session return correlation


## v2.2 Universal Macro & Cross-Asset Lab

New **Universal Macro Lab** includes:

- Market / ETF / Crown UCITS inputs
- Full Treasury curve: 1M, 3M, 6M, 1Y, 2Y, 5Y, 7Y, 10Y, 20Y, 30Y
- 10Y-2Y and 10Y-3M curve spreads
- 5Y/7Y/10Y/20Y/30Y real yields
- 5Y/10Y breakevens and 5Y5Y forward inflation
- Fed Funds, SOFR and IORB
- Fed balance sheet, reserve balances, ON RRP, TGA and M2
- High-yield OAS, corporate OAS, NFCI and ANFCI
- Growth, consumption and housing series
- Direct BLS CPI, Core CPI, unemployment, participation, payrolls, AHE, JOLTS and PPI
- Direct EIA WTI/Brent spot and petroleum inventories
- Direct BEA NIPA explorer driven by BEA metadata
- Any BLS series ID and any legacy EIA Series ID can be entered manually

Transformations:
- Ratio A/B
- Spread A-B
- Spread in basis points
- Indexed comparison
- Indexed relative strength
- Z-score divergence
- YoY change spread
- Rolling correlation

Add these Streamlit Secrets:

```toml
FRED_API_KEY = "..."
BLS_API_KEY = "..."
BEA_API_KEY = "..."
EIA_API_KEY = "..."
```

Missing optional keys are shown explicitly and do not break the rest of the app.
