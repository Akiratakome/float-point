# AI Infra Accelerator Qualification Project Execution Plan

**Date:** 2026-08-23
**Status:** Proposed and execution-ready
**Target duration:** 6 weeks for the core portfolio project; 2 optional weeks for the custom-kernel and multi-GPU extensions
**External project name:** `AccelQual — Reproducible AI Accelerator Qualification and Numerical Reliability Harness`

## Goal

Extend the existing numerical experiment harness into a workload-agnostic AI
infrastructure project that can qualify real LLM inference workloads across
hardware, execution backends, arithmetic modes, and serving loads. The finished
project must jointly measure correctness, latency, throughput, memory use, and
reproducibility, while retaining the existing HRSC solver as a numerically
sensitive non-ML accelerator stress workload.

The core deliverable is not a new model and not a chat application. It is a
repeatable qualification platform:

```text
workload definition
    -> environment/build qualification
    -> local or Slurm execution
    -> correctness + performance + resource gates
    -> aggregate + compare + profile
    -> evidence manifest + report
```

## Success Definition

The project is resume-ready after the P0 acceptance gate, even if the optional
kernel and multi-GPU phases are not completed.

### P0 — required portfolio core

1. A real, pinned Transformer model runs through at least PyTorch eager,
   `torch.compile`, and vLLM paths where supported.
2. FP32/TF32, FP16, and BF16 arithmetic modes are qualified rather than merely
   timed; unsupported combinations fail with a structured capability result.
3. A small model is reproducible across the Cambridge accelerator axis:
   Lovelace's 2 x A30 24 GB (Ampere, compute capability 8.0) and a Slurm-allocated
   RTX 5090 32 GB on `phy-thetis` or `phy-damysus` (Blackwell, compute capability
   12.0). `phy-cerberus5` supplies a CPU reference; a local RTX 5070 is optional
   developer-smoke evidence, not a P0 dependency.
4. A pinned 7B-class model has a production-shaped vLLM serving study on the
   common feasible A30/RTX 5090 workload intersection. RTX 5090-only capacity
   points are reported separately and are not presented as matched comparisons.
5. Results include output fidelity, TTFT, TPOT, ITL, throughput, peak memory,
   environment provenance, and bounded claim text.
6. Selected configurations have PyTorch Profiler, Nsight Systems, and Nsight
   Compute evidence explaining the observed bottlenecks.
7. One command reproduces a small smoke packet without regenerating the large
   experiment matrix.

### P1 — differentiating kernel extension

Implement a precision-aware fused residual + RMSNorm inference kernel in
Triton and C++/CUDA, compare it with PyTorch eager and `torch.compile`, profile
it, and integrate it into one real Transformer block. A neutral or negative
end-to-end result is acceptable if the correctness and bottleneck analysis are
sound.

### P2 — optional distributed extension

Qualify the two-GPU topology available on Lovelace (2 x A30) and the two-GPU
topology allocated on one CSC GPU node (2 x RTX 5090), then compare NCCL
collectives and vLLM tensor parallelism at TP=1 and TP=2 where supported. This
is an intra-node topology case study, not a large-scale distributed-training
claim.

## Existing Assets To Reuse

- `scripts/harness/`: versioned run records, failure categories, artifact
  freshness checks, subprocess execution, Git provenance, and compatibility
  metadata.
- `scripts/run_matrix.py`: canonical matrix entry point.
- `scripts/metrics/`: numerical comparisons and reusable metric conventions.
- `scripts/cluster/`: Slurm and Apptainer patterns.
- `scripts/harness/experiment_manifest.py`: lifecycle and evidence routing.
- Existing CPU/CUDA HRSC workloads: retain as a second workload family and as
  evidence that the platform is not hard-coded to Transformers.
- Existing reporting discipline: machine-readable summary first, plots second,
  explicit claim boundaries, and no retention of large transient grids/traces.

## Cambridge LSC/CSC Hardware Topology Lock

The resource baseline below comes from the LSC systems, CSC cluster, CUDA,
storage, and computation guidance pages, reviewed on 2026-08-23. The systems
inventory itself was last updated on 2026-08-17. Static documentation is useful
for planning; the environment record captured inside each allocation is the
authority for a result.

| Role | Host/allocation | Documented CPU/RAM | Accelerator and local storage | Project use |
|---|---|---|---|---|
| Control plane | `athena` / `csc-athena` | Xeon E5-2430 v2, 6 physical cores, 32 GB; Ubuntu 24.04.4 | no NVIDIA GPU | submit, inspect, stage, and aggregate only; no long-running benchmark |
| Direct CPU utility | `apollo` | Xeon E5-2670, 16 physical cores, 64 GB; Ubuntu 24.04.3 | no NVIDIA GPU; 1.8 TB `/local/data` | light development or aggregation fallback after checking load; not a GPU or headline performance target |
| CPU reference plane | `phy-cerberus5` in `csc-mphil` | Xeon Gold 5418Y, 48 physical cores; 257 GB physical RAM in the systems table and 248 GB in the cluster allocation guide; Ubuntu 24.04.4 | no NVIDIA GPU; 7.3 TB `/local/data` | small-model FP32 CPU oracle, portability, and host-overhead experiments |
| Ampere execution plane | `lovelace` / `csc-lovelace` via direct SSH | Xeon Silver 4314, 32 physical cores, 257 GB; Ubuntu 24.04.4 | 2 x NVIDIA A30 24 GB, compute capability 8.0; 7.0 TB `/local/data`, 101 GB `/scratch` | required heterogeneous-GPU correctness and performance target when the shared host is uncontended |
| Blackwell execution plane A | `phy-damysus` in `csc-mphil-gpu` | Threadripper PRO 7975WX, 32 physical cores, 128 GB | 2 x RTX 5090 32 GB, compute capability 12.0; 7.3 TB `/local/data`, approximately 781 GB `/scratch` | qualify one of two GPU node types; candidate canonical scheduled benchmark target |
| Blackwell execution plane B | `phy-thetis` in `csc-mphil-gpu` | Threadripper PRO 9975WX, 32 physical cores, 128 GB | 2 x RTX 5090 32 GB, compute capability 12.0; 7.3 TB `/local/data`, approximately 797 GB `/scratch` | qualify one of two GPU node types; candidate canonical scheduled benchmark target |

