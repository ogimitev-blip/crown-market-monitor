# Crown Market Monitor v1.3 — Freshness & State Semantics

Changes:
- Crown run age is calculated from the framework `as_of` timestamp.
- Fresh/aging/stale Crown-run banner.
- Crown `live_input_refresh.stale_inputs` and `unverified_or_unavailable_inputs` are surfaced.
- FRED rates show explicit source freshness and stale warnings.
- Condition-state status preserves uncertainty/confirmation semantics:
  UNCONFIRMED, DATA_INSUFFICIENT, UNAVAILABLE, UNKNOWN, MIXED/TRANSITION,
  WAIT/CONFIRM, NO TRIGGER, or ACTIVE STATE.
- Live prices continue to refresh independently of the uploaded Crown ZIP.

Deploy by replacing the existing GitHub repository files with the contents of this folder.
Your existing FRED_API_KEY Streamlit secret remains unchanged.
