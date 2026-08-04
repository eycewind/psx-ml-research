# C10 CP4B — KMI All Share Reconciliation Audit

This audit applies official incoming/outgoing tables to the accepted 2022 baseline. It intentionally does not write final membership history.

| Effective | Source | Start | Incoming | Outgoing | Computed | Official | Gap | Missing outgoing | Already-present incoming |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022-01-03 | baseline | None | 0 | 0 | 250 | 250 | 0 | 0 | 0 |
| 2022-07-15 | review_2021_h2 | 250 | 30 | 25 | 255 | 252 | 3 | 0 | 0 |
| 2023-01-12 | review_2022_h1 | 255 | 30 | 21 | 264 | 261 | 3 | 0 | 0 |
| 2023-07-10 | review_2022_h2 | 264 | 26 | 33 | 258 | 251 | 7 | 1 | 0 |
| 2023-12-26 | review_2023_h1 | 258 | 32 | 24 | 267 | 258 | 9 | 1 | 0 |
| 2024-06-25 | review_2023_h2 | 267 | 28 | 29 | 266 | 255 | 11 | 0 | 0 |
| 2025-01-03 | review_2024_h1 | 266 | 26 | 13 | 279 | 264 | 15 | 0 | 0 |
| 2025-06-10 | review_2024_h2 | 279 | 15 | 22 | 274 | 257 | 17 | 2 | 0 |
| 2025-12-02 | review_2025_h1 | 274 | 35 | 12 | 297 | 281 | 16 | 0 | 0 |

## Exceptions requiring source reconciliation

- 2022-07-15 (review_2021_h2): count gap +3
- 2023-01-12 (review_2022_h1): count gap +3
- 2023-07-10 (review_2022_h2): count gap +7; missing outgoing: CNERGY
- 2023-12-26 (review_2023_h1): count gap +9; missing outgoing: CLVL
- 2024-06-25 (review_2023_h2): count gap +11
- 2025-01-03 (review_2024_h1): count gap +15
- 2025-06-10 (review_2024_h2): count gap +17; missing outgoing: WAVESAPP, ZAL
- 2025-12-02 (review_2025_h1): count gap +16

## Stop condition

Do not create final membership intervals while any official-count gap or impossible outgoing symbol remains unresolved.
