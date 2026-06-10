# Provenance Scripts

This directory stores scripts that are kept for reproducing completed Report 1
or historical weekly evidence, but should not be used as starting points for
new Report 2 work.

Compatibility wrappers remain at the old paths, so commands such as

```bash
python scripts/figures/report1_d2_replots.py
```

still work. The wrappers execute the archived source while preserving the old
`__file__` value, so old path-derived defaults are unchanged.

For new work, use the canonical entry points documented in `scripts/README.md`.
