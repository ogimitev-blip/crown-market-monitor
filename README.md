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
