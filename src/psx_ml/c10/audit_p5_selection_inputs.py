from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

REPORT = Path('artifacts/reports/C10_CP4B_P5_INPUT_AUDIT.md')
MANIFEST = Path('artifacts/reports/C10_CP4B_P5_INPUT_AUDIT.json')
ROOTS = [
    Path('artifacts/c8'), Path('data/processed/c8'),
    Path('artifacts/c9'), Path('data/processed/c9'),
    Path('data/processed/features'), Path('data/processed'),
    Path('data/reference'),
]
TOKENS = {
    'prediction','trade_date','symbol','model_name','feature_variant',
    'target_family','horizon','sector','turnover_median_20obs_adj'
}

def read_table(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path) if path.suffix == '.parquet' else pd.read_csv(path)

def inspect(path: Path) -> dict[str, object] | None:
    try:
        frame = read_table(path)
    except Exception:
        return None
    columns = [str(c) for c in frame.columns]
    relevant = [c for c in columns if c in TOKENS]
    if not relevant:
        return None
    out: dict[str, object] = {'path': str(path), 'rows': int(len(frame)), 'columns': columns, 'relevant_columns': relevant}
    for column in ('policy_id','model_name','feature_variant','target_family','horizon'):
        if column in frame.columns:
            out[f'{column}_values'] = sorted(frame[column].dropna().astype(str).unique().tolist())[:50]
    if 'trade_date' in frame.columns and not frame.empty:
        dates = pd.to_datetime(frame['trade_date'], errors='coerce')
        out['trade_date_min'] = None if dates.isna().all() else dates.min().date().isoformat()
        out['trade_date_max'] = None if dates.isna().all() else dates.max().date().isoformat()
        out['trade_date_nunique'] = int(dates.nunique())
    return out

def main() -> None:
    tables = []
    seen: set[Path] = set()
    for root in ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path in seen or path.suffix.lower() not in {'.parquet','.csv'}:
                continue
            seen.add(path)
            record = inspect(path)
            if record:
                tables.append(record)

    p1_summary = None
    p1_path = Path('data/processed/c9/candidate_selections.parquet')
    if p1_path.exists():
        frame = pd.read_parquet(p1_path)
        p1 = frame.loc[frame['policy_id'] == 'P1_broad_canonical'].copy()
        dates = pd.to_datetime(p1['trade_date'])
        p1_summary = {
            'rows': int(len(p1)), 'signal_dates': int(dates.nunique()),
            'date_min': dates.min().date().isoformat(), 'date_max': dates.max().date().isoformat(),
            'dates': sorted(dates.dt.date.astype(str).unique().tolist()),
        }

    screened_summary = None
    screened_path = Path('data/reference/kmi_all_share_screened_universe_history.parquet')
    if screened_path.exists():
        frame = pd.read_parquet(screened_path)
        screened_summary = {
            'rows': int(len(frame)), 'intervals': int(frame['effective_from'].nunique()),
            'columns': [str(c) for c in frame.columns],
            'confidence_values': sorted(frame['membership_confidence'].dropna().astype(str).unique().tolist()),
        }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        '# C10 CP4B — P5 Input Audit','',
        'This audit identifies the exact accepted prediction, feature/liquidity, sector, and date sources required before generating P5 selections.','',
        '## P1 weekly date source','',
    ]
    if p1_summary:
        lines += [f"- Rows: {p1_summary['rows']}", f"- Signal dates: {p1_summary['signal_dates']}", f"- Range: {p1_summary['date_min']} to {p1_summary['date_max']}"]
    else:
        lines += ['- Missing `data/processed/c9/candidate_selections.parquet`.']
    lines += ['', '## Screened-universe artifact', '']
    if screened_summary:
        lines += [f"- Rows: {screened_summary['rows']}", f"- Intervals: {screened_summary['intervals']}", '- Confidence values: ' + ', '.join(screened_summary['confidence_values'])]
    else:
        lines += ['- Missing screened-universe Parquet.']
    lines += ['', '## Candidate data tables', '', '| Path | Rows | Relevant columns |', '|---|---:|---|']
    for record in tables:
        lines.append(f"| `{record['path']}` | {record['rows']} | {', '.join(record['relevant_columns'])} |")
    lines += ['', '## Stop condition', '', 'Do not implement the P5 generator until the exact accepted C8 OOF prediction table, PIT liquidity table, sector source, and P1 weekly dates have been identified.', '']
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    MANIFEST.write_text(json.dumps({'checkpoint':'C10-CP4B-3-p5-input-audit','holdout_accessed':False,'p1_summary':p1_summary,'screened_summary':screened_summary,'candidate_tables':tables}, indent=2, sort_keys=True), encoding='utf-8')
    print('\n'.join(lines))
    print(f'Manifest: {MANIFEST}')

if __name__ == '__main__':
    main()
