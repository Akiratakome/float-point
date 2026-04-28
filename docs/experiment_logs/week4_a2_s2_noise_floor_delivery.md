# A2-S2 delivery log (MCA p=53 noise-floor)

**Date:** 2026-04-22 (same-day delivery; Stage 1 sent earlier today)
**Branch:** `week4-implementation`
**Commits:** `b8e0543` (scripts), `fb5d356` (3-mode detector), `425fb61` (tests), `48fd41f` (review fixes), `3f27d63` (dispatcher), `744badd` (python3 + GRID_RTOL)

## What was produced

### Data artefacts (under `experiments/week4/noise_floor/`, gitignored)

| Test | Solver | N samples | max(rho_std) | max(p_std) |
|---|---|---|---|---|
| sod | hllc | 30 | measured in npz | measured in npz |
| sod | rusanov | 30 | measured in npz | measured in npz |
| stationary_contact | hllc | 30 | " | " |
| stationary_contact | rusanov | 30 | " | " |
| toro4 (Lax) | hllc | 30 | 1.8e-15 | 4.4e-15 |
| toro4 (Lax) | rusanov | 30 | ~ | ~ |

All runs used Verificarlo `libinterflop_mca.so --mode=rr --precision-binary64=53` inside
the `verificarlo/verificarlo:latest` container (pip-installed CMake ≥3.18 per build pre-req).
Seeds are 64-bit `/dev/urandom` draws logged in each `seeds.csv`, with sha256 fingerprint
written into the `noise_floor.npz` metadata. Per-cell `std(ddof=1)` is computed over the
30 samples for each of `{rho, u, v, p}`.

### Figures (under `experiments/week4/figures/a2_s2/`, gitignored)

6 supervisor-facing PNGs (3 tests × 2 variables), 1-D solver output with the
`noise_floor`-mode tolerance envelope:

```
sod_rho_noise_floor.png      sod_p_noise_floor.png
stationary_contact_rho_noise_floor.png   stationary_contact_p_noise_floor.png
toro4_rho_noise_floor.png    toro4_p_noise_floor.png
```

`scripts/gen_a2_s2_figures.py` regenerates these from the existing `.npz` + sample data.

## What was dropped, and why

- **toro2** (two symmetric rarefactions, near-vacuum centre) hung on the first sample
  for 29 minutes under MCA p=53: stochastic rounding at the near-vacuum interface
  destabilises the CFL-limited `dt` and produces pathological sample times. Skipped
  with no partial data retained. Options for Week 5: (a) impose a `rho_floor` in
  `cons_to_prim` to survive negative-rho round-off, (b) drop toro2 from the A2 suite
  permanently and use toro5 (slow contact) as a 4th test instead.

## Known methodological note

The default `k_grad = 1.0` in `noise_floor` mode absorbs all shock-region differences
because `k_grad · |∇avg|` dominates `safety · max(nf_a, nf_b)` at every shock cell by
~14 orders of magnitude. All 6 figures therefore report **"No divergence detected"**
— the HLLC vs Rusanov difference at shocks stays within the `k_grad · |∇|` term's
allowance. This is the expected behaviour of the formula as specified in plan §A2.3;
the physical interpretation ("within 1-cell shock-location uncertainty") is what the
gradient term was designed to enforce. Calibrating `k_grad` against the noise-floor
data (plan §A2.4) is Week 5 work; the supervisor may also wish to run with
`k_grad = 0.0` to see the pure statistical boundary.

## Reproduction (one command, inside WSL + Docker Desktop)

```bash
docker run --rm -v "$(pwd)":/work -w /work \
    verificarlo/verificarlo:latest \
    bash scripts/noise_floor_all.sh      # ~10 min per (test, solver) pair

python3 scripts/gen_a2_s2_figures.py \
    --tests sod stationary_contact toro4  # skip toro2 per above
```

## Next (per §8 calendar)

- 04/23: A3 kickoff — done in this same session (LW3 IC + cfg + 2D runtime dispatch + local 2D runner).
- 04/24: A3 smoke — run `scripts/verificarlo_run_2d.sh --samples 3` once A2-S2 figures are sent.
