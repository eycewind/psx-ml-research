# C6 Instrument Report

## Evidence limitation

C1–C5 contain contemporaneous symbol and numeric sector observations, but no authoritative security master or explicit instrument-type field. Sector and ticker classifications are therefore low-confidence research heuristics; unknowns remain explicit. No current classification is projected before its observed interval.

Zero unknown intervals occur because every unmatched interval in this snapshot has an observed sector beginning with `08`; this does not make those classifications authoritative.

## Actual precedence

1. manual mapping; 2. government ticker regex; 3. exact sector mapping; 4. ETF suffix; 5. debt ticker regex; 6. right ticker regex; 7. preference suffix with `08`; 8. generic `08` prefix; 9. unknown.

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
  "debt_security": 50,
  "government_security": 115,
  "ordinary_equity": 584,
  "preference_share": 11,
  "right_or_entitlement": 82
}
```

## Rule and source counts

```json
{
  "rules": {
    "sector_exact:0836": 6,
    "sector_exact:0837": 10,
    "sector_exact:36": 47,
    "sector_prefix:08": 584,
    "sector_prefix:08+preference_suffix": 11,
    "ticker_regex:debt_security": 3,
    "ticker_regex:government_security": 115,
    "ticker_regex:right_or_entitlement": 82,
    "ticker_suffix:ETF": 1
  },
  "sources": {
    "observed_sector_rule": 63,
    "sector_prefix_inference": 584,
    "ticker_heuristic": 212
  }
}
```

Generic `sector_prefix:08` inference accounts for **584** ordinary-equity intervals. These are low-confidence inferred classifications, not manual or authoritative classifications.

The deterministic sector audit contains 78 rows. The hierarchy audit found 271 competing-rule intervals; 591 symbols are in the targeted manual-review queue.

## Sector audit

| Sector | Assigned type | Source | Rule | Intervals | Symbols | Examples |
|---|---|---|---|---:|---:|---|
| `<blank>` | `ETF` | `ticker_heuristic` | `ticker_suffix:ETF` | 1 | 1 | MZNPETF |
| `<blank>` | `government_security` | `ticker_heuristic` | `ticker_regex:government_security` | 1 | 1 | P05PIB151025 |
| `0801` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 12 | 12 | AGTL|ATLH|DFML|GAIL|GAL|GHNI|GHNL|HINO|INDU|MTL |
| `0801` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | HCAR|HINOR|SAZEWR |
| `0802` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 11 | 11 | AGIL|ATBA|BELA|BWHL|DWAE|EXIDE|LOADS|PTL|SLM|TBL |
| `0802` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | GTYR|LOADSR|LOADSR1 |
| `0803` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 9 | 9 | EMCO|FCL|JOPP|PAEL|PCAL|SIEM|WAVES|WAVESAPP|WHALE |
| `0803` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 2 | 2 | PAELR3|WAVESR1 |
| `0804` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 18 | 18 | ACPL|BWCL|CHCC|DBCI|DCL|DGKC|DNCC|FCCL|FECTC|FLYNG |
| `0804` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 2 | 2 | JVDCPS|POWERPS |
| `0804` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 5 | 5 | DNCCR|FLYNGR|FLYNGR1|POWER|POWERR1 |
| `0805` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 31 | 31 | AGL|AKZO|ARPL|BAPL|BERG|BIFO|BUXL|COLG|DAAG|DOL |
| `0805` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 2 | 2 | AGLNCPS|EPCLPS |
| `0805` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 4 | 4 | GCWLR|GGLR1|GTECHBR|PAKOXYR |
| `0806` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | HGFA|HIFA|TSMF |
| `0807` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 21 | 21 | ABL|AKBL|BAFL|BAHL|BIPL|BML|BOK|BOP|FABL|HBL |
| `0807` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | JSBLR1 |
| `0808` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 20 | 20 | ADOS|AGHA|ASL|ASTL|BCL|BECO|CSAP|DADX|DKL|DSL |
| `0808` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 2 | 2 | ASLCPS|ASLPS |
| `0808` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | KSBPR|MUGHALR1|MUGHALR2 |
| `0809` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 7 | 7 | AGL|AHCL|EFERT|ENGRO|FATIMA|FFBL|FFC |
| `0809` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 1 | 1 | AGLNCPS |
| `0809` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | FFBLR |
| `0810` | `debt_security` | `ticker_heuristic` | `ticker_regex:debt_security` | 1 | 1 | ASC |
| `0810` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 26 | 26 | BBFL|BFAGRO|BNL|CLOV|COLG|FCEPL|FFL|GDL|GLPL|ISIL |
| `0810` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 10 | 10 | ASCR|ASCR1|ASCR2|FFLR1|GLPLR|MFFLR|MFFLR1|TOMCLR|TREETR2|UNITYR3 |
| `0811` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 8 | 8 | BGL|FRCL|GGGL|GHGL|GVGL|KCL|STCL|TGL |
| `0811` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | GGGLR1|GHGLR3|GVGLR3 |
| `0812` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 30 | 28 | AGIC|AICL|ALAC|ALIFE|ASIC|ATIL|CENI|CSIL|CYAN|EFUG |
| `0812` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 6 | 6 | AGICR2|ALACR4|CSILR3|EWICR3|PAKQATAR|PKGIR |
| `0813` | `debt_security` | `ticker_heuristic` | `ticker_regex:debt_security` | 1 | 1 | FCSC |
| `0813` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 43 | 41 | 786|AHL|AKDSL|AMBL|ARMG|BIPLS|CASH|CYAN|DAWH|DEL |
| `0813` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 6 | 6 | 786R|AMBLR4|JSCLR1|LSECLR|LSEVLR|TSBLR1 |
| `0814` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 1 | 1 | SUHJ |
| `0815` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 7 | 7 | CASH|CPAL|GRYL|OLPL|PGLC|SLL|SPLC |
| `0816` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 6 | 6 | BATA|FIL|LEUL|PAKL|SGF|SRVI |
| `0818` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 25 | 25 | AKDCL|AKDHL|AKGL|ARPAK|DIIL|ECOP|GAMON|GEMPACRA|GOC|MACFL |
| `0818` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | SPELR |
| `0819` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 30 | 30 | ARM|AWWAL|BFMOD|FANM|FECM|FEM|FFLM|FHAM|FIBLM|FIMM |
| `0819` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 5 | 5 | BRR|BRRR|MODAMR|MODAMR1|WASLR |
| `0820` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 4 | 4 | MARI|OGDC|POL|PPL |
| `0821` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 11 | 11 | APL|BPL|HASCOL|HTL|OBOY|PSO|SHEL|SNGP|SPSL|SSGC |
| `0821` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | OBOYR1|OBOYR2|SHELR |
| `0822` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 12 | 12 | BPBL|CEPB|CPPL|GEMPAPL|IPAK|MACFL|MERIT|PKGS|PPP|RPL |
| `0822` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | MERITR2 |
| `0823` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 16 | 16 | ABOT|AGP|BFBIO|CPHL|FEROZ|GLAXO|GSKCH|HALEON|HINOON|HPL |
| `0823` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 5 | 5 | LIVENR|MACTER|MACTERR|SEARLR1|SEARLR2 |
| `0824` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 17 | 17 | AEL|ALTN|EPQL|GEMMEL|HUBC|KAPCO|KEL|KOHE|KOHP|LPL |
| `0825` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 5 | 5 | ATRL|BYCO|CNERGY|NRL|PRL |
| `0825` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | PRLR1 |
| `0826` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 32 | 32 | AABS|ADAMS|AGSML|ALNRS|ANSM|BAFS|CHAS|DWSM|FRSM|HABSM |
| `0826` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 2 | 2 | HSMCPS|TCORPCPS |
| `0826` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 6 | 6 | FRSMR|HSMPSR|HSMR3|MIRKSR|TCORPR1|TCORPR2 |
| `0827` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 7 | 7 | GATI|IBFL|IMAGE|NSRM|PSYL|RUPL|TRPOL |
| `0827` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | GATIR|IMAGER1|IMAGER2 |
| `0828` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 24 | 24 | AIRLINK|AVN|GEMNETS|GEMSPNL|HCL|HUMNL|ITANZ|LSEPL|MDTL|NETSOL |
| `0829` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 45 | 45 | ADMM|AEL|AHTM|ANL|ANLNV|ANTM|ARUJ|BHAT|BTL|CHBL |
| `0829` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 1 | 1 | CLCPS |
| `0829` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 4 | 4 | ANLR|CRTMR2|FMLR|STYLERSR |
| `0830` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 67 | 67 | AATM|AMTEX|ARCTM|ASTM|AWTX|BCML|BECO|BILF|CCM|CFL |
| `0830` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 3 | 3 | DINTR|SHDTR1|SNAIR |
| `0831` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 10 | 10 | ASHT|GTECH|ICCI|PRWM|SERF|SMTM|STJT|WHALE|YOUW|ZTL |
| `0831` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | SERFR |
| `0832` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | KHTC|PAKT|PMPK |
| `0833` | `debt_security` | `ticker_heuristic` | `ticker_regex:debt_security` | 1 | 1 | PNSC |
| `0833` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 9 | 9 | BLUEX|CLVL|GEMBLUEX|GEMUNSL|PIAA|PIAB|PIBTL|PICT|SLGL |
| `0833` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | CLVLR |
| `0834` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 3 | 3 | POML|SSOM|UNITY |
| `0834` | `right_or_entitlement` | `ticker_heuristic` | `ticker_regex:right_or_entitlement` | 1 | 1 | UNITYR2 |
| `0835` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 2 | 2 | BNL|BNWM |
| `0836` | `REIT` | `observed_sector_rule` | `sector_exact:0836` | 6 | 6 | DCR|GRR|IREIT|JSRR|SRR|TPLRF1 |
| `0837` | `ETF` | `observed_sector_rule` | `sector_exact:0837` | 10 | 9 | ACIETF|HBLTETF|JSGBETF|JSMFETF|MIIETF|MZNPETF|NBPGETF|NITGETF|UBLPETF |
| `0838` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 5 | 5 | BRRG|HUSI|JVDC|PACE|TPLP |
| `0838` | `preference_share` | `ticker_heuristic` | `sector_prefix:08+preference_suffix` | 1 | 1 | JVDCPS |
| `0839` | `ordinary_equity` | `sector_prefix_inference` | `sector_prefix:08` | 4 | 4 | IMAGE|INKL|MSOT|STYLERS |
| `36` | `debt_security` | `observed_sector_rule` | `sector_exact:36` | 47 | 47 | AGSILSC|AKBLTFC6|AKBLTFC7|BAFLTFC5|BAFLTFC6|BAFLTFC7|BAFLTFC8|BAHLTFC10|BAHLTFC9|BCEMSTSC |
| `36` | `government_security` | `ticker_heuristic` | `ticker_regex:government_security` | 84 | 84 | P01GHS100627|P01GHS130527|P01GHS150427|P01GHS200527|P01GHS230627|P01GHS290427|P01GIS031225|P01GIS040226|P01GIS060326|P01GIS061125 |
| `3610` | `government_security` | `ticker_heuristic` | `ticker_regex:government_security` | 30 | 30 | P03PIB040825|P03PIB050824|P03PIB200823|P05PIB131027|P05PIB290427|P10PIB101230|PK03TB010623|PK03TB021221|PK03TB040523|PK03TB060423 |