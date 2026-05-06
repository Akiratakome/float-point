# Week 4 — A4-part 2 落地设计 (`s_req(N=200)` 头版 conclusion table)

**Date:** 2026-04-26
**Branch:** `week4-implementation`
**Plan reference:** [docs/week4/week4-plan.md §A4.4 / §A4.5](week4-plan.md)
**Trigger:** 800² double reference 已落入 `experiments/week4/reference/`（HLLC + Rusanov），200² deterministic IEEE-double 已落入 `experiments/week4/deterministic/`。`s_req` 主路径不再阻塞。

---

## 1. Scope

**单一目标**：把 `s_req(N=200)` 行写进头版 conclusion table，`pareto_lw_config3_200.png` 与 `lw_config3_200.md` 同时产出，发邮件。

**μ_sample 数据源决策**：用 `experiments/week4/deterministic/{hllc,rusanov}_200.bin`（单次 IEEE 跑），不用 MCA 30 样本均值。理由：

- `E_trunc` 应反映"该 solver 在该网格上的 IEEE-double 行为"，而非附加 MCA 噪声后的均值。
- MCA 均值与 deterministic 之差 ≈ MCA 单 sample std/√30 ≈ 1e-12，远小于 `μ_trunc` ≈ 1e-3，二者数值上不可分；deterministic 概念上更干净并与"reference 也是 deterministic IEEE"对称。
- 脚本仍支持两种模式（CLI 互斥），本轮命令行用 deterministic。

**`U_ref` 800→200 处理**：4×4 **block-average**，作用在 conserved variables。block-avg 后再 `cons_to_prim`。不用 bilinear / nearest——block-avg 是 finite-volume 守恒平均，与 cell-average 解释一致。

**明确不在范围内**（推到后续 round）：

- N=400 / N=800 的 `s_req` 行（需要 400² MCA + ≥1600² reference 或精确解）
- B1（PrecisionConfig + TimeReal=double + Kahan + explicit instantiation）
- `losos_metric.py` 加 `--reference-bin` 接口以计算 `s_accuracy`
- HLLC float / Rusanov float 行（依赖 B1 + C1）
- k_grad 数据驱动重校准、OpenMP 内层 vector hoist、toro2 ρ_floor、progress 常数命名

---

## 2. 组件清单（5 个新文件 + 1 个 commit-only 收尾）

| # | 路径 | 职责 | 依赖 |
|---|---|---|---|
| 1 | `scripts/_tradeoff_thresholds.py` | 集中 4 个常量：`REGIME_MARGIN_OVER_PROVISIONED=2.0` / `REGIME_MARGIN_WELL_MATCHED=1.0` / `BITWISE_DOUBLE_S_RELIABILITY=15` / `BITWISE_FLOAT_S_RELIABILITY=7`。**不**含 `s_req` 阈值（动态量，不是常量） | 无 |
| 2 | `scripts/s_req_metric.py` | candidate 200².bin + reference 800².bin → block-avg → `E_trunc(N)` → `s_req(N)`。输出 CSV `(solver, variable, N, U_ref_L1, U_ref_inf, n_cells, floor_L1, mu_trunc_L1, E_trunc, s_req)` | `io_helper.read_binary`, `cons_to_prim` |
| 3 | `tests/py/test_s_req_scaling.py` | 6 用例：Δx 收敛率、完美匹配、floor 触发、block-avg 守恒、不可整除 grid、dtype 一致性 | `s_req_metric` |
| 4 | `scripts/tradeoff_summary_table.py` | join 三份 CSV → 8 列头版 table → `docs/week4/tradeoff_summary_tables/lw_config3_200.md` | `s_req_metric`, `snr_metric`, `losos_metric`, `_tradeoff_thresholds` |
| 5 | `scripts/pareto_plot.py` | x=`log10(μ_trunc_L1)`, y=`s_worst_q05`，每 (solver, p) 一点 + `s_req(N)` 水平虚线 | 同上 |

**头版 table 数据耦合细节**：`s_req_metric.py` 顺带产出 `mu_trunc_L1` 列；`tradeoff_summary_table.py` 取这一份覆盖 `snr_scalars.csv` 的同名列（消除"自指 mu_trunc 与 reference-anchored s_req 自相矛盾"的问题）。`snr_scalars.csv` 仅贡献 `σ_FP_*` 列。

---

## 3. 数据流 & block-average

