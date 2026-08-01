# C6 Instrument Report

## Evidence limitation

C1–C5 contain contemporaneous symbol and numeric sector observations, but no authoritative security master or explicit instrument-type field. Sector and ticker classifications are therefore low-confidence research heuristics; unknowns remain explicit. No current classification is projected before its observed interval.

## Taxonomy

- `ordinary_equity`: Residual ownership share that is not identified as a special instrument.
- `preference_share`: Share with documented preference terms.
- `closed_end_fund`: Exchange-listed closed-end investment fund.
- `open_end_fund`: Open-end investment fund instrument.
- `ETF`: Exchange-traded fund unit.
- `REIT`: Real-estate investment trust unit.
- `debt_security`: Corporate debt or term-finance security.
- `government_security`: Government bill or bond.
- `sukuk`: Shariah-compliant certificate identified as sukuk.
- `commercial_paper`: Short-term commercial paper.
- `right_or_entitlement`: Temporary subscription right or entitlement.
- `warrant_or_option`: Warrant, option, or similar derivative security.
- `index_or_non_security`: Index or non-security observation.
- `temporary_or_special_listing`: Temporary or otherwise special listing.
- `unknown`: Evidence is insufficient for a more specific class.

## Interval counts

```json
{
  "ETF": 11,
  "REIT": 6,
  "debt_security": 50,
  "government_security": 115,
  "ordinary_equity": 584,
  "preference_share": 11,
  "right_or_entitlement": 82
}
```
