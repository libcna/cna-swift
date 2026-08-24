# CNA-Swift structural verifier

`verify.py` maps the pinned Microsoft XNA 4.0 Windows runtime contract through
`mapping-rules.json`, then compares it to Swift's compiler-emitted Symbol Graph.
Namespace markers and documented Swift synthesis are language infrastructure,
not XNA types or members. Enum raw values are the only compiler-Symbol-Graph
gap in the selected slice; the verifier supplements them from the same compiled
Swift source declarations and reports a category as unmeasured if that evidence
is unavailable.

Run from the repository root:

```text
python3 tools/api_compat/verify.py --self-test
swift package dump-symbol-graph
python3 tools/api_compat/verify.py \
  --symbol-graph .build/x86_64-pc-linux-gnu/symbolgraph/CNA.symbols.json \
  --output docs/generated/api-compat-report.json
```

The command exits nonzero in normal strict mode while future XNA types remain
missing. `--leak-only` fails only public implementation/pointer/FFI leaks.