Operational facts that shape the design:

- The systems table's total device count can include display/consumer devices.
  The experiment axis follows the CUDA/cluster guides' explicit production
  inventory: 2 x A30 on Lovelace and 2 x RTX 5090 per CSC GPU node. The runtime
  probe enumerates every visible device and rejects an unexpected model rather
  than selecting GPU index by assumption.
- CSC jobs are submitted from Athena with `--clusters=CSC`. The documented
  partitions are `csc-mphil` and `csc-mphil-gpu`; both have a six-hour maximum,
  and the GPU partition permits at most two requested GPUs.
- CSC nodes are non-exclusive and may host up to four jobs. A headline run must
  record allocation, co-tenant/utilization evidence, requested CPU/RAM/GPU
  resources, and the effective node name. A quiet-node retry is preferred to
  pretending an allocation was exclusive.
- Lovelace is a direct-login shared machine, not a Slurm target. Check CPU/GPU
  occupancy first, use `nice -19` for long processes, pin `CUDA_VISIBLE_DEVICES`,
  and treat contaminated runs as non-headline evidence.
- Use `/local/data/public/<userid>/aiinfra` on the executing node for model
  cache, staged assets, and raw results. `/data/athena` can stage compact inputs
  for Slurm jobs, but assets must be copied to node-local storage and hash-checked
  before timed execution. Home directories, remote I/O, and model download are
  outside headline timings.
- Disk free-space figures in the inventory are snapshots, not capacity promises;
  record current free space before staging and clean transient assets promptly.
- The cluster guide's fixed-frequency CPU procedure is documented for
  `phy-cerberus4-8`, so it may be tested for a controlled Cerberus CPU baseline.
  Do not apply or imply the same control on the AMD GPU nodes or Lovelace without
  a separate capability check.
- The general CUDA guide documents `/lsc/opt/cuda-12.6`, while the CSC example
  uses `/lsc/opt/cuda-12.9`. Probe the actual driver/toolkit/compiler paths on
  every host; do not infer one common software stack from the hardware list.
- Prefer one pinned Apptainer image digest across A30 and RTX 5090 if runtime
  probes prove it works on both. Otherwise lock an architecture-specific
  environment for each target and treat software stack as an explicit
  experimental factor, not a hidden hardware difference.

Planning sources:

