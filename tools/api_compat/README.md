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

## Reference assembly registration

`pinned_assembly_audit.py` decides whether a Microsoft XNA assembly may be used
as a behavior authority. The retained contract is the public-shape authority;
an assembly earns behavior authority only by machine-comparing its public
metadata against every contract entry it declares.

```text
python3 tools/api_compat/pinned_assembly_audit.py \
  --assembly-dir /path/to/xna/redistributable \
  --require-exact Microsoft.Xna.Framework.dll \
  --require-exact Microsoft.Xna.Framework.Graphics.dll \
  --output docs/generated/pinned-assembly-audit.json
```

The tool disassembles each assembly with `ikdasm`, reconstructs the public
type and member shape in the contract's own schema, and diffs it. It exits
nonzero if a calibration assembly is not reproduced exactly, or if its own
mutation self-tests fail.

`accessor_fallibility.py` derives, from the CIL of the same registered
assemblies, whether each public property accessor has a contract-relevant
failure path. Swift cannot express a throwing setter, so that per-accessor
answer decides whether a CLR property projects to `var P { get set }` or to
`var P { get }` plus a `SetP(_:) throws` writer method.

```text
python3 tools/api_compat/accessor_fallibility.py \
  --assembly-dir /path/to/xna/redistributable \
  --output tools/api_compat/reference/xna40-accessor-fallibility.json \
  --markdown docs/generated/accessor-fallibility-inventory.md
```

The emitted JSON is a *pinned reference*, hash-checked by `verify.py` against
`accessorFallibilitySha256` in `mapping-rules.json`, so the verifier still runs
with no Microsoft binary present. Every fallible verdict carries the shortest
call chain that reaches the throw and the exception types constructed there.
Thirty-four self-tests run on every invocation, including five mutations that
must flip a verdict and a two-sided bound proving that merging same-named
overloads by arity changes no accessor verdict.

`verify.py --graph-self-test --symbol-graph <path>` is the reader's own
negative-fixture suite: twelve mutations of the Symbol Graph the compiler
actually emitted, each of which must introduce a diagnostic the unmutated graph
does not already carry.

`--require-exact` is the calibration gate. The reconstruction's correctness is
not asserted, it is demonstrated on the assemblies whose provenance was already
established, and only then trusted for the others. No Microsoft binary is
stored in the repository; only the SHA-256 of each registered assembly is
retained, in `docs/xna-swift-mapping.md`.
