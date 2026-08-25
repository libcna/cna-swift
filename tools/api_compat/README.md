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

`dependency_graph.py` builds the public-signature dependency graph from the same
pinned contract and the generated strict report. `--type NAME` reports one
type's direct and transitive reverse consumers; without it the tool ranks every
still-missing type whose XNA dependencies are strict-complete, which is the
deterministic selection input for the next milestone.

```text
python3 tools/api_compat/dependency_graph.py \
  --report docs/generated/api-compat-report.json \
  --output docs/generated/dependency-graph.json
```