```
[experiments/week4/deterministic/{hllc,rusanov}_200.bin]   ── candidate (μ)
                                                            │
[experiments/week4/reference/{hllc,rusanov}_800.bin]      ─┼── reference (U_ref)
                                                            ▼
                                            s_req_metric.py
                                            ├─ block-avg 800²→200² (4×4 平均, conservation-preserving)
                                            ├─ cons → prim (rho, u, v, p)
                                            ├─ E_trunc(N) per variable
                                            ├─ floor_L1 = sqrt(eps)·||U_ref||_∞·N_cells
                                            └─ s_req = -log10(E_trunc) + 1
                                                            │
                ┌───────────────────────────────────────────┴───┐
                ▼                                                ▼
   experiments/week4/metrics/                  experiments/week4/figures/a4_pareto/
        s_req_lw_config3_200.csv                    pareto_lw_config3_200.png
                │                                                ▲
                │   ┌── snr_scalars.csv (existing) ──────────────┤
                │   │   (only σ_FP_L1 columns used; mu_trunc 被覆盖)
                │   ├── losos_scalars.csv (run once if missing)
                ▼   ▼                                             │
     tradeoff_summary_table.py ─────────────────────────────────┘
                │
                ▼
  docs/week4/tradeoff_summary_tables/lw_config3_200.md
```

### Block-average 实现（伪代码）

```python
def block_average_4x_to_coarse(fine: np.ndarray) -> np.ndarray:
    """fine shape (800, 800, nvars) → coarse (200, 200, nvars), conservation-preserving."""
    ny_f, nx_f, nv = fine.shape
    if ny_f % 4 != 0 or nx_f % 4 != 0:
        raise ValueError(f"Block-average requires factor-4 grid; got ({ny_f}, {nx_f})")
    return fine.reshape(ny_f//4, 4, nx_f//4, 4, nv).mean(axis=(1, 3))
```

- 作用在 conserved variables；block-avg 后再 `cons_to_prim`。
- 比例因子整数除法精确整除——CLI 入口处 assert，不做 magic 适配。

### `E_trunc` & floor（plan §A4.2.2 严格执行）

```python
def compute_e_trunc(mu_coarse, u_ref_coarse, eps_real):
    n_cells = u_ref_coarse.shape[0] * u_ref_coarse.shape[1]
    out = {}
    for k, name in enumerate(("rho", "u", "v", "p")):
        diff_l1 = np.abs(mu_coarse[..., k] - u_ref_coarse[..., k]).sum()
        ref_l1  = np.abs(u_ref_coarse[..., k]).sum()
        ref_inf = np.abs(u_ref_coarse[..., k]).max()
        floor_l1 = np.sqrt(eps_real) * ref_inf * n_cells   # plan §A4.2.2
        denom = max(ref_l1, floor_l1)
        out[name] = (diff_l1, diff_l1 / denom, ref_l1, ref_inf, n_cells, floor_l1)
    return out

s_req = -np.log10(E_trunc) + 1.0
```

**Floor rationale**（写进 s_req_metric.py top-of-file comment）：
- `1e-14` 是 magic — 对 float32 太松，对 long double 太紧。
- `sqrt(eps)` 是 IEEE 标准下"L2-style noise floor"的精度感知量纲（Higham 2002 §3）。
- `× ||U_ref||_∞` 与场幅值同量纲；`× N_cells` 与 L1 求和的 cell 数对齐。
- 与 SNR / LoSoS 模块共用同一约定，避免脚本间 floor 不一致。

### `s_req` 数值兜底（NaN/Inf 处理）

`E_trunc=0`（完美匹配）会让 `-log10(0)+1 = +inf`，`np.log10` 还会发 RuntimeWarning。统一处理：

```python
from losos_metric import SIG_DIGITS_CEILING   # 复用 commit 8883c25 既有常量
with np.errstate(divide="ignore"):
    s_req = -np.log10(e_trunc) + 1.0
s_req = np.where(np.isfinite(s_req), s_req, SIG_DIGITS_CEILING)
```

**为何不写 `nan_to_num(posinf=15.0)`**：`15.0` 数值上恰好等于 `BITWISE_DOUBLE_S_RELIABILITY` 但语义完全不同（一个是"可复现位数工程阈值"，一个是"log 截断 ceiling"）。用同一字面值会让未来读者误以为它们关联——直接从 `losos_metric` 复用 `SIG_DIGITS_CEILING`，与既有 inf-clamp 约定一致，零新魔术数。

### gamma 传递

`cons_to_prim(coarse_cons, args.gamma)` 显式传入，函数内不出现 `1.4` 字面值。CLI `--gamma` 默认 `1.4`，但代码路径上 gamma 是参数，不是常量——为未来 real-gas EOS / 多 gamma 测预留。

### CLI

```bash
python scripts/s_req_metric.py \
    --solver hllc \
    --candidate-bin experiments/week4/deterministic/hllc_200.bin \
    --reference-bin experiments/week4/reference/hllc_800.bin \
    --gamma 1.4 \
    --out experiments/week4/metrics/s_req_lw_config3_200_hllc.csv
```

`--candidate-bin` 与 `--candidate-samples-root` **互斥**；本轮用前者。N=200 隐式来自 candidate header（不在 CLI 显式传，避免人工设错）。

---

## 4. 验收 & 测试

### 单测 `tests/py/test_s_req_scaling.py`（6 用例）

| 用例 | 构造 | 断言 |
|---|---|---|
| 1. **Δx 收敛率** | 合成 `mu_N(x) = U_ref(x) + C/N` 在 N ∈ {100, 200, 400} | `s_req(2N) − s_req(N) ≈ log10(2)` 容差 1e-3 |
| 2. **完美匹配 → s_req 大** | mu == U_ref（`E_trunc=0`） | `s_req` 命中 SIG_DIGITS_CEILING（与 losos_metric inf clamp 约定一致） |
| 3. **floor 触发** | U_ref 全零，mu = `√eps` 量级噪声 | `E_trunc` 不 blow up；`s_req` 有限非 nan |
| 4. **block-average 守恒** | 任意 fine field | `coarse.sum() * 16 == fine.sum()` 严格相等（float64） |
| 5. **不可整除 grid** | 7-pixel fine | raise `ValueError` |
| 6. **dtype 一致性** | float32 candidate, float64 reference | cast → float64，结果有限 |

### 端到端 smoke（真实数据）

```bash
# s_req per solver
python scripts/s_req_metric.py --solver hllc \
    --candidate-bin experiments/week4/deterministic/hllc_200.bin \
    --reference-bin experiments/week4/reference/hllc_800.bin \
    --out experiments/week4/metrics/s_req_lw_config3_200_hllc.csv
python scripts/s_req_metric.py --solver rusanov \
    --candidate-bin experiments/week4/deterministic/rusanov_200.bin \
    --reference-bin experiments/week4/reference/rusanov_800.bin \
    --out experiments/week4/metrics/s_req_lw_config3_200_rusanov.csv
# concat（注意 header 处理；推荐 pandas concat 后 dedup header 而不是 cat）

# losos_metric 落 CSV（如未落）
python scripts/losos_metric.py \
    --root experiments/week4/2d_vfc_cluster --expected-n 30 \
    --out experiments/week4/metrics/losos_lw_config3_200.csv

# 头版 table
python scripts/tradeoff_summary_table.py \
    --snr-csv experiments/week4/figures/a4_snr/snr_scalars.csv \
    --losos-csv experiments/week4/metrics/losos_lw_config3_200.csv \
    --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
    --N 200 \
    --out docs/week4/tradeoff_summary_tables/lw_config3_200.md

# Pareto
python scripts/pareto_plot.py \
    --losos-csv experiments/week4/metrics/losos_lw_config3_200.csv \
    --snr-csv experiments/week4/figures/a4_snr/snr_scalars.csv \
    --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
    --out experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png
```

### 验收指标

1. 5 个新文件齐全且合规（无 magic、命名规范、注释解释 why）
2. `pytest tests/py/test_s_req_scaling.py -v` 6/6 绿
3. s_req CSV：2 solver × 4 var = 8 行；`s_req(rho)` 量级与上周邮件预测 `~3.5` 一致
4. `lw_config3_200.md` 头版 table：本轮**只 2 行**（HLLC double / Rusanov double）；HLLC float / Rusanov float 行**不**写"估算值"，留待 C1 后补；regime 列分类正确
5. Pareto 图含 `s_req(N)` 水平虚线、2 点全标注
6. 头版 table 的 `s_worst_q05` 列暂等于 `s_reliability_q05`，列尾 footnote 明示上界关系
7. `git status` 干净；commit 拆分按 §5 序列

### `s_worst_q05` footnote（精确文本，写进 `tradeoff_summary_table.py` template）

> `s_worst_q05` 暂等于 `s_reliability_q05`；`s_accuracy` 接口扩展（`losos_metric.py --reference-bin`）后将更新。**注意当前列值是 s_worst 的上界**：`s_worst = min(s_reliability, s_accuracy) ≤ s_reliability`，accuracy 落地后真值只会更低或持平，不会更高。

### 关键风险

- **风险 1**（`losos_metric.py` 当前接口未知）：进入实施先查 CLI；若不支持 `--reference-bin`，按上面 footnote 处理，本轮不扩展接口。
- **风险 2**（float 行无数据）：HLLC float / Rusanov float 行不写。本轮头版 table 2 行而非 4 行；结论仍能讲清"double 在 200² over-provisioned"。

---

## 5. 实施顺序、commit 拆分、时长

### 顺序

```
0. 探勘 losos_metric.py CLI（5 分钟）
   ↓
1. _tradeoff_thresholds.py（10 分钟）
   ↓
2. s_req_metric.py + 跑两个 solver 出 CSV（45 分钟）
   ↓
3. test_s_req_scaling.py（30 分钟）
   ↓
4. tradeoff_summary_table.py → lw_config3_200.md（45 分钟）
   ↓
5. pareto_plot.py → png（30 分钟）
   ↓
6. 邮件草稿更新（20 分钟）
```

### Commit 拆分（**8 个**，code-causality first；docs 收尾）

| # | commit | 内容 |
|---|---|---|
| 1 | `feat(progress,openmp): wall-clock progress + OMP sweep pragmas; analyzer fail-fast on partial samples` | `CMakeLists.txt` / `src/euler/euler_solver.hpp` / `src/main.cpp` / `scripts/verificarlo_analysis_2d.py` |
| 2 | `feat(scripts): _tradeoff_thresholds — centralize regime + bitwise constants` | `scripts/_tradeoff_thresholds.py` |
| 3 | `feat(scripts): s_req_metric — truncation-anchored required sig digits via 800² block-avg reference` | `scripts/s_req_metric.py` |
| 4 | `test(scripts): s_req scaling + floor + block-avg conservation invariants` | `tests/py/test_s_req_scaling.py` |
| 5 | `feat(scripts): tradeoff_summary_table — headline conclusion table generator` | `scripts/tradeoff_summary_table.py` |
| 6 | `feat(scripts): pareto_plot — sigma_FP × s_worst with s_req(N) target band` | `scripts/pareto_plot.py` |
| 7 | `chore(a4): s_req + losos CSVs + headline table + pareto plot for LW Config 3 N=200` | `experiments/week4/metrics/*.csv` + `docs/week4/tradeoff_summary_tables/lw_config3_200.md` + `experiments/week4/figures/a4_pareto/pareto_lw_config3_200.png`。前缀 `chore(a4)` 沿用 `dbaf6fd` 既定约定（generated artifacts），Commitlint 兼容 |
| 8 | `docs(week4): 800² reference workflow + a3 production log + email + noise_floor calibration` | `docs/week4/800_reference_workflow.md` / `docs/week4/2d_vfc_feasibility.md`（diff 部分）/ `docs/week4/2d_vfc_report.md` / `docs/week4/noise_floor_calibration.md` / `docs/week4/email_supervisor_2026-04-23_week4_progress.md` |

**Causality 论点**：commit 1 是真正"enabled 800² to land"的代码改动；commit 8 是"what we did + analysis log"，自然在分析脚本之后。两端各自一个 commit，1–6 中段是新增脚本与产出，git log 时序与因果正序一致。

### 总时长

`5 + 10 + 45 + 30 + 45 + 30 + 20 = 185 分钟 ≈ 3 小时`，加 commit / 写 message / 全量复跑 ~30 分钟 buffer = **~3.5 小时**。

---

## 6. 邮件落地

更新 `docs/week4/email_supervisor_2026-04-23_week4_progress.md` 或新建 `docs/week4/email_supervisor_2026-04-26_s_req_landed.md`：

- attachment：`lw_config3_200.md`（贴文本）+ `pareto_lw_config3_200.png`
- §3.2 把"预计 s_req ≈ 3.5"换成实测值
- §4 limitations：`μ_trunc 自指` 这条改为"已替换为 800² block-avg reference"；`k_grad=1.0` 与 `toro2 vacuum` 维持 limitation 状态，明确推到下一轮

---

## 7. 推迟清单（写入备查）

- `losos_metric.py --reference-bin` 加 `s_accuracy` → 下一轮（与 B1 同期）
- HLLC float / Rusanov float 行 → C1 完成后
- N=400 / N=800 的 s_req 行 → 下周（需要 400² MCA + 1600² reference 或精确解）
- B1（PrecisionConfig + TimeReal + Kahan）→ 下一轮
- k_grad 数据驱动校准 + 重画 6 张 noise_floor 图 → 再下一轮
- toro2 ρ_floor → 下下周
- OpenMP 内层 `std::vector` 提升 → C1 期间附带
