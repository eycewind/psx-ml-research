# C6 Instrument Report

## Primary evidence

Classification now uses the dated PSX security-master snapshot `2026-08-01` before sector or ticker fallbacks. The snapshot combines Listing Status, Eligible Scrips, and Fixed Income Securities Detail. Ticker regexes run only for historical symbols absent from that master.

The snapshot is current-state evidence. Applying its family to earlier observations is explicitly a backcast, not contemporaneous point-in-time proof; this limitation is recorded in the manifest. Historical symbols absent from the master retain low-confidence fallback provenance, and unknowns remain explicit.

## Actual precedence

1. manual mapping; 2. dated PSX security master; 3. exact observed-sector mapping; 4. ticker fallback only when absent from the master; 5. preference suffix; 6. generic `08` prefix; 7. unknown.

Configured exact mappings: `36 → debt_security`, `3610 → government_security`, `0836 → REIT`, `0837 → ETF`.

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
  "debt_security": 123,
  "government_security": 28,
  "ordinary_equity": 602,
  "preference_share": 1,
  "right_or_entitlement": 77,
  "sukuk": 11
}
```

## Rule and source counts

```json
{
  "rules": {
    "psx_master:2026-08-01:ETF": 11,
    "psx_master:2026-08-01:REIT": 6,
    "psx_master:2026-08-01:debt_security": 78,
    "psx_master:2026-08-01:ordinary_equity": 515,
    "psx_master:2026-08-01:right_or_entitlement": 2,
    "psx_master:2026-08-01:sukuk": 11,
    "sector_exact:36": 45,
    "sector_exact:3610": 27,
    "sector_prefix:08": 87,
    "sector_prefix:08+preference_suffix": 1,
    "ticker_regex:government_security": 1,
    "ticker_regex:right_or_entitlement": 75
  },
  "sources": {
    "observed_sector_rule": 72,
    "psx_security_master_snapshot": 623,
    "sector_prefix_inference": 87,
    "ticker_heuristic": 1,
    "ticker_heuristic_historical_fallback": 76
  }
}
```

Generic `sector_prefix:08` inference now accounts for **87** intervals and is used only after stronger master/sector/ticker evidence. These remain low-confidence inferred classifications.

The deterministic sector audit contains 98 rows. The hierarchy audit found 769 competing-rule intervals; 785 symbols are in the targeted manual-review queue.

## Sector audit

| Sector | Assigned type | Source | Rule | Intervals | Symbols | Examples |
|---|---|---|---|---:|---:|---|
| `<blank>` | `ETF` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ETF` | 1 | 1 | MZNPETF |
| `<blank>` | `government_security` | `ticker_heuristic_historical_fallback` | `ticker_regex:government_security` | 1 | 1 | P05PIB151025 |
| `0801` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 10 | 10 | AGTL|ATLH|DFML|GAL|GHNI|HCAR|HINO|INDU|MTL|SAZEW |
| `0801` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | GAIL|GHNL|PSMC |
| `0801` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 2 | 2 | HINOR|SAZEWR |
| `0802` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 12 | 12 | AGIL|ATBA|BELA|BWHL|DWAE|EXIDE|GTYR|LOADS|PTL|SLM |
| `0802` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 2 | 2 | LOADSR|LOADSR1 |
| `0803` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 7 | 7 | EMCO|FCL|PAEL|PCAL|SIEM|WAVES|WAVESAPP |
| `0803` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | JOPP|WHALE |
| `0803` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 2 | 2 | PAELR3|WAVESR1 |
| `0804` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 21 | 21 | ACPL|BWCL|CHCC|DBCI|DCL|DGKC|DNCC|FCCL|FECTC|FLYNG |
| `0804` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 4 | 4 | DNCCR|FLYNGR|FLYNGR1|POWERR1 |
| `0805` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 28 | 28 | AGL|AGLNCPS|ARPL|BAPL|BERG|BIFO|BUXL|COLG|DAAG|DOL |
| `0805` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 5 | 5 | AKZO|GCILB|GTECH|ICI|PGCL |
| `0805` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 4 | 4 | GCWLR|GGLR1|GTECHBR|PAKOXYR |
| `0806` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 3 | 3 | HGFA|HIFA|TSMF |
| `0807` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 19 | 19 | ABL|AKBL|BAFL|BAHL|BIPL|BML|BOK|BOP|FABL|HBL |
| `0807` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | SILK|SMBL |
| `0807` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | JSBLR1 |
| `0808` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 20 | 20 | AGHA|ASL|ASLCPS|ASLPS|ASTL|BCL|BECO|CSAP|DADX|DSL |
| `0808` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | ADOS|DKL |
| `0808` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 3 | 3 | KSBPR|MUGHALR1|MUGHALR2 |
| `0809` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | AGL|AGLNCPS|AHCL|EFERT|FATIMA|FFC |
| `0809` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | ENGRO|FFBL |
| `0809` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | FFBLR |
| `0810` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 25 | 25 | ASC|BBFL|BFAGRO|BNL|CLOV|COLG|FCEPL|FFL|GDL|ISIL |
| `0810` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | GLPL|SCL |
| `0810` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 10 | 10 | ASCR|ASCR1|ASCR2|FFLR1|GLPLR|MFFLR|MFFLR1|TOMCLR|TREETR2|UNITYR3 |
| `0811` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 8 | 8 | BGL|FRCL|GGGL|GHGL|GVGL|KCL|STCL|TGL |
| `0811` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 3 | 3 | GGGLR1|GHGLR3|GVGLR3 |
| `0812` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 28 | 28 | AGIC|AICL|ALAC|ALIFE|ASIC|ATIL|CENI|CSIL|EFUG|EFUL |
| `0812` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 1 | CYAN |
| `0812` | `right_or_entitlement` | `psx_security_master_snapshot` | `psx_master:2026-08-01:right_or_entitlement` | 1 | 1 | AGICR2 |
| `0812` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 4 | 4 | ALACR4|CSILR3|EWICR3|PKGIR |
| `0813` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 33 | 33 | 786|AHL|AKDSL|AMBL|ARMG|DEL|DLL|ENGROH|ESBL|FCEL |
| `0813` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 11 | 9 | BIPLS|CASH|CYAN|DAWH|DHPL|EFGH|FDIBL|JSCLPSA|MCBAH |
| `0813` | `right_or_entitlement` | `psx_security_master_snapshot` | `psx_master:2026-08-01:right_or_entitlement` | 1 | 1 | 786R |
| `0813` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 5 | 5 | AMBLR4|JSCLR1|LSECLR|LSEVLR|TSBLR1 |
| `0814` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 1 | 1 | SUHJ |
| `0815` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 4 | 4 | GRYL|OLPL|PGLC|SLL |
| `0815` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | CASH|CPAL|SPLC |
| `0816` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | BATA|FIL|LEUL|PAKL|SGF|SRVI |
| `0818` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 23 | 23 | AKDHL|AKGL|ARPAK|DIIL|ECOP|GAMON|GEMPACRA|GOC|MACFL|MWMP |
| `0818` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | AKDCL|META |
| `0818` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | SPELR |
| `0819` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 21 | 21 | BFMOD|FANM|FECM|FEM|FFLM|FHAM|FIBLM|FIMM|FNBM|FPJM |
| `0819` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 9 | 9 | ARM|AWWAL|FUDLM|HMM|KASBM|MODAM|ORIXM|PAKMI|PMI |
| `0819` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 5 | 5 | BRR|BRRR|MODAMR|MODAMR1|WASLR |
| `0820` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 4 | 4 | MARI|OGDC|POL|PPL |
| `0821` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 10 | 10 | APL|BPL|HASCOL|HTL|OBOY|PSO|SNGP|SPSL|SSGC|WAFI |
| `0821` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | SHEL |
| `0821` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 3 | 3 | OBOYR1|OBOYR2|SHELR |
| `0822` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 11 | 11 | CEPB|CPPL|GEMPAPL|IPAK|MACFL|MERIT|PKGS|PPP|RPL|SEPL |
| `0822` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | BPBL |
| `0822` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | MERITR2 |
| `0823` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 14 | 14 | ABOT|AGP|BFBIO|CPHL|FEROZ|GLAXO|HALEON|HINOON|HPL|IBLHL |
| `0823` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | GSKCH|SAPL|WYETH |
| `0823` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 4 | 4 | LIVENR|MACTERR|SEARLR1|SEARLR2 |
| `0824` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 16 | 16 | ALTN|EPQL|GEMMEL|HUBC|KAPCO|KEL|KOHE|KOHP|LPL|NCPL |
| `0824` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | AEL |
| `0825` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 4 | 4 | ATRL|CNERGY|NRL|PRL |
| `0825` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | BYCO |
| `0825` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | PRLR1 |
| `0826` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 30 | 30 | AABS|ADAMS|AGSML|ALNRS|ANSM|BAFS|CHAS|DWSM|FRSM|HABSM |
| `0826` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | HAL|HSM|IMSL |
| `0826` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 1 | 1 | HSMCPS |
| `0826` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 6 | 6 | FRSMR|HSMPSR|HSMR3|MIRKSR|TCORPR1|TCORPR2 |
| `0827` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | GATI|IBFL|IMAGE|NSRM|PSYL|RUPL |
| `0827` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | TRPOL |
| `0827` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 3 | 3 | GATIR|IMAGER1|IMAGER2 |
| `0828` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 21 | 21 | AIRLINK|AVN|GEMNETS|HUMNL|ITANZ|MDTL|NETSOL|OCTOPUS|PAKD|PTC |
| `0828` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | GEMSPNL|HCL|LSEPL |
| `0829` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 44 | 44 | ADMM|AHTM|ANL|ANLNV|ANTM|ARUJ|BHAT|BTL|CHBL|CLCPS |
| `0829` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | AEL|MTIL |
| `0829` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 4 | 4 | ANLR|CRTMR2|FMLR|STYLERSR |
| `0830` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 51 | 51 | AATM|AMTEX|ARCTM|ASTM|AWTX|BECO|CCM|CFL|CTM|DFSM |
| `0830` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 16 | 16 | BCML|BILF|CLOUD|CWSM|DATM|DMIL|DMTX|DSML|IDSM|ILTM |
| `0830` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 3 | 3 | DINTR|SHDTR1|SNAIR |
| `0831` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | ASHT|ICCI|PRWM|STJT|YOUW|ZTL |
| `0831` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 4 | 4 | GTECH|SERF|SMTM|WHALE |
| `0831` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | SERFR |
| `0832` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 2 | 2 | KHTC|PAKT |
| `0832` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | PMPK |
| `0833` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | BLUEX|CLVL|PIBTL|PICT|PNSC|SLGL |
| `0833` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 4 | 4 | GEMBLUEX|GEMUNSL|PIAA|PIAB |
| `0833` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | CLVLR |
| `0834` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 3 | 3 | POML|SSOM|UNITY |
| `0834` | `right_or_entitlement` | `ticker_heuristic_historical_fallback` | `ticker_regex:right_or_entitlement` | 1 | 1 | UNITYR2 |
| `0835` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 2 | 2 | BNL|BNWM |
| `0836` | `REIT` | `psx_security_master_snapshot` | `psx_master:2026-08-01:REIT` | 6 | 6 | DCR|GRR|IREIT|JSRR|SRR|TPLRF1 |
| `0837` | `ETF` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ETF` | 10 | 9 | ACIETF|HBLTETF|JSGBETF|JSMFETF|MIIETF|MZNPETF|NBPGETF|NITGETF|UBLPETF |
| `0838` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 6 | 6 | BRRG|HUSI|JVDC|JVDCPS|PACE|TPLP |
| `0839` | `ordinary_equity` | `psx_security_master_snapshot` | `psx_master:2026-08-01:ordinary_equity` | 4 | 4 | IMAGE|INKL|MSOT|STYLERS |
| `36` | `debt_security` | `observed_sector_rule` | `sector_exact:36` | 45 | 45 | AGSILSC|AKBLTFC7|BAFLTFC5|BAFLTFC7|BCEMSTSC|BYCOSC|CNERGYSC|DAWHSC1|DAWHSC2|EPCLSC |
| `36` | `debt_security` | `psx_security_master_snapshot` | `psx_master:2026-08-01:debt_security` | 75 | 75 | AKBLTFC6|BAFLTFC6|BAFLTFC8|BAHLTFC10|BAHLTFC9|BIPLSC|BIPLSC2|BOPTFC2|HBLTFC2|HUBPHLSC |
| `36` | `sukuk` | `psx_security_master_snapshot` | `psx_master:2026-08-01:sukuk` | 11 | 11 | KELSC5|MUGHALSC|P01GHS100627|P01GHS130527|P01GHS150427|P01GHS200527|P01GHS230627|P01GHS290427|P03FRR180629|P05FRR180631 |
| `3610` | `debt_security` | `psx_security_master_snapshot` | `psx_master:2026-08-01:debt_security` | 3 | 3 | P05PIB131027|P05PIB290427|P10PIB101230 |
| `3610` | `government_security` | `observed_sector_rule` | `sector_exact:3610` | 27 | 27 | P03PIB040825|P03PIB050824|P03PIB200823|PK03TB010623|PK03TB021221|PK03TB040523|PK03TB060423|PK03TB150623|PK03TB150721|PK03TB171122 |