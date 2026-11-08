# M1 Clean-room research package

Scientific authority: `docs/M1_SINGLE_AUTHORITY.md`. Round 2 engineering findings: `docs/ROUND2_EXECUTION_REPORT.md` and `docs/evidence_review.md`.

From the repository root, install the explicitly recorded numerical dependencies and run the independent tests:

```powershell
python -m pip install -r research_m1/requirements.txt
python -m unittest discover -s research_m1/tests -v
$env:PYTHONPATH = (Resolve-Path research_m1/src).Path
python -m m1_research status
python -m m1_research reference
python -m m1_research reference-16r
python -m m1_research synthetic-pair
```

The single runtime configuration is `config/study.yaml`. Unknown scientific parameters remain null; the entry point refuses formal trajectory generation while required qualification is missing.

`reference-16r` evaluates only the 16R printed-precision reconstruction. It exports a conditional common-circle RF/RF/TF representative, preserves all printed AIP fields, and refuses a discontinuous path. The rounding hypothesis, deterministic representative rule, tests and limitations are recorded in `docs/16R_RF_PRECISION_AUDIT.md`; this is not a database-accuracy or full nominal-flight qualification.

`reference` additionally includes the `CONDITIONAL_LOC_REFERENCE` for 16L: one LOC line from `IF_REFERENCE_STATION` to THR. Published TJ954 is retained separately with its cross-date offset; `FAF_D6P2_ICU` is a conditional horizontal-range event, while FAP and GP_CAPTURE remain unresolved. See `docs/16L_LOC_REFERENCE_AUDIT.md`. This reference is not a LOC capture or aircraft execution trajectory. Vertical, performance, stochastic and cross-date evidence limits remain. `synthetic-pair` is an explicitly synthetic interface demonstration, not aircraft performance evidence or a Tianjin simulation. Neither command declares M2 readiness.

No historical project implementation is required at runtime. No original AIP or track data is redistributed. Refer to the source manifest for evidence fingerprints and allowed scope. M1/M2 scientific qualification remains open.
