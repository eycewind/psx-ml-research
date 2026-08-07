# C10 CP4B — KMI All Share Gap Diagnosis

This report diagnoses why simple chaining of incoming/outgoing tables does not reproduce the official constituent counts.

| Effective | Computed | Official | Gap | Screening symbols | Extra vs screening | Missing vs screening |
|---|---:|---:|---:|---:|---:|---:|
| 2022-07-15 | 255 | 252 | 3 | 0 | 255 | 0 |
| 2023-01-12 | 264 | 261 | 3 | 257 | 14 | 7 |
| 2023-07-10 | 258 | 251 | 7 | 0 | 258 | 0 |
| 2023-12-26 | 267 | 258 | 9 | 265 | 15 | 13 |
| 2024-06-25 | 266 | 255 | 11 | 270 | 21 | 25 |
| 2025-01-03 | 279 | 264 | 15 | 285 | 25 | 31 |
| 2025-06-10 | 274 | 257 | 17 | 0 | 274 | 0 |
| 2025-12-02 | 297 | 281 | 16 | 309 | 27 | 39 |

## Detailed exceptions

### 2022-07-15 (review_2021_h2)

- Missing outgoing symbols: none
- Computed members absent from screening list: AABS, ABOT, ACPL, ADAMS, AGIL, AGP, AGTL, AHTM, AIRLINK, AKGL, ALNRS, ANL, ANTM, APL, ARM, ARPL, ASC, ASHT, ASTM, ATLH, ATRL, AVN, AWWAL, BAFS, BATA, BCL, BCML, BECO, BERG, BFMOD, BGL, BHAT, BIFO, BIPL, BNL, BNWM, BPL, BRR, BTL, BUXL, BWCL, BWHL, BYCO, CCM, CEPB, CFL, CHAS, CHCC, CLOV, COLG, CPPL, CSAP, CTM, DAAG, DADX, DAWH, DCL, DCR, DFSM, DGKC, DINT, DLL, DOL, DSIL, DYNO, EFERT, ELCM, EMCO, ENGRO, EPCL, EXIDE, FANM, FATIMA, FCCL, FCEPL, FECM, FECTC, FEM, FEROZ, FFBL, FFLM, FHAM, FIBLM, FIMM, FLYNG, FML, FPJM, FPRM, FRCL, FRSM, FTMM, FTSM, FUDLM, GADT, GAIL, GAMON, GATI, GFIL, GGGL, GGL, GHGL, GHNI, GHNL, GIL, GLAXO, GLPL, GOC, GSKCH, GVGL, GWLC, HAEL, HAFL, HCAR, HINO, HINOON, HMM, HRPL, HSM, HTL, HUBC, IBFL, IBLHL, ICI, ICL, IDRT, IMAGE, INIL, INKL, ISL, ITTEFAQ, JATM, JDMT, JKSM, JOPP, JSML, KASBM, KEL, KHSM, KHYT, KOHC, KOHE, KOHP, KOIL, KSBP, KTML, LEUL, LPGL, LUCK, MACFL, MACTER, MARI, MEBL, MFFL, MIRKS, MLCF, MSCL, MTIL, MTL, MUGHAL, NATF, NESTLE, NML, NRL, NSRM, OCTOPUS, OGDC, ORIXM, ORM, OTSU, PABC, PAEL, PAKD, PAKMI, PAKOXY, PCAL, PHDL, PIBTL, PIM, PIOC, PKGS, PMI, PMRS, PNSC, POL, POML, POWER, PPL, PPP, PREMA, PSEL, PSMC, PSO, PSYL, PTL, RCML, REDCO, RMPL, RPL, RUPL, SANSM, SAPL, SAPT, SARC, SASML, SAZEW, SCL, SEARL, SERT, SFL, SGABL, SGF, SHDT, SHEL, SHEZ, SHFA, SHSML, SINDM, SITC, SMCPL, SML, SNAI, SNGP, SPEL, SPL, SSGC, SSML, SSOM, STCL, STJT, STML, STPL, SURC, SUTM, SYS, SZTM, TELE, TGL, THALL, THCCL, TICL, TOMCL, TOWL, TREET, TRSM, UBDL, UDPL, UNITY, UPFL, WAHN, WAVES, WTL, WYETH, YOUW, ZIL, ZTL
- Screening symbols absent from computed members: none
- Alias/corporate-action candidates: none