- [LSC systems inventory](https://www-internal.lsc.phy.cam.ac.uk/systems.shtml)
- [CSC Slurm cluster guide](https://www-internal.lsc.phy.cam.ac.uk/csc_cluster.shtml)
- [CUDA systems and toolkit guide](https://www-internal.lsc.phy.cam.ac.uk/cuda.shtml)
- [Data and scratch storage guide](https://www-internal.lsc.phy.cam.ac.uk/data.shtml)
- [Compute-intensive job etiquette](https://www-internal.lsc.phy.cam.ac.uk/computation.shtml)

## Global Constraints

- Do not change solver numerics, existing cfg defaults, established HRSC binary
  formats, or historical result metadata.
- All AI dependencies and build steps are opt-in. The current CMake and Python
  test paths must continue to work without PyTorch, vLLM, Triton, or a GPU.
- Do not commit model weights, Hugging Face caches, virtual environments, raw
  profiler traces, vLLM caches, or large request logs.
- Never describe a requested backend as the effective backend. Record the
  resolved attention backend, compiler mode, dtype, CUDA version, driver,
  PyTorch/vLLM versions, GPU UUID/model, and model/tokenizer revisions.
- Correctness gates are hard. Performance thresholds are not hard gates until a
  canonical baseline and variance envelope have been recorded.
- OOM and unsupported configurations must be explicit structured outcomes; they
  must not disappear from aggregates.
- Cross-hardware fidelity and within-hardware precision fidelity are separate
  comparisons. Do not attribute their difference to precision alone.
- Use deterministic greedy decoding for fidelity comparisons. Sampling-based
  text is not an accuracy oracle.
- All headline timing excludes environment setup and model download. Record
  model load/cold-start time separately from steady-state inference.
- Record `hostname`, Slurm job/allocation fields, visible GPU UUIDs, CPU model,
  CPU affinity, RAM, local filesystem, concurrent GPU-process snapshot, and
  power/clock/temperature state with every benchmark packet. A partition name or
  requested GPU count is never sufficient provenance.
- Athena is the control plane only. Direct work on Lovelace/Apollo follows the
  shared-machine etiquette above; scheduled work must stay within the documented
  six-hour and resource limits.
- Preserve the pipeline shape:
  `config -> build/environment -> run -> measure -> aggregate -> plot`.

## Locked Workload Scope

### Models

- **Smoke/reference model:** `Qwen/Qwen2.5-0.5B-Instruct`.
  Pin the exact repository revision and tokenizer revision during Task 1. This
  model supplies FP32 reference work on `phy-cerberus5` and matched FP32/TF32,
  FP16, and BF16 qualification on both A30 and RTX 5090.
- **Serving model:** `Qwen/Qwen2.5-7B-Instruct`.
  Pin the exact revision during Task 1. FP32 is not required for the 7B model;
  the required serving modes are FP16 and BF16, plus one quantized mode only if
  the chosen vLLM version supports it without an unreviewed model conversion.
  The 24 GB A30 and 32 GB RTX 5090 receive the same preflight; OOM/capacity limits
  define a common comparison subset plus architecture-specific capacity rows.
- If either model becomes inaccessible or incompatible, replace it only through
  a recorded decision in `docs/aiinfra/environment_matrix.md`; do not silently
  substitute a different model between runs.

### Data

- A tracked deterministic prompt fixture supplies CI and correctness smoke
  inputs.
- A pinned ShareGPT-style prompt subset supplies workload-shaped serving
  inputs. Store only the selected prompt IDs/text allowed by its license and a
  SHA-256 digest of the normalized fixture.
- A pinned WikiText-2 test subset supplies the small-model perplexity check.
- All dataset acquisition is an explicit preparation step. Unit tests never
  access the network.

### Core Arithmetic Modes

- `fp32_strict`: FP32 weights/activations, TF32 disabled.
- `fp32_tf32`: FP32 model with TF32 matmul enabled and the effective PyTorch
  matmul policy recorded.
- `fp16`: FP16 model and kernels.
- `bf16`: BF16 model and kernels.
- `int8` or weight-only quantization is a P1 experiment and must name the exact
  method, such as SmoothQuant-compatible W8A8 or AWQ. Do not use the generic
  label `int8` when weights and activations use different formats.
- FP8 is deferred until the software stack exposes a verified effective FP8
  path; hardware support alone is insufficient.

## Measurement Contract

### Completion gate

A workload group is complete only when:

1. the process exits successfully;
2. every expected request completes;
3. result JSON validates against the workload-result schema;
4. required prompts, output tokens, and timing samples are present;
5. no output/logit/metric contains NaN or Inf;
6. model, tokenizer, dataset, environment, and code revisions are recorded;
7. no unclassified exception or silent backend fallback occurred.

### Fidelity metrics

For the small model, compare lower-precision/configuration results against the
same-hardware PyTorch-eager `fp32_strict` reference:

- next-token logit relative L2 and maximum absolute error;
- KL divergence on aligned logits or a documented top-k approximation when the
  backend exposes only logprobs;
- top-1 agreement and top-k set agreement;
- greedy token exact-match rate and common-prefix length;
- perplexity on the pinned WikiText-2 subset for supported offline backends.

Thresholds are not invented in advance. Task 6 first measures same-backend
repeatability/noise, then locks thresholds in a reviewed configuration before
running the held-out headline matrix.

### Performance and resource metrics

- offline/cold: model load time and first-inference latency, reported separately;
- offline/warm: prefill latency, decode latency, tokens/s, median and IQR;
- serving: TTFT, TPOT, ITL, and E2E latency at p50/p95/p99;
- serving capacity: request throughput, output-token throughput, and goodput
  under a predeclared SLO;
- resource: peak allocated/reserved GPU memory, sampled GPU utilization, and
  optional power samples clearly labelled as sampled rather than exact energy;
- profiling: kernel/operator time, achieved memory bandwidth, occupancy,
  arithmetic intensity, and compute-bound versus memory-bound classification.

### Timing protocol

- Offline groups: at least 3 warm-ups and 20 measured repetitions for the
  headline small-model matrix.
- Serving groups: at least 200 completed requests after server readiness and
  warm-up, unless an explicit time-budget pilot justifies a larger number.
- CUDA synchronization must bracket device timing. End-to-end client timing is
  still the serving headline.
- Record every raw timing sample in machine-readable local output; retain only
  compact samples/summaries required for review.

## Target Repository Layout

```text
configs/aiinfra/
  models.json
  smoke/*.cfg
  offline/*.json
  serving/*.json
  qualification_thresholds.json
scripts/aiinfra/
  config.py
  result_schema.py
  run_llm_workload.py
  prepare_assets.py
  environment.py
  backends/
  aggregate.py
  compare.py
  serve.py
  profile.py
  requirements.in
  requirements.lock.txt
scripts/cluster/aiinfra/
  run_cpu_reference.slurm
  run_gpu_workload.slurm
  run_lovelace.sh
src/ai_kernels/rmsnorm/
tests/py/test_aiinfra_*.py
experiments/aiinfra/              # generated/ignored except selected evidence
docs/aiinfra/
  README.md
  ARCHITECTURE.md
  cambridge_resources.md
  REPRODUCE.md
  EVIDENCE.md
  RESULTS.md
```

---

## Task 1: Environment, model, and dataset decision lock

**Files:**

- Create: `docs/aiinfra/README.md`
- Create: `docs/aiinfra/environment_matrix.md`
- Create: `docs/aiinfra/cambridge_resources.md`
- Create: `configs/aiinfra/models.json`
- Create: `scripts/aiinfra/requirements.in`
- Create after resolution: `scripts/aiinfra/requirements.lock.txt`
- Create: `scripts/aiinfra/environment.py`
- Create: `scripts/aiinfra/prepare_assets.py`
- Test: `tests/py/test_aiinfra_environment.py`

- [ ] Turn the documented Athena, Apollo, Lovelace, `phy-cerberus5`,
  `phy-thetis`, and `phy-damysus` inventory into a checked-in resource registry.
  Preserve the documented 257 GB physical versus 248 GB Slurm-visible Cerberus
  RAM discrepancy until the runtime probe resolves its meaning.
- [ ] Run a read-only probe on Athena and Apollo, on Lovelace, in a
  `phy-cerberus5` CPU allocation, and in one-GPU and two-GPU allocations on both
  CSC GPU node types when scheduling permits. Capture `sinfo`, `scontrol show
  node`, `SLURM_JOB_*`, CPU affinity, `nvidia-smi -L`, `nvidia-smi topo -m`,
  `deviceQuery`, local disk paths, and CUDA/Apptainer availability.
- [ ] Use the current documented Slurm request form (`--clusters=CSC`,
  `--partition=csc-mphil-gpu`, `--gpus=N`). Retain the repository's historical
  `--gres=gpu:N` result as provenance or a compatibility fallback only after the
  live scheduler probe; never claim that a requested device was allocated
  without recording `CUDA_VISIBLE_DEVICES` and the effective hostname.
- [ ] Establish the Linux execution environment on the school nodes. A local
  WSL/RTX 5070 environment may be added for fast developer smoke but is not a
  required P0 target and does not replace either school GPU architecture.
- [ ] Resolve a compatible Python/PyTorch/CUDA/vLLM/Triton set and freeze exact
  packages. Keep the existing project Python environment untouched.
- [ ] Review model and dataset licences, download them into an external cache,
  and record immutable revisions and normalized data hashes.
- [ ] Implement a read-only environment probe that emits JSON and never installs
  packages or downloads assets.
- [ ] Unit-test JSON stability with mocked PyTorch/NVIDIA responses.
- [ ] Prefer one pinned Apptainer image digest across Ampere and Blackwell. If
  that is not viable, freeze separate named environments and record their
  differences before interpreting any cross-hardware result.
- [ ] Run the probe on every required execution plane and save compact outputs
  under `docs/aiinfra/`; generate commands through the harness rather than using
  undocumented one-off shell history.

**Gate E0:** `phy-cerberus5`, Lovelace A30, and at least one instance of each CSC
GPU node type have a recorded capability matrix. The small model runs as an FP32
CPU reference and in FP32 plus one 16-bit mode on both GPU architectures. The 7B
model runs in FP16 or BF16 on an A30 and an RTX 5090, or a structured preflight
record establishes the unsupported boundary. Node-local storage and scheduling
paths are validated; unsupported modes are enumerated.

---

## Task 2: Generalize the harness for non-HRSC workload commands

**Files:**

- Modify: `scripts/run_matrix.py`
- Modify: `scripts/harness/contracts.py`
- Modify: `scripts/harness/runner.py`
- Modify: `scripts/harness/artifacts.py`
- Modify: `scripts/harness/metadata.py` only if additive workload fields require it
- Test: `tests/py/test_harness_runner.py`
- Test: `tests/py/test_harness_scripts.py`
- Test: `tests/py/test_aiinfra_harness_contract.py`

- [ ] Add an optional matrix `arguments` array inserted between `binary` and the
  generated config. Legacy matrices without `arguments` must construct the
  identical command they do today.
- [ ] Add an optional `artifact_kind`; preserve `hrsc_binary` behavior and make
  unknown kinds fail closed.
- [ ] Preserve the legacy `output_format=binary` config overlay only for the
  existing HRSC path. A `workload_result` run writes only its configured JSON
  `output_file`; it must not receive a misleading binary-format key.
- [ ] Add a versioned `workload_result` JSON artifact validator. It must reject
  future schema versions, failed/incomplete result status, non-finite headline
  metrics, count mismatches, and absent provenance.
- [ ] Extend structured completion parsing additively with
  `kind=workload completed=<n> expected=<n>`. Legacy simulation status lines
  without `kind` retain the existing `final_time/target_time/steps` contract.
- [ ] Map explicit workload capability rejection to
  `unsupported_capability`; add the explicit additive failure category
  `resource_exhausted` for OOM; retain `infrastructure_error` for timeout; and
  map invalid metrics to `artifact_error` or `numerical_failure` as appropriate.
- [ ] Add dry-run coverage for command construction and config overlays.
- [ ] Run all existing harness tests to prove no metadata or command regression.

**Gate H0:** Existing HRSC matrix tests are unchanged and green; a fake Python
workload can be run through `run_matrix.py`, produce a fresh validated JSON
artifact, and receive `completion.reported=true` with workload counts.

---

## Task 3: Define AI workload configuration and result schemas

**Files:**

- Create: `scripts/aiinfra/config.py`
- Create: `scripts/aiinfra/result_schema.py`
- Create: `scripts/aiinfra/backends/base.py`
- Create: `scripts/aiinfra/backends/fake.py`
- Create: `configs/aiinfra/smoke/qwen05b-eager-fp32.cfg`
- Test: `tests/py/test_aiinfra_config.py`
- Test: `tests/py/test_aiinfra_result_schema.py`

- [ ] Define required config fields for model/revision, backend, arithmetic mode,
  attention backend, prompt source, input/output lengths, batch/concurrency,
  warm-ups, repetitions, seed, output artifact, and timeout.
- [ ] Reject unknown keys and invalid combinations before loading a model.
- [ ] Define `hrsc.ai-workload-result` schema version 1 with these sections:
  `identity`, `environment`, `workload`, `completion`, `correctness`,
  `performance`, `resources`, `artifacts`, and `failure`.
- [ ] Store raw samples separately from aggregate percentiles so summaries do
  not need to reconstruct statistics from prose.
- [ ] Define a backend protocol with `capabilities`, `prepare`, `warmup`,
  `infer`, `synchronize`, and `close` operations.
- [ ] Use the fake backend to exercise success, unsupported, OOM, NaN, partial
  completion, and timeout paths without AI dependencies or a GPU.

**Gate S0:** Config and result schemas have positive and negative unit tests,
and the fake workload produces a completion-attested result through the shared
harness.

---

## Task 4: PyTorch eager reference workload

**Files:**

- Create: `scripts/aiinfra/run_llm_workload.py`
- Create: `scripts/aiinfra/backends/hf_eager.py`
- Create: `scripts/aiinfra/prompts.py`
- Create: `configs/aiinfra/smoke/matrix.json`
- Test: `tests/py/test_aiinfra_hf_backend.py`
- Test: `tests/py/test_aiinfra_prompt_fixture.py`

- [ ] Load only the pinned local model/tokenizer revision; headline execution
  must not silently fetch a newer revision.
- [ ] Implement deterministic tokenization, greedy decoding, fixed seeds, and
  explicit CUDA synchronization.
- [ ] Separate model load, first inference, warm-up, prefill, and decode timing.
- [ ] Capture logits/logprobs required for fidelity without retaining full large
  tensors after aggregation.
- [ ] Capture peak allocated/reserved memory and the resolved attention backend.
- [ ] Emit structured success/failure and a schema-valid result artifact.
- [ ] Run the required smoke matrix: `phy-cerberus5` FP32 CPU reference;
  Lovelace A30 FP32/BF16; and Slurm RTX 5090 FP32/BF16. Run once on both
  `phy-thetis` and `phy-damysus` to qualify node types, then select one as the
  canonical Blackwell benchmark target. Local RTX 5070 is an optional extra row;
  Athena and Apollo are never labeled accelerator rows.
- [ ] Retain configs, environment, summaries, and logs; do not commit caches or
  weights.

**Gate W0:** Every required smoke row completes, or an unsupported row is
explained by the E0 capability matrix. Repeated FP32 eager output on CPU, A30,
and RTX 5090 is deterministic under greedy decoding within its locked gate.

---

## Task 5: `torch.compile` and vLLM backend adapters

**Files:**

- Create: `scripts/aiinfra/backends/torch_compile.py`
- Create: `scripts/aiinfra/backends/vllm_offline.py`
- Create: `scripts/aiinfra/capabilities.py`
- Test: `tests/py/test_aiinfra_capabilities.py`
- Test: `tests/py/test_aiinfra_compile_backend.py`
- Test: `tests/py/test_aiinfra_vllm_backend.py`

- [ ] Record compile time separately from steady-state `torch.compile` timing.
- [ ] Record graph breaks/recompilations where the PyTorch APIs expose them.
- [ ] Resolve and record the effective SDPA/FlashAttention/backend selection.
- [ ] Configure vLLM for deterministic greedy output and fixed model revision.
- [ ] Normalize common output fields while retaining backend-native metrics in a
  namespaced section.
- [ ] Implement capability checks before expensive load: backend, dtype,
  quantization, device count, model fit estimate, and attention backend.
- [ ] Unit-test adapters with fakes; GPU integration tests are opt-in markers.
- [ ] Add bridge configurations that run the small model through all three
  backends in BF16 on one hardware.

**Gate B0:** Supported bridge rows complete with aligned tokenization and
greedy decoding. Any different token result is retained as a fidelity result,
not suppressed or forced to match.

---

## Task 6: Fidelity metrics, calibration, and locked qualification gates

**Files:**

- Create: `scripts/metrics/llm_fidelity.py`
- Create: `scripts/aiinfra/calibrate.py`
- Create: `configs/aiinfra/qualification_thresholds.json`
- Test: `tests/py/test_llm_fidelity.py`
- Test: `tests/py/test_aiinfra_calibration.py`

- [ ] Implement relative L2, Linf, KL/top-k KL, top-1 agreement, top-k set
  agreement, token exact-match, and common-prefix metrics with finite checks.
- [ ] Implement perplexity with explicit token counts and no padding leakage.
- [ ] Handle backend top-k logprobs without pretending they are complete logits;
  name approximate metrics explicitly.
- [ ] Measure five same-backend repeated blocks for `fp32_strict`, FP16, and BF16
  to establish deterministic/noise floors.
- [ ] Run a calibration prompt subset, select bounded thresholds, document the
  reasoning, and lock the JSON before running held-out headline prompts.
- [ ] Give each gate a question and claim boundary; for example, top-1 agreement
  does not imply distributional equality.

**Gate Q0:** Thresholds are machine-readable, source-hashed, and locked before
headline execution. A deliberately perturbed fixture fails each relevant gate.

---

## Task 7: Offline cross-backend and cross-hardware qualification matrix

**Files:**

- Create: `configs/aiinfra/offline/matrix-small.json`
- Create: `scripts/aiinfra/aggregate.py`
- Create: `scripts/aiinfra/compare.py`
- Create: `scripts/figures/aiinfra_qualification.py`
- Test: `tests/py/test_aiinfra_aggregate.py`
- Test: `tests/py/test_aiinfra_compare.py`

### Planned matrix

- Hardware: Lovelace A30 and a Slurm-allocated RTX 5090 are the primary matched
  accelerator targets. `phy-cerberus5` supplies a bounded FP32 CPU reference.
  Both CSC GPU node types receive qualification smoke; one locked node type owns
  the repeated Blackwell headline matrix. Local RTX 5070 rows are optional and
  excluded from required cross-hardware claims.
- Model: pinned 0.5B reference model.
- Backend: PyTorch eager and `torch.compile`; vLLM bridge rows where meaningful.
- Mode: `fp32_strict`, `fp32_tf32`, FP16, BF16, capability-gated.
- Input length: 128 and 1024 tokens.
- Batch: 1 and 8, reduced only when memory preflight rejects a row.
- Output: 64 greedy tokens for generation timing; one-step logits for full
  fidelity metrics.
- Repetitions: 3 warm-ups + 20 measured repetitions per group.
- Comparison sets: report the A30/RTX 5090 common feasible intersection as the
  matched architecture study. Report hardware-specific maximum batch/context
  capacity in a second table; do not fill infeasible A30 rows with smaller work
  and call them like-for-like.

- [ ] Generate the matrix from one tracked definition rather than hand-writing
  dozens of run configs.
- [ ] Keep unsupported rows in the summary with reason and capability evidence.
- [ ] Compare precision within hardware/backend first; compare hardware at fixed
  backend/mode in a separate table.
- [ ] Aggregate medians, IQRs, bootstrap confidence intervals, fidelity gates,
  peak memory, and completion counts.
- [ ] Produce a Pareto plot only for comparable rows: performance versus a named
  fidelity metric, with memory as a separate encoding or panel.
- [ ] Produce one concise cross-hardware plot without claiming architectural
  causation before profiling.
- [ ] On Lovelace, admit a timing row only when pre/post utilization snapshots
  and process monitoring show no conflicting GPU work. On CSC, record the
  effective node and co-tenant evidence; neither direct login nor Slurm implies
  exclusive access.

**Gate P0-offline:** Every planned row is success or explicitly unsupported;
no row silently disappears. All headline claims are generated from validated
metadata and held-out prompts.

---

## Task 8: vLLM online serving benchmark and SLO goodput

**Files:**

- Create: `scripts/aiinfra/serve.py`
- Create: `scripts/aiinfra/parse_vllm_benchmark.py`
- Create: `configs/aiinfra/serving/matrix-qwen7b.json`
- Create: `scripts/cluster/aiinfra/run_vllm_serving.slurm`
- Create: `scripts/cluster/aiinfra/run_lovelace_serving.sh`
- Test: `tests/py/test_aiinfra_vllm_parser.py`
- Test: `tests/py/test_aiinfra_server_lifecycle.py`

### Planned matrix

- Hardware: one Lovelace A30 and one Slurm-allocated RTX 5090 for the matched
  common workload; the RTX 5090 additionally owns the maximum-capacity sweep.
- Model: pinned 7B serving model.
- Arithmetic: FP16 and BF16; one named quantized mode only after capability
  validation.
- Prompt lengths: 128, 1024, and 4096 tokens.
- Generated length: fixed 128-token request target.
- Common concurrency/request-rate points: 1, 4, and 8 after a memory preflight.
  Continue each architecture's independent capacity search to 16/32 only as
  capability rows, with OOM or saturation retained as results.
- At least 200 completed requests per headline point.

- [ ] Launch the server in a bounded process group or Slurm allocation, wait for
  a health/readiness gate, warm it, run the client, and always tear it down.
- [ ] Stage the pinned model from shared storage to node-local
  `/local/data/public/<userid>/aiinfra`, verify its manifest hash, and keep
  staging and model-load time outside steady-state request timing.
- [ ] Use the direct Lovelace wrapper only after an idle-host gate. Use the Slurm
  wrapper with an explicit GPU count, CPU/RAM request, six-hour bound, and node
  identity capture. If Lovelace cannot provide an uncontended window, retain its
  correctness/capacity results but give no A30 performance headline.
- [ ] Reuse `vllm bench serve` output where possible; do not reimplement its
  client timing without a demonstrated need.
- [ ] Parse request throughput, output-token throughput, TTFT, TPOT, ITL, E2E,
  failures, and native benchmark metadata into the shared result schema.
- [ ] After a pilot, lock a project-specific TTFT/TPOT SLO and report goodput at
  each load. Clearly state that this is a project SLO, not an industry standard.
- [ ] Record CUDA OOM, request failure, timeout, or server crash as failed rows.
- [ ] Generate latency-throughput and goodput-concurrency plots with p95/p99
  tails, not averages alone.

**Gate P0-serving:** The full supported matrix is completion-attested, tail
latency and throughput are jointly reported, and the server lifecycle leaves no
orphan process after success or failure.

---

## Task 9: Profiler-driven bottleneck analysis

**Files:**

- Create: `scripts/aiinfra/profile.py`
- Create: `scripts/aiinfra/parse_nsys.py`
- Create: `scripts/aiinfra/parse_ncu.py`
- Create: `configs/aiinfra/profile/selected.json`
- Create: `scripts/cluster/aiinfra/run_profiles.slurm`
- Create: `scripts/cluster/aiinfra/run_lovelace_profiles.sh`
- Test: `tests/py/test_aiinfra_profile_parsers.py`

- [ ] Select configurations before profiling: short/long prefill, eager/compile,
  FP32-TF32/BF16 small model, and low/high-concurrency BF16 serving.
- [ ] Profile the same representative shapes on A30 and RTX 5090, and record the
  effective kernels and clocks. Use the common supported profiler-counter subset
  for direct tables and keep architecture-specific counters in separate panels.
- [ ] Capture PyTorch Profiler operator tables and a bounded trace.
- [ ] Capture Nsight Systems timelines for CPU launch gaps, GPU utilization,
  synchronization, and serving request overlap.
- [ ] Capture Nsight Compute sections only for selected kernels; do not profile
  every kernel in the entire server request.
- [ ] Export compact CSV/JSON counters before removing or externally archiving
  large `.nsys-rep` and `.ncu-rep` files.
- [ ] Classify major kernels as compute-, bandwidth-, latency-, or launch-bound
  using counters and roofline evidence.
- [ ] Connect each measured speed difference to evidence or label the cause
  unresolved. Do not infer kernel causation from wall time alone.

**Gate P0-profile:** At least six representative configurations have compact,
source-linked profiler evidence, and the final report contains two concrete
bottleneck findings plus any unresolved cases.

At this point the P0 project is resume-ready.

---

## Task 10: P1 fused residual + RMSNorm Triton/CUDA kernel

**Files:**

- Create: `src/ai_kernels/rmsnorm/bindings.cpp`
- Create: `src/ai_kernels/rmsnorm/residual_rmsnorm_cuda.cu`
- Create: `src/ai_kernels/rmsnorm/triton_impl.py`
- Create: `src/ai_kernels/rmsnorm/build.py`
- Create: `scripts/aiinfra/integrations/qwen_rmsnorm.py`
- Create: `scripts/aiinfra/benchmark_rmsnorm.py`
- Test: `tests/py/test_aiinfra_rmsnorm.py`

- [ ] Define inference-only semantics: residual addition, RMS calculation,
  learned weight application, supported layouts, and FP32 accumulation policy.
- [ ] Write failing correctness tests against a simple PyTorch FP32 reference for
  FP16 and BF16 input, including model-derived hidden sizes and boundary shapes.
- [ ] Implement the Triton kernel first, then the C++/CUDA implementation with an
  opt-in PyTorch extension build independent of the main HRSC CMake build.
- [ ] Benchmark PyTorch eager, `torch.compile`, Triton, and CUDA using warm-ups,
  CUDA synchronization/events, and at least 30 measured samples per shape.
- [ ] Profile representative shapes for memory traffic, occupancy, registers,
  and achieved bandwidth.
- [ ] Integrate each passing custom implementation into one real Qwen block and
  validate block logits/output against the baseline.
- [ ] Measure model-level prefill/decode impact. Retain neutral or negative
  results and explain launch/fusion/integration overhead.
- [ ] Do not advertise a speedup unless both the kernel-level and model-level
  comparisons pass correctness and matched-timing gates.

**Gate K0:** Both custom implementations pass the locked fidelity tolerance,
have reproducible shape-sweep results, and have a real model integration result.

---

## Task 11: P2 two-GPU NCCL and tensor-parallel case study

**Files:**

- Create: `scripts/cluster/aiinfra/probe_topology.slurm`
- Create: `scripts/cluster/aiinfra/probe_lovelace_topology.sh`
- Create: `scripts/cluster/aiinfra/run_nccl_tests.slurm`
- Create: `scripts/cluster/aiinfra/run_lovelace_nccl_tests.sh`
- Create: `scripts/cluster/aiinfra/run_vllm_tp.slurm`
- Create: `scripts/cluster/aiinfra/run_lovelace_vllm_tp.sh`
- Create: `scripts/aiinfra/parse_nccl.py`
- Create: `configs/aiinfra/distributed/tp1-tp2.json`
- Test: `tests/py/test_aiinfra_nccl_parser.py`

- [ ] Qualify both documented intra-node pairs: 2 x A30 on Lovelace and a
  `--gpus=2` allocation on either `phy-thetis` or `phy-damysus`. Gate each result
  independently on visibility, topology, software support, and an uncontended
  run; defer one target with evidence without blocking P0/P1 or the other target.
- [ ] Record `nvidia-smi topo -m`, GPU UUIDs, PCIe/NVLink facts, NUMA placement,
  NCCL version, and the exact external `nccl-tests` commit.
- [ ] Run all-reduce, all-gather, and reduce-scatter from 1 KiB to 1 GiB with
  warm-ups, correctness checks, and repeated cycles.
- [ ] Parse algorithmic bandwidth, bus bandwidth, latency, and errors into a
  compact summary.
- [ ] Compare the same 7B BF16 serving workload at TP=1 and TP=2 for prompt
  lengths 128/1024/4096 and concurrency 1/8/32 where feasible.
- [ ] Compare A30 and RTX 5090 only at the same tensor-parallel degree, model,
  workload, environment contract, and common feasible load. Treat interconnect
  type and topology as measured variables; do not assume NVLink or PCIe peer
  access from the GPU model name.
- [ ] Report scaling efficiency, memory per GPU, communication time share, and
  the break-even workload if one exists.
- [ ] Treat TP=2 slowdown as a valid result; never describe two GPUs as
  large-scale distributed infrastructure.

**Gate D0:** Every TP comparison uses the same model revision, prompts, output
length, load, and SLO. Communication topology evidence accompanies the result.

---

## Task 12: Regression gates, lifecycle manifests, and portfolio presentation

**Files:**

- Create: `scripts/aiinfra/regression_gate.py`
- Create: `docs/aiinfra/ARCHITECTURE.md`
- Create: `docs/aiinfra/REPRODUCE.md`
- Create: `docs/aiinfra/EVIDENCE.md`
- Create: `docs/aiinfra/RESULTS.md`
- Create: root `README.md`
- Modify: `docs/INDEX.md`
- Modify: `scripts/harness/experiment_manifest.py` to accept an `aiinfra`
  ownership value additively, without rewriting Report 2 manifests
- Test: `tests/py/test_experiment_manifests.py`
- Test: `tests/py/test_aiinfra_documentation.py`

- [ ] Promote the first completed P0 matrix to a canonical baseline with
  environment matching rules.
- [ ] Make correctness/completion regressions hard failures. Make performance
  regression initially advisory; promote a threshold only after baseline
  variance is measured and documented.
- [ ] Create lifecycle manifests for offline, serving, profiling, kernel, and
  distributed packets as they become complete.
- [ ] Keep generated runs and raw traces ignored. Force-add only reviewed
  manifests, compact summaries, small figures, and necessary provenance; never
  force-add caches or model assets.
- [ ] Create a one-command small smoke reproduction and a separate explicit
  command for the expensive matrix.
- [ ] Add an architecture diagram, experiment matrix, hardware table, headline
  findings, negative results, limitations, and evidence links to the README.
- [ ] Present HRSC as an additional numerically sensitive accelerator workload,
  not as the AI model.
- [ ] Generate resume bullets only from stored results; no placeholder speedup
  or throughput number may survive in the final README.
- [ ] Run the complete available Python and CPU C++ suites. Run GPU integration
  suites where hardware exists and record explicit skips elsewhere.

**Gate R0:** A new reader can reproduce the small smoke, trace every headline
number to a manifest and summary, understand unsupported/negative results, and
see that existing HRSC behavior remains unchanged.

## Verification Commands

The exact AI environment executable is recorded during Task 1. These are the
repository-level command shapes the implementation must preserve:

```powershell
# Existing non-regression suite
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py -q
cmake --build build-double --target unit_tests
.\build-double\unit_tests.exe -r compact

# AI-infra CPU/fake-backend contract tests; must not require torch/vLLM/GPU
python -m pytest tests/py/test_aiinfra_config.py \
  tests/py/test_aiinfra_result_schema.py \
  tests/py/test_aiinfra_harness_contract.py -q

# Environment-specific smoke after Task 4
python scripts/run_matrix.py configs/aiinfra/smoke/matrix.json

# Expensive packets are explicit, never part of the default test suite
python scripts/run_matrix.py configs/aiinfra/offline/matrix-small.json
python scripts/aiinfra/serve.py configs/aiinfra/serving/matrix-qwen7b.json
```

School-resource probes and job shapes are versioned scripts in the final
implementation. The initial read-only checks should be equivalent to:

```bash
# Athena is the control plane; do not benchmark on the login node.
ssh csc-athena
sinfo --clusters=CSC --partition=csc-mphil,csc-mphil-gpu --Node --long
scontrol --clusters=CSC show node phy-cerberus5
scontrol --clusters=CSC show node phy-thetis
scontrol --clusters=CSC show node phy-damysus

# CPU reference allocation, explicitly on the user's established Cerberus node.
srun --clusters=CSC --partition=csc-mphil --nodelist=phy-cerberus5 \
  --time=00:10:00 --cpus-per-task=1 --mem=2G hostname

# Blackwell allocation. The saved probe also records SLURM_JOB_* and
# CUDA_VISIBLE_DEVICES before it starts any timed work.
srun --clusters=CSC --partition=csc-mphil-gpu --gpus=1 \
  --time=00:10:00 --cpus-per-task=2 --mem=8G \
  bash -lc 'hostname; nvidia-smi -L; nvidia-smi topo -m'

# Lovelace is direct-login/shared. Run the versioned probe first; long work is
# nice -19, device-pinned, node-local, and admitted only after an idle check.
ssh csc-lovelace 'hostname; nvidia-smi -L; nvidia-smi topo -m'
```

## Six-Week Schedule

| Week | Required outcome | Tasks |
|---|---|---|
| 1 | Environment lock and workload-agnostic harness contract | 1-3 |
| 2 | PyTorch reference plus compile/vLLM bridge | 4-5 |
| 3 | Fidelity calibration and offline matrix | 6-7 |
| 4 | Online serving matrix | 8 |
| 5 | Profiler evidence and P0 stabilization | 9 |
| 6 | Regression baseline, docs, and final P0 evidence audit | 12 |
| Optional 7 | Fused Triton/CUDA kernel and model integration | 10 |
| Optional 8 | NCCL/tensor-parallel case study, then refresh final evidence | 11, 12 |

Task 12 is intentionally executable immediately after Task 9 and can be rerun
to register later P1/P2 evidence. Do not trade P0 correctness, provenance, or
profiling quality for an unfinished custom kernel.

## Paper-To-Experiment Map

| Paper/system | What this project adopts | Owning task |
|---|---|---|
| Mixed Precision Training | higher-precision accumulation and fidelity gates | 6, 10 |
| FP8 Formats for Deep Learning | capability-based FP8 scope, not label-based claims | future/P1 |
| FlashAttention | IO-aware profiling and effective attention-backend recording | 5, 9 |
| SmoothQuant | named quantization method and accuracy-memory-throughput trade-off | 8/P1 |
| vLLM/PagedAttention | production-shaped serving, KV-cache and concurrency study | 8 |
| MLPerf Inference | accuracy-gated performance, workload scenarios, reproducible load | 7-8 |
| Megatron-LM / ZeRO | compute-communication and memory reasoning for TP | 11 |

## Risk Register

| Risk | Effect | Mitigation |
|---|---|---|
| vLLM/PyTorch/CUDA incompatibility on Blackwell | blocks serving | lock environment first; keep HF eager P0 fallback; record unsupported state |
| one container cannot support both A30 and RTX 5090 | confounds hardware comparison | test one pinned Apptainer digest first; otherwise lock two explicit environments and narrow claims to matched supported paths |
| 7B model or 4K prompt OOM | incomplete matrix | preflight memory; retain OOM row; lower concurrency, not model revision silently |
| model/data download or licence issue | irreproducible workload | explicit preparation, pinned revision, reviewed fallback decision |
| backend exposes only top-k logprobs | incomplete full-logit comparison | name approximate KL; retain full-logit metrics on HF paths |
| performance variance from thermals/background load or non-exclusive nodes | unstable claims | idle/co-tenant admission gate, warm-up, repeats, utilization and clock capture, medians/IQR/CI; demote contaminated rows |
| timed run reads weights or output over network storage | misleading I/O/latency result | stage to node-local `/local/data`, hash-check first, and measure staging/load separately |
| CUDA guide and cluster sample expose different toolkit paths | accidental stack drift | probe compiler/runtime paths per host and store the resolved path and version in each environment lock |
| `torch.compile` recompilation contaminates timing | false speedup/slowdown | separate compile time; record graph breaks; time stable phase only |
| profiler overhead changes behavior | misleading performance | profiler results explain bottlenecks; unprofiled matched runs own headline timing |
| documented two-GPU node is busy or the pair is not allocated together | one P2 arm blocked | request `--gpus=2`, validate visibility/topology inside the allocation, and defer that arm with evidence |
| custom kernel is faster alone but neutral end-to-end | weak headline | report model-level result honestly; bottleneck analysis remains useful |
| AI changes break HRSC harness compatibility | damages original project | additive contracts, fake-backend tests, full existing regression suite |

## Final Acceptance Checklist

- [ ] P0 offline, serving, and profiler gates pass.
- [ ] Every result is success, unsupported, or failed with a structured reason.
- [ ] Model, tokenizer, data, code, environment, and hardware provenance are
  available for every headline row.
- [ ] The resource registry distinguishes Athena control, Apollo utility,
  Cerberus CPU reference, Lovelace 2 x A30 direct execution, and Thetis/Damysus
  2 x RTX 5090 Slurm execution; runtime records confirm the effective target.
- [ ] Required A30/RTX 5090 claims use the common feasible workload intersection;
  architecture-specific capacity results and optional local RTX 5070 evidence
  are clearly separated.
- [ ] Fidelity and performance are reported together; no speed-only claim.
- [ ] Tail latency, throughput, and peak memory exist for serving results.
- [ ] Profiler evidence explains at least two bottlenecks and preserves
  unresolved cases.
- [ ] The small smoke is reproducible with one documented command.
- [ ] No model weights, caches, raw large traces, or transient grids are added to
  Git.
- [ ] Existing output formats and solver defaults are unchanged.
- [ ] Existing Python and CPU C++ suites pass; GPU availability/skips are
  recorded.
- [ ] Headline runs use node-local storage and pass the shared-resource admission
  gate; staging, download, cold start, and contaminated runs are not mixed into
  steady-state inference timing.
- [ ] Root README and `docs/aiinfra/EVIDENCE.md` link every headline to a compact
  machine-readable authority.
- [ ] Resume bullets contain only measured numbers from canonical summaries.
