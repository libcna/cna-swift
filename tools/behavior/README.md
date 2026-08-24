# Pure behavior corpus

The corpus executes only deterministic `PURE_XNA_DERIVED` observations. CNA is
not a golden source for these value semantics, and no native library is needed.
Selected exact Float results are compared by binary32 bit pattern; semantic
predicates cover NaN and value/object behavior where a single bit pattern is
not the reference contract.