### 2023-01-12 (review_2022_h1)

- Missing outgoing symbols: none
- Computed members absent from screening list: AGSML, BCML, BYCO, GAIL, HABSM, HINO, KHSM, MTIL, ORIXM, SANSM, SASML, UCAPM, UNITY, WYETH
- Screening symbols absent from computed members: ARCTM, CLVL, CNERGY, GEMPAPL, GEMSPNL, GEMUNSL, OLPM
- Alias/corporate-action candidates: BYCO->CNERGY possible rename

### 2023-07-10 (review_2022_h2)

- Missing outgoing symbols: CNERGY
- Computed members absent from screening list: ABOT, ACPL, ADAMS, AGHA, AGIL, AGP, AGTL, AHTM, AIRLINK, AKGL, ALNRS, ANL, APL, ARM, ARPL, ASC, ASHT, ASTM, ATBA, ATLH, ATRL, AVN, BAFS, BATA, BCL, BCML, BECO, BERG, BFMOD, BGL, BIFO, BIPL, BNL, BNWM, BPL, BRR, BUXL, BWCL, BWHL, BYCO, CCM, CEPB, CFL, CHAS, CHCC, CLOV, COLG, CPHL, CRTM, CSAP, CTM, DAAG, DADX, DAWH, DCL, DCR, DFSM, DGKC, DIIL, DINT, DOL, DYNO, EFERT, ELCM, EMCO, ENGRO, EPCL, EXIDE, FABL, FATIMA, FCCL, FCEPL, FECM, FECTC, FEM, FEROZ, FFBL, FFLM, FHAM, FIBLM, FIMM, FLYNG, FML, FPJM, FPRM, FRCL, FRSM, FTMM, FTSM, FUDLM, FZCM, GAIL, GAMON, GATI, GGGL, GGL, GHGL, GHNI, GHNL, GIL, GLAXO, GLPL, GOC, GSKCH, GVGL, GWLC, HAEL, HAFL, HCAR, HINO, HINOON, HMM, HRPL, HSM, HTL, HUBC, HUSI, IBFL, IBLHL, ICI, ICL, ILP, IMAGE, INIL, INKL, ISL, ITTEFAQ, JDMT, JOPP, JSML, JVDC, KASBM, KCL, KEL, KHSM, KHYT, KOHC, KOHE, KOHP, KOHTM, KSBP, KTML, LEUL, LOTCHEM, LPGL, LPL, LUCK, MACFL, MACTER, MARI, MEBL, MERIT, META, MFFL, MLCF, MODAM, MSCL, MTIL, MTL, MUGHAL, NATM, NCPL, NESTLE, NETSOL, NML, NRL, NSRM, OBOY, OGDC, OML, ORIXM, ORM, PABC, PAEL, PAKD, PAKMI, PHDL, PIBTL, PICT, PIM, PIOC, PKGP, PKGS, PMI, PMRS, PNSC, POML, POWER, PPL, PPP, PREMA, PRL, PSEL, PSMC, PSO, PSYL, PTL, QUET, QUICE, RCML, RMPL, RPL, RUPL, SANSM, SAPL, SARC, SASML, SAZEW, SCL, SEARL, SERT, SFL, SGABL, SGF, SGPL, SHDT, SHEL, SHEZ, SHFA, SHSML, SINDM, SITC, SMCPL, SNAI, SNGP, SPEL, SPL, SSGC, STCL, STJT, STML, STPL, SURC, SUTM, SYS, SZTM, TELE, TGL, THALL, THCCL, TICL, TOMCL, TOWL, TPL, TPLP, TREET, TRSM, UBDL, UCAPM, UDPL, UNITY, WAHN, WAVES, WTL, WYETH, ZAHID, ZIL, ZTL
- Screening symbols absent from computed members: none
- Alias/corporate-action candidates: BYCO->CNERGY outgoing mismatch

