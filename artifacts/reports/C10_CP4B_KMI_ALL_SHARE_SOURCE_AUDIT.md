# C10 CP4B — KMI All Share Source Audit

This report audits the downloaded official PSX notices before any historical membership table is built.

| Source | Effective from | Notice count | Parsed compliant | Screening table |
|---|---:|---:|---:|---|
| review_2021_h1 | 2022-01-03 | 250 | 257 | True |
| review_2021_h2 | 2022-07-15 | 252 | 0 | False |
| review_2022_h1 | 2023-01-12 | 261 | 257 | True |
| review_2022_h2 | 2023-07-10 | 251 | 0 | False |
| review_2023_h1 | 2023-12-26 | 258 | 265 | True |
| review_2023_h2 | 2024-06-25 | 255 | 270 | True |
| review_2024_h1 | 2025-01-03 | 264 | 285 | True |
| review_2024_h2 | 2025-06-02 | None | 284 | True |
| review_2025_h1 | 2025-12-02 | None | 309 | True |

## Interpretation

- A parsed screening-table count is diagnostic only.
- It must not automatically become an index-membership count.
- Some PDFs contain incoming/outgoing changes only.
- Some screening tables cover the full listed universe and include non-index or special-status rows.
- Membership will be reconstructed from a reviewed baseline and official effective-date changes.

## Required stop condition

Do not generate the final membership CSV until every notice's incoming/outgoing list has been extracted and the reconstructed counts reconcile with the notice.