### 2023-12-26 (review_2023_h1)

- Missing outgoing symbols: CLVL
- Computed members absent from screening list: BCML, BRR, BYCO, GAIL, GHNL, GSKCH, HMM, HSM, ICI, KASBM, KHSM, MTIL, ORIXM, PAKMI, WYETH
- Screening symbols absent from computed members: ARCTM, GAL, GEMPAPL, GEMSPNL, GEMUNSL, HALEON, LCI, MZNPETF, OLPM, SGABL, SGPL, SPL, TCORP
- Alias/corporate-action candidates: BYCO->CNERGY possible rename, ICI->LCI possible rename

### 2024-06-25 (review_2023_h2)

- Missing outgoing symbols: none
- Computed members absent from screening list: BCML, BRR, BYCO, FCL, GAIL, GHNL, GSKCH, HMM, HSM, ICI, KASBM, KHSM, MODAM, MTIL, ORIXM, PAKMI, PSMC, SAPL, STYLERS, WHALE, WYETH
- Screening symbols absent from computed members: ARCTM, BECO, DBSL, DMTX, FIL, FNBM, GAL, HALEON, HATM, HPL, JUBS, KSTM, LCI, LMSM, MZNPETF, NCML, OLPM, QUET, RUBY, SGABL, SKRS, SML, SPL, SUHJ, TCORP
- Alias/corporate-action candidates: BYCO->CNERGY possible rename, ICI->LCI possible rename

### 2025-01-03 (review_2024_h1)

- Missing outgoing symbols: none
- Computed members absent from screening list: ARM, BCML, BML, BRR, BYCO, FFBL, FUDLM, GAIL, GEMBCEM, GHNL, GSKCH, HMM, HSM, ICI, KASBM, KHSM, MODAM, MTIL, ORIXM, PAKMI, PSMC, SAPL, STYLERS, WHALE, WYETH
- Screening symbols absent from computed members: ARCTM, ASC, BECO, DBSL, DMTX, DWSM, FIL, FNBM, GAL, HALEON, HATM, HPL, JUBS, KSTM, LCI, LIVEN, MIIETF, MUBT, MZNPETF, NCML, OLPM, QUET, RUBY, SGABL, SKRS, SML, SPL, SSML, SUHJ, TCORP, WAVESAPP
- Alias/corporate-action candidates: BYCO->CNERGY possible rename, ICI->LCI possible rename

### 2025-06-10 (review_2024_h2)

- Missing outgoing symbols: WAVESAPP, ZAL
- Computed members absent from screening list: AABS, ABOT, ADAMS, AGIL, AGP, AGSML, AGTL, AHTM, AKGL, ALNRS, ANL, ANTM, APL, ARM, ARPL, ASHT, ASL, ATBA, ATRL, AVN, AWTX, BATA, BBFL, BCL, BCML, BECO, BERG, BFBIO, BFMOD, BGL, BIFO, BIPL, BML, BNL, BNWM, BPL, BRR, BRRG, BTL, BUXL, BWCL, BWHL, BYCO, CCM, CEPB, CFL, CHCC, CLOV, CLVL, CNERGY, CPHL, CPPL, CRTM, CTM, DAAG, DADX, DAWH, DCL, DCR, DFSM, DGKC, DINT, DLL, DOL, DYNO, ECOP, EFERT, ELCM, EMCO, ENGRO, EPCL, EXIDE, FABL, FANM, FATIMA, FCCL, FCEPL, FCL, FECM, FECTC, FEM, FEROZ, FFBL, FFL, FFLM, FHAM, FIBLM, FIMM, FLYNG, FML, FPJM, FPRM, FRCL, FRSM, FTMM, FTSM, FUDLM, FZCM, GAIL, GATI, GATM, GCIL, GEMBCEM, GEMBLUEX, GEMMEL, GEMPAPL, GEMSPNL, GFIL, GGGL, GGL, GHGL, GHNI, GHNL, GIL, GLAXO, GLPL, GOC, GSKCH, GTYR, GVGL, GWLC, HAEL, HAFL, HCAR, HINO, HINOON, HMM, HRPL, HSM, HTL, HUBC, IBFL, IBLHL, ICCI, ICI, ICL, IDRT, IDSM, ILP, IMAGE, INIL, INKL, IPAK, ISL, ITTEFAQ, JDMT, JDWS, JSML, JVDC, KASBM, KCL, KEL, KHSM, KHYT, KML, KOHE, KOHTM, KPUS, KSBP, LEUL, LIVEN, LOTCHEM, LPGL, LUCK, MACFL, MACTER, MARI, MEBL, MERIT, MFFL, MIRKS, MLCF, MODAM, MQTM, MSCL, MTIL, MTL, MUGHAL, NATF, NESTLE, NETSOL, NML, NRSL, NSRM, OBOY, OCTOPUS, OGDC, OML, ORIXM, ORM, PAEL, PAKD, PAKMI, PAKOXY, PIBTL, PIM, PIOC, PKGS, PMI, POML, POWER, PPL, PPP, PREMA, PRL, PSEL, PSMC, PSO, PSYL, QUICE, RCML, REDCO, RMPL, RPL, RUPL, SANSM, SAPL, SARC, SASML, SAZEW, SCL, SEARL, SEL, SERT, SFL, SGF, SGPL, SHCM, SHDT, SHEL, SHEZ, SHFA, SHSML, SINDM, SITC, SLGL, SMCPL, SNAI, SNGP, SPEL, SPWL, SSGC, SSOM, STCL, STJT, STL, STML, STYLERS, SURC, SYM, SYS, SZTM, TELE, TGL, TICL, TOMCL, TOWL, TPLP, TPLRF1, TPLT, TREET, TRSM, UBDL, UCAPM, UDPL, UNITY, UPFL, WAHN, WHALE, WYETH, YOUW, ZAHID, ZIL, ZTL
- Screening symbols absent from computed members: none
- Alias/corporate-action candidates: none

### 2025-12-02 (review_2025_h1)

- Missing outgoing symbols: none
- Computed members absent from screening list: ARM, BCML, BML, BRR, BYCO, DAWH, ENGRO, FFBL, FUDLM, GAIL, GHNL, GSKCH, HMM, HSM, ICI, KASBM, KHSM, MODAM, MTIL, ORIXM, PAKMI, PMI, PSMC, SAPL, SHEL, WHALE, WYETH
- Screening symbols absent from computed members: ARCTM, ASC, ASTM, BFAGRO, CWSM, DBSL, DFSM, DSL, DWSM, ENGROH, FIL, FNBM, GAL, GAMON, HALEON, HATM, HPL, IREIT, ITANZ, JATM, JUBS, KSTM, LCI, MIIETF, MUBT, MZNPETF, NCML, OLPM, QUET, RUBY, SKRS, SML, SPL, SSML, SUHJ, SWL, TCORP, WAFI, WASL
- Alias/corporate-action candidates: BYCO->CNERGY possible rename, ICI->LCI possible rename, ENGRO->ENGROH possible rename

## Interpretation

A non-zero gap means the official change table is not a complete event ledger. Delistings, defaulter-list changes, newly listed securities, ticker renames, mergers, and other corporate actions may be reflected in the official final count without appearing as ordinary incoming/outgoing rows.

Do not force counts by deleting arbitrary symbols. Use this report to identify each unexplained event against the relevant official source.
