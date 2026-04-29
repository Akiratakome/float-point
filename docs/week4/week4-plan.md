# Week 4 代码实施计划

**Date:** 2026-04-22（Rewrite v5：四大技术修正 — SLURM array 并发、truncation-anchored s_req(N)、SSIM 相移分离、flip_indices BC 解耦）
**Source branch:** `week3-implementation`
**Target branch:** `week4-implementation`（已存在，当前 HEAD）
**Deadline awareness:** Report 1 due 2026-05-29 (Week 10)；当前实际处于 calendar Week 5 (04/20–04/26)，但 overall.md 标签为 Week 4 的两项（PrecisionConfig、periodic/reflective BC）尚未落地，因此此文档代号 Week 4。

**本次 rewrite 的定位：纯执行导向（Pure-execution plan）**

- 不再把本计划视为 Report 1 的素材预研；所有 `.md` 产出统一降级为 **Raw Data Log / Experiment Summary**（表格 + 图 + bullets），Report 1 章节素材由 Week 8-9 另写，不与本周工作混淆
- A2 采用 **两阶段交付**：Stage 1 用 `--mode visible` 在 0.5 天内向导师发出首张 "x-mark" 图；Stage 2 用 MCA p=53 overnight 跑统计 noise floor，后续补发
- A3 **直接 200²×N=30 on SLURM array（并发执行）**：v4 基于"12h 跑不完"的错误前提引入的 PILOT / G1/G2 / 灰色带全部废弃；`sbatch --array=1-30` 是 30 个独立 task **并发**，`--time=12:00:00` 仅限单 task；整批 wall-clock ≈ `t_{200²}`
- A4 头版给 **结论 table + 动态 `s_req(N)`**：`s_req(N) = -log10(||E_trunc(N)||) + 1` 基于物理截断误差，取代 publication≥4 / convergence≥6 的静态阈值；直接回答导师 "how many significant figures we need" = "恰好匹配网格截断"
- C1.2.5 **SSIM 单 scalar**（lean）取代 axis-aligned W1：`skimage.metrics.structural_similarity` 三行代码作 L1 的定性补充；完整三因子分解（luminance/contrast/structure）与相移拓扑分离延后到 Report 2 Future Work
- B2 `apply_reflective_bc` **接口解耦**：`std::array<int, NFlips> flip_indices_x/y` 取代 `int normal_x/y_index`，Euler 传 `{RHOU}` / MHD 传 `{RHOU, BX}`，BC 对物理 agnostic
- Phase B / C 其余内容（PrecisionConfig + BC enum + float 全回归）维持 Round 3 既定内容，不做叙述改写

时间判断：充裕。Report 1 截止 5/29，本计划预计 05/10 完成，留 >2 周 buffer。

---

## 0. 计划导航

| Phase | 子项 | 依赖 | 预估工作日 | 产出（Raw Data Log 级别） |
|---|---|---|---|---|
| A1 | Rusanov 设为默认 solver（cfg 层） | 无 | 0.5 | cfg 默认值改动 + experiment summary |
| A2-S1 | **Stage 1** `--mode visible` 快速 x-mark 图（04/22, 0.5 天） | 现有 sample + Python | 0.5 | 1 张 supervisor-facing 图 + 邮件草稿 |
| A2-S2 | **Stage 2** MCA p=53 noise-floor 统计（overnight batch） | Verificarlo（WSL+Docker / CSC） | 1.5 | `noise_floor_run.sh`, `plot_divergence_marker.py`（3-mode），noise_floor npz × 8, 图 × 12 |
| A3 | 2D Verificarlo on LW Config 3（/dev/urandom seed + **SLURM array 并发 200²×N=30**，per-task seed CSV 无 flock） | 无（outflow BC 即可） | 3 | LW3 IC/cfg，`lw_tests.hpp`，SLURM 脚本，per-task seeds/ 目录，heatmap |
| A4 | SNR / LoSoS（field-first 算子顺序，**truncation-anchored `s_req(N)`**） + Pareto + **头版 conclusion table** | 依赖 A3 数据 | 2.5 | `snr_metric.py`（带算子顺序回归测试）, `losos_metric.py`, `s_req_metric.py`, `pareto_plot.py`, `tradeoff_analysis.md`（首页为 8 列结论表，regime 列基于 `s_worst − s_req(N)`） |
| B1 | `cmake/PrecisionConfig.cmake` + explicit instantiation + 分离编译 | 无 | 1 | cmake 模块、`euler_solver.cpp`、分离库 |
| B2 | `apply_periodic_bc` / `apply_reflective_bc` | 无 | 1 | `src/core/boundary.hpp` 扩展 |
| B3 | `BoundaryType` enum + cfg `bc_x`/`bc_y` + solver 集成 | B2 | 1 | `EulerSolver::step()` 改动，cfg 模板 |
| B4 | `test_boundary.cpp` 扩展（periodic/reflective 单测） | B2 | 0.5 | Catch2 新增 case |
| C1 | float 全回归：6×1D Toro + 2D LW3 + phase-error 定性补充 (shock-track + **SSIM 单 scalar**) | B1 | 4 | float build + L1/L2/Linf + SSIM scalar + Δx_shock 表 + 2D reference |
| C2 | Verificarlo 真·float 编译 p24 | B1 | 1.5 | `scripts/verificarlo/verificarlo_run.sh` 改造 + MCA 对比 |

**总工作量估计**: ~17 工作日（2026-04-22 → 2026-05-10）。SLURM 作业多为 overnight/weekend 运行，不占用主线工时。A2-S1 的 0.5 天快速交付确保在 24h 内回应导师；A2-S2 的统计 batch 作为 overnight 背景任务，不阻塞 A3 启动。Phase B 落地后 Week 5 的 Liska-Wendroff/Kelvin-Helmholtz IC 即可动工。Report 1 截止 2026-05-29，仍留 2.5 周缓冲。

**交付优先级铁律**（新）：supervisor-facing 图 > 数据完备性 > 报告美化。若任一 stage 面临延期，优先砍 A2-S2 statistical update（Stage 1 已覆盖最小必要交付），绝不砍 A3 / A4。

---

## 1. Scope 与参考

### 1.1 范围内（本计划覆盖）

- overall.md Week 4 原计划（line 266–275）剩余 2 项
- 导师 2026-04-17 邮件明列 3 项（Rusanov 坚持、plot "x" 发散标记、2D Verificarlo），外加导师提出的开放问题（accuracy-vs-FP-robustness trade-off、需要多少显著位）
- 导师 2026-04-17 邮件隐含要求：用现有 Rusanov（而非 FORCE 或 SLIC）作为与 HLLC 对比的 underlying solver

### 1.2 范围外（不在本计划内，留给后续 week）

- **Report 1 章节撰写 / 文献综述 / 数学推导（overall.md Week 8-9 工作）**——明确**不**在 Week 4 内；本计划全部 `.md` 均为 **Raw Data Log / Experiment Summary** 格式（表格 + 图 + bullets），不写叙事段落，不为 Report 1 的章节结构做预研
- FMA 写入 `cmake/CompilerFlags.cmake`（overall.md 标为 secondary，Week 17）
- vfc_precexp 逐函数最低精度扫描（overall.md Week 17 Tier 3）
- unstable-branches `--coverage` 工作流完善（Week 3 脚本级已做，主要价值在 Week 17 paper）
- GPU（Week 5 开始）
- MHD（Week 12 开始）

### 1.3 关键参考

- [docs/requirement/overall.md](../requirement/overall.md) — 整体时间表与架构
- [docs/requirement/coding guidance.md](../requirement/coding%20guidance.md) — 编码规范（无魔术数字、配置文件驱动、命名、注释解释 why）
- [docs/week4/week3_to_week4_bridge.md](week3_to_week4_bridge.md) — Week 3 已完成状态 + 接口清单
- 导师 2026-04-17 邮件（见 [supervisor.md](../../supervisor.md)）

---

## 2. 优先级 rationale

**为何 Phase A 先于 Phase B**：

- 用户指令明确"优先实现导师要求内容中和 week4 关联性不大的内容"
- Phase A 全部 4 项都**不依赖** `Real` typedef 切换或新 BC 代码，可在当前 `week3-implementation` 代码基础上立即展开
- Phase A 的产出（plot "x" 标记 / 2D MCA 数据 / 定量 metric）是直接回应 2026-04-17 邮件的内容，越早越好
- Phase B 是纯基础设施，落地后立刻解锁 Phase C（float 回归、真·float Verificarlo）和 Week 5 的 2D tests（需 periodic for KH）

**为何 Phase C 最后**：

- 必须 Phase B 的 float build 已经跑通才能做
- 产出是 Raw Data Log：float vs double 的定量 L1/L2/Linf 比较 + phase-error 分解结果，存档于 `experiments/week4/` 供未来 Report 1 validation 章节自取，**本 Week 不负责章节撰写**

---

## 3. Phase A — 非 Week-4 导师要求（04/22 → 04/30）

### A1. Rusanov 设为默认 solver（0.5 天，04/22）

**目的**：导师 2026-04-17 邮件明确 "stay with Rusanov as the underlying solver for now"。当前 cfg 默认值是 `solver=hllc`，Rusanov 只作为对比。把默认切到 Rusanov，HLLC 仍可显式指定用于对比。

**文件改动**：

- [src/main.cpp](../../src/main.cpp) — `parse_flux()` 当前默认 `hllc`（第 65 行）。改为：
  ```cpp
  std::string s = cfg.get_string("solver", "rusanov");  // default per 2026-04-17 supervisor email
  ```
- [tests/cases/toro_1d/*.cfg](../../tests/cases/toro_1d/) — 保持现状（HLLC cfg 和 Rusanov cfg 共存，明确写 `solver=hllc` 或 `solver=rusanov`），不依赖 default。
- **不改** 任何 `.cfg` 文件，避免 regression test 挨批量改动；默认值变化只影响**未显式指定 solver** 的新 cfg 或命令行直接运行。

**注释**：在 `parse_flux` 上方加 2 行 why：
```cpp
// Default chosen to match supervisor recommendation (email 2026-04-17):
// Rusanov is the designated baseline vs HLLC for FP-sensitivity comparison.
```

**验收**：
- `build/unit_tests.exe` 全绿（107 cases / 3403 assertions）
- `build/hrsc.exe tests/cases/toro_1d/sod.cfg` 输出与之前**完全一致**（cfg 写了 `solver=hllc`，默认变化不起作用）

**Commit**: `feat(solver): default to Rusanov per 2026-04-17 supervisor email`

---

### A2. plot 发散标记工具（两阶段交付：Stage 1 快速 + Stage 2 统计）（2 天，04/22–04/24）

**目的**：导师 2026-04-16 邮件附 `stationary_contact_hllc_vs_rusanov.png` 为参考，要求：**比较两方法 rho（或类似量）时，在两条数据开始不同的点打 "x" 标记**。目前 `scripts/run_comparison.py` 绘图但无此标记。

#### A2.0 两阶段交付策略（5-point rewrite 新增）

**动机**：对导师邮件请求的**响应优先级高于统计完备性**。导师的核心请求是"能看到两条 line 在哪里分开"；第一版图 `--mode visible` 即可满足，不需要等 MCA 统计跑完。把交付拆成两阶段，避免"1.5 天后才发第一张图"的拖延。

| Stage | 触发时间 | 工作量 | 所需 infra | 交付内容 |
|---|---|---|---|---|
| **S1 — Visible x-mark**（supervisor-facing） | 04/22 当天 ≤0.5 天 | 仅 Python（matplotlib），复用 Week 3 已有 HLLC + Rusanov `.txt` 输出 | 本地 Python（无需 Verificarlo） | 1 张 2×3 panel（Sod / stationary-contact × {ρ, p}）+ 红 "x" 标注在 `\|a-b\| > rel_tol·max(\|a\|,\|b\|)` 处；`rel_tol = 1e-3` 是 visible 模式明确的 "人眼可见相对差异" 阈值，写在图注里 |
| **S2 — MCA p=53 noise-floor**（statistical） | 04/22 晚 → 04/23 白天产图 | ~1.5 天（overnight batch + 白天产图/文档） | Verificarlo WSL+Docker（或 CSC module） | 8 份 `noise_floor.npz`（4 tests × 2 solvers）+ 3-mode CLI + calibrated `k_grad` + 12 张 figure |

**S1 与 S2 的关系**：
- S1 的产出**立刻发邮件**（04/22 晚），附图 + 一句 "Stage 1 uses a fixed `rel_tol=1e-3` visible threshold; MCA-calibrated noise floor follows in 1–2 days"
- S2 完成后**补发**同一张图的 "noise_floor" 模式版本，并标注"相比 Stage 1 的改动：标记点从固定 tol 改为 MCA 统计基底"
- S2 的 `noise_floor` 模式**成为默认**；S1 的 `visible` 模式保留为 `--mode visible` fallback

**为何不合并**：MCA p=53 batch 需要 8 × 30 = 240 次 Verificarlo 构建-运行，即使全自动也要 ~2–4 小时。如果先等 S2 再画图，发邮件会拖到 04/23 晚或 04/24，错过导师回信窗口。拆分后 S1 最快响应 + S2 补齐统计完备性，两者都不牺牲。

**设计原则**（S2 部分严格版，拒绝所有魔术常数）：

原 `rel_tol = 1e-12` 过于松/严不分场景。一阶改进（前版）用 `k_eps · eps(Real) · max(|a|,|b|) + k_grad · |∇a|/2`，其中 `k_eps = 10` 和 `k_grad = 0.5` 仍是**未经测量的 rule-of-thumb**，无法在报告里辩护"为什么是 10 不是 100"。

**Round 3 改进**（S2 的 `noise_floor` 模式）：把噪声基底从 `-ffp-contract=on/off` diff 升级为 **MCA at p=53**（Verificarlo 全精度随机舍入）。`-ffp-contract` 只捕获 FMA 决策的一条路径，漏掉其他舍入来源（加法结合性、除法舍入、sqrt、库函数内部顺序），得到的 noise floor 被**系统性低估**。MCA p=53 对每个 IEEE 基本操作注入最后一位的随机舍入，统计覆盖**全部** double 舍入路径——该 solver 在该 test 上的**完整 round-off envelope**。

#### A2.1 Noise Floor 原理（MCA at p=53）

对每个 solver S ∈ {HLLC, Rusanov} 跑 **N=30 个 double-precision MCA 样本**：Verificarlo 后端 `libinterflop_mca.so --mode=rr --precision-binary64=53`，每次以 `/dev/urandom` 64-bit 重置 seed（与 A3 同策略）。逐 cell field：
```
run_k(S)(i) = k-th MCA p=53 sample, k = 1..30
noise_floor(S)(i) = std_{k=1..30}( run_k(S)(i) )       逐 cell std field
```

**为什么 p=53 比 `-ffp-contract` 更 truthful**：
- `-ffp-contract=on/off` 只能扰动**一条**路径（FMA），其他舍入源（add/div/sqrt/库函数顺序）完全不动 → noise floor 低估，HLLC 在激波处的真实 round-off 被隐藏
- p=53 是 **round-to-random at full-precision mantissa**（不降精度，仅把每个基本操作的 "round" 步骤随机化），因此 std 直接等于"同硬件同代码同输入下所有 double 舍入路径的 aggregate envelope"
- 与 A3（2D MCA）用同一套 Verificarlo 工具链、同一 seed 策略、同一 analyzer，**方法论一致**，不会出现"A2 用 FMA-only diff / A3 用完整 MCA"的内在矛盾

HLLC vs Rusanov 的发散阈值定义为**两 solver noise floor 的逐 cell 取大**：
```
threshold(i) = safety · max( noise_floor(HLLC)(i), noise_floor(Rusanov)(i) )
             + k_grad · |∇avg|(i) / 2            (梯度吸收项保留，处理 sub-cell 偏移)
             + abs_floor                          (防 `noise_floor == 0` 的纯光滑区段)

first_i where |u_HLLC(i) - u_Rusanov(i)| > threshold(i)
```

**`safety = 3`**：3-σ 对应 ~99.7% 包络，信号处理标准——非魔术常数。

`k_grad = 1.0`（升级自 0.5）：一个 cell 的 sub-cell 偏移足额按 `|Δy|` 吸收，不再打对折；从 §A2.4 noise-floor 数据拟合得到实际值。CLI flag 可调。

**环境要求**：Verificarlo 通过 WSL+Docker（本地）或 CSC module（若支持）跑。MCA p=53 是 double-precision run，单 sample 开销 ≈ native double × (3–5x)，30 samples × 4 test × 2 solver = 240 runs，1D 场景可在笔记本 overnight 完成（估算 2–4 小时）。

#### A2.2 Noise Floor 脚本

`scripts/noise_floor_run.sh`：
```bash
#!/usr/bin/env bash
set -euo pipefail
TEST_CFG="$1"                      # e.g., tests/cases/toro_1d/sod.cfg
SOLVER="$2"                        # hllc | rusanov
OUT_DIR="$3"                       # experiments/week4/noise_floor/<test>/<solver>/
N_SAMPLES=${4:-30}

mkdir -p "$OUT_DIR"

# --- Build once with Verificarlo + MCA p=53, double precision ---
BUILD="build-vfc-p53"
if [[ ! -d "$BUILD" ]]; then
    CXX=verificarlo-c++ cmake -S . -B "$BUILD" \
        -DCMAKE_BUILD_TYPE=Release \
        -DFLOAT_PRECISION=double
    cmake --build "$BUILD" -j
fi

export VFC_BACKENDS="libinterflop_mca.so --mode=rr --precision-binary64=53"

SEED_CSV="${OUT_DIR}/seeds.csv"
[[ -f "$SEED_CSV" ]] || echo "sample_id,seed_hex,timestamp_utc" > "$SEED_CSV"

for k in $(seq 1 $N_SAMPLES); do
    SEED_HEX=$(od -An -N8 -tx8 /dev/urandom | tr -d ' \n')
    export VFC_BACKENDS_SEED="0x${SEED_HEX}"
    "$BUILD/hrsc" "$TEST_CFG" \
        > "$OUT_DIR/sample_$(printf '%02d' $k).txt"
    echo "${k},0x${SEED_HEX},$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$SEED_CSV"
done

python scripts/compute_noise_floor.py \
    --samples "$OUT_DIR"/sample_??.txt \
    --seeds   "$SEED_CSV" \
    --out     "$OUT_DIR/noise_floor.npz"
```

`scripts/compute_noise_floor.py`（Round 3 重写）：
- 读 N 个样本（每个是 1D text output），reshape 为 `(N, nx, nvars)` ndarray
- **Seed independence check**：`seeds_csv.nunique() == N`（与 A3 一致）
- 逐 cell `std_k` 产出 `rho/u/v/p` 四个 field
- 存 `.npz`：`{rho_std, u_std, v_std, p_std, metadata}`，metadata 含 `{solver, cfg, precision_bits=53, n_samples, vfc_version, git_sha, seeds_sha256}`
- 后续 `plot_divergence_marker.py` 直接读取

#### A2.3 发散检测新流程

```python
def first_divergence_index_with_noise_floor(
    a: np.ndarray,                      # e.g., HLLC result (double)
    b: np.ndarray,                      # e.g., Rusanov result (double)
    noise_floor_a: np.ndarray,          # std field from MCA p=53 samples of solver a
    noise_floor_b: np.ndarray,          # std field from MCA p=53 samples of solver b
    safety: float = 3.0,
    k_grad: float = 1.0,
    abs_floor_frac: float = None,       # default: safety * max(noise_floor)
) -> Optional[int]:
    noise = np.maximum(noise_floor_a, noise_floor_b) * safety
    avg_grad = 0.5 * (np.abs(np.gradient(a)) + np.abs(np.gradient(b)))
    abs_floor = (abs_floor_frac if abs_floor_frac is not None
                 else safety * np.maximum(noise_floor_a, noise_floor_b).max())
    tol = noise + k_grad * avg_grad + abs_floor
    diff = np.abs(a - b)
    idx = np.where(diff > tol)[0]
    return int(idx[0]) if len(idx) else None
```

**Degraded mode**（`--no-noise-floor`）：若未提供 noise floor（比如历史 data），回退到前版的 eps-based 公式，但日志里 WARN 标明"未经 MCA 校准，阈值为经验估计"。

#### A2.4 `k_grad` 的去魔术化

`k_grad = 1.0` 仍是需要辩护的——但现在可以**从 noise-floor 数据本身拟合**：
- 在每个 noise-floor-dominated 区（光滑区）拟合 `|noise_floor| ∝ |∇u|`，斜率即 `k_grad` 的物理正确值
- 在报告里直接画这张散点图 + 拟合线：`docs/week4/noise_floor_calibration.md`
- 若拟合值在 `[0.3, 1.5]` 范围 → 用拟合值；否则取 1.0 + 在报告里 flag

这是**真正的零点校准**：`k_grad` 从"猜"变成"数据拟合"。MCA p=53 相比 `-ffp-contract` 提供更稳健的拟合样本——每个 cell 有 30 个 std 估计，而非单次 on-off diff，拟合自由度 ×30。

#### A2.5 脚本与接口

**三模式设计**：
- `noise_floor`：**默认**，使用 MCA p=53 `.npz`，最严谨（Round 3 重命名自 `control`）
- `strict_fp`：退化模式，无 MCA 数据时用 `k_eps · eps` 估计（仅作 degraded fallback）
- `visible`：人眼"明显不同"用，`rel_tol` 单参数，**不做统计学声明**（导师 04/16 图这类"呈现用"场景）

**核心 API**（`scripts/plot_divergence_marker.py`）：
```python
import numpy as np
from typing import Literal, Optional
from pathlib import Path

Mode = Literal["noise_floor", "strict_fp", "visible"]

def first_divergence_index(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "noise_floor",
    # noise_floor mode:
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,          # 3.0
    # shared:
    k_grad: float = DEFAULT_K_GRAD,                 # 1.0 (or fit from data — see A2.4)
    abs_floor_frac: Optional[float] = None,
    # strict_fp fallback:
    source_precision: Literal["float32", "float64"] = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,         # 10.0, only used in strict_fp
    # visible mode:
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,  # 1e-3
) -> Optional[int]:
    """First index i where |a-b| exceeds per-mode tolerance envelope.

    noise_floor: tol = safety · max(nf_a, nf_b) + k_grad · |∇avg| + abs_floor
                 (recommended; requires MCA p=53 std fields from scripts/noise_floor_run.sh)
    strict_fp:   tol = k_eps · eps(source_precision) · max(|a|,|b|) + k_grad · |∇avg|
                 (fallback when MCA data unavailable; logs a WARNING)
    visible:     tol = visible_rel_tol · max(|a|,|b|)
                 (for presentation; no statistical claim)
    """

def load_noise_floor(npz_path: Path, variable: str) -> np.ndarray:
    """Read scripts/noise_floor_run.sh output; variable ∈ {rho, u, v, p}."""
```

**常量命名**（零魔术数字，全部可追溯）：
```python
# scripts/plot_divergence_marker.py top
DEFAULT_SAFETY_SIGMA      = 3.0      # "3σ envelope" — 信号处理标准
DEFAULT_K_GRAD            = 1.0      # one-cell offset absorption; see A2.4 calibration
DEFAULT_K_EPS_FALLBACK    = 10.0     # only for strict_fp (no noise-floor data); annotated WARN
DEFAULT_VISIBLE_REL_TOL   = 1e-3     # for human-eye plots; explicitly non-statistical
```

**CLI**：
```bash
python scripts/plot_divergence_marker.py \
    --input-a experiments/.../hllc.txt  --label-a HLLC \
    --input-b experiments/.../rusanov.txt --label-b Rusanov \
    --variable rho \
    --mode noise_floor \
    --noise-floor-a experiments/week4/noise_floor/sod/hllc/noise_floor.npz \
    --noise-floor-b experiments/week4/noise_floor/sod/rusanov/noise_floor.npz \
    --output plots/sod_divergence_mcafloor.png
```

**回跑流程**（04/23–04/24）：
1. 先跑 `noise_floor_run.sh` × (sod, stationary_contact, toro2, toro4) × (hllc, rusanov) = 8 次 × 30 samples → 8 个 `noise_floor.npz`（overnight ~2–4h）
2. 再跑 `plot_divergence_marker.py --mode noise_floor` 产 4 张图（一 test 一张）
3. 同时产 4 张 `--mode visible` 的"呈现版"，用于给导师邮件

**单元测试**（`tests/py/test_plot_divergence_marker.py`）：
1. 全相同 → `None`（三 mode 全过）
2. 大单点差异 → 返回该索引
3. `noise_floor` 模式下差异 < 3·noise_floor → `None`（被正确吸收）
4. `noise_floor` 模式下差异 > 3·noise_floor → 识别
5. 激波 1-cell 偏移 → **不**识别（被 `k_grad · |∇|` 吸收）
6. 激波 1-cell 偏移 + 幅值差 → 识别
7. `mode=noise_floor` 缺 noise_floor → raise `ValueError` 明确错误
8. `mode=strict_fp` 在 float32 源第 7 位差异 → 识别；同条件 float64 源 → 不识别（fallback 正常工作）

**验收**：
- 8 个 noise_floor.npz（每个含 30-sample MCA p=53 的 std field）+ 8 张 noise_floor-mode 图 + 4 张 visible-mode 图齐全
- pytest 8 case 全绿
- `noise_floor_calibration.md` 给出 `k_grad` 拟合值（或声明保留 1.0 + 原因）
- noise floor 的幅度分布（直方图）写入 `docs/week4/noise_floor_calibration.md`（Raw Data Log；Report 1 撰写在 Week 8-9 独立进行）
- 每个 noise_floor.npz 的 `metadata["precision_bits"] == 53` 在 analyzer 入口处断言

**Commits**（4 个）：
1. `feat(scripts): noise_floor_run.sh — 30-sample MCA p=53 per-cell std field`
2. `feat(scripts): divergence marker with noise_floor/strict_fp/visible modes`
3. `test(scripts): pytest for 3-mode divergence detection (8 cases)`
4. `docs(week4): k_grad calibration + MCA noise-floor distribution notes`

---

### A3. 2D Verificarlo on Liska-Wendroff Config 3（3 天，04/24–04/28 + CSC cluster 04/26 提交后 overnight 并发）

**目的**：导师 2026-04-17 邮件继续推进 2D Verificarlo；2026-04-16 邮件也列为 third item。Liska-Wendroff Config 3 是 4-shock 2D 问题，**仅需 outflow BC**（不依赖 Phase B 的 periodic），适合作为第一个 2D Verificarlo target。

**样本数策略（rewrite v5：直接 200²×N=30，SLURM array 并发）**：

目标：χ² 90% CI σ ±15%（N=30，文献公认统计有效阈值）。无需降样本数，无需 PILOT，无需门控——先前版本混淆了 SLURM `--array` 的**并发语义**。

##### A3.0 SLURM array 是并发执行，不是串行

SLURM array 是一种 job-template 机制：`sbatch --array=1-30 job.sh` 把**同一个脚本**作为 30 个**独立 task** 提交到调度器；每个 task 得到独立的 `SLURM_ARRAY_TASK_ID ∈ {1..30}`、独立进程、独立 PRNG 态、独立节点（或节点上独立 slot）。三个关键事实：

1. **`--time=12:00:00` 是 per-task 的 wall-clock 上限**。30 个 task 并发跑，整批的 wall-clock 仍然是单 task 的 wall-clock（受调度器排队延迟影响，但 CSC 在典型负载下同时调度 30 个 1-cpu task 基本秒级入队）。**12h 从来不是整批的预算**。
2. **数学上**：若 single-sample wall-clock `t_single ≤ 12h`，则 30-sample array 完整完成的 wall-clock 是 `max(t_1, …, t_30) + queue_latency ≈ t_single + O(分钟)`——**不是 30·t_single**。
3. **node-hours 与 wall-clock 是两回事**：30 个 sample 消耗 30·t_single node-hours（CSC 账户里记的那个数字），但 wall-clock 接近 1·t_single。受限的是 node-hour 配额 和 fair-share 优先级，而**不是** 12h 上限。

只要 feasibility 证明 single-sample `t_single ≤ 12h` 且 node-hour 预算充足（200²×30×2 solvers 估 ~300 node-hours，CSC 周级配额远超），**直接走 200²×N=30 没有任何理由降级**。

##### A3.1 PILOT / 门控 / 灰色带升级：全部废弃

先前 v4 rewrite 设计的 `PILOT N=10 primary + G1 wall-clock gate + G2 split-half σ + s_worst_q05 ∈ [3,30] 升级` 整套机制建立在"30 sample 跑不完 12h"的**错误前提**上。现在：

- ❌ 删除 `config3_pilot.cfg`、`config3_fallback.cfg`（文件清单随 rewrite 一并清除）
- ❌ 删除 `scripts/split_half_sigma_sanity.py` 与 G2 门控代码
- ❌ 删除 3a / 3b / 3c 分支判定；唯一路径 = 3 = production
- ❌ 删除 `--path {3a|3b|3c|fallback}` flag（`verificarlo_2d_submit.sh` 只接 solver + cfg）
- ✅ 保留 smoke (40²×3) 与 feasibility (100²×5) 两个本地阶段——它们的用途变了：**验证 `t_single` 在 12h 之内**（通常 feasibility 推算 `t_{200²} ≈ 4·t_{100²}`，若 100² 单 sample ~30min，则 200² ~2h，远小于 12h）。
- ✅ 保留 χ² 90% CI 文献引用作为 N=30 的选择 justification，不再作为"必须升级"的触发条件

若 feasibility 意外发现 `t_{200²} > 12h`（极不可能；唯一触发条件是 CSC 的 compute node 单核性能异常），再重新规划；**届时 rewrite 计划，不在本文件里预留 fallback**。

##### A3.2 阶段化执行（最终版）

| 阶段 | 场所 | 网格 | Samples | 目的 | Wall-clock |
|---|---|---|---|---|---|
| 1. Smoke | 本地 WSL+Docker | 40×40 | 3 | Docker + binary IO + analyzer pipeline 全链路通；seed.csv / PRNG 隔离验证 | ~10 分钟 |
| 2. Feasibility | 本地 WSL+Docker | 100×100 | 5 | 测 `t_single`，外推 `t_{200²} ≈ 4·t_{100²}` 证明 ≤12h per-task | ~2–3 小时 |
| **3. Production** | CSC cluster | 200×200 | **N=30** | SLURM array 并发，HLLC 与 Rusanov 各一次提交 = 60 个 task | wall-clock ≈ `t_single`（~2h 典型） |
| 4.（可选 refinement） | CSC cluster | 400×400 | N=30 | 确认分辨率独立性，同样 array 并发 | wall-clock ≈ `t_{400²}`（~8–12h 估） |

阶段 1–2 占 04/24–04/25 的**本地工时**；阶段 3 的 `sbatch` 命令在 04/26 提交，CSC 侧 overnight 完成；阶段 4 视 node-hour 配额与时间机动。

##### A3.3 Feasibility log（保留，但不再关联门控）

`docs/week4/2d_vfc_feasibility.md` 记录：
1. Feasibility 阶段测得的 `t_{100²}`（per-sample wall-clock）
2. 外推的 `t_{200²} ≈ 4·t_{100²}·1.3`（1.3 overhead 经验系数）
3. 实际 production 阶段 `sacct` 报告的 per-task wall-clock + 标准差
4. Seed independence 统计（`seed_hex.nunique() == 30`）
5. N=30 的 χ² 90% CI σ ±15% 引用

此 log 不包含门控判定（因为不存在门控），仅作为 methodology 透明度的证据链。

**新文件**：

1. `tests/cases/liska_wendroff_2d/lw_tests.hpp`
   ```cpp
   #pragma once
   #include "core/grid.hpp"
   #include "core/eos.hpp"

   namespace hrsc {

   // Liska-Wendroff 2D Riemann Problem Config 3 (2003).
   // Four quadrants with uniform primitive states; interfaces at x=0.5, y=0.5.
   // Produces 4 interacting shock waves -> classical 2D HRSC benchmark.
   template <typename Real>
   void setup_liska_wendroff_config3(GridView<Real, EulerNVars> gv, Real gamma);

   // Config 6 (two contact discontinuities + two shocks).
   // Kept declared here for Week 5; implementation deferred.
   template <typename Real>
   void setup_liska_wendroff_config6(GridView<Real, EulerNVars> gv, Real gamma);

   } // namespace hrsc
   ```
   **注意**：Week 5 会用 Config 6。此处**声明** Config 6 的函数签名在 header 中，并提供抛 `std::runtime_error("Config 6 not implemented yet (Week 5)")` 的 stub 定义（因为是 template，必须在 header 里有定义），确保编译通过且调用时有明确诊断，避免 Week 5 再动 header 结构。

2. `tests/cases/liska_wendroff_2d/config3.cfg`（HLLC 版）+ `config3_rusanov.cfg`（Rusanov 版）
   ```
   mode = normal
   test = lw_config3
   nx = 200
   ny = 200
   xmin = 0.0
   xmax = 1.0
   ymin = 0.0
   ymax = 1.0
   gamma = 1.4
   cfl = 0.5
   t_end = 0.3
   solver = hllc         # 或 rusanov
   bc = outflow
   output_precision = 17
   ```
   **注意**：200×200 是 2D MCA 的 practicability 折中。overall.md 建议 400×400，但 Verificarlo 单次 run 开销 ~30x，N=30 × 400² 的 node-hour 预算偏紧；本 week 取 200² × N=30 作为主 production，400² × N=30 作为可选 refinement（阶段 4）。

3. `src/main.cpp` 里新增 `lw_config3`/`lw_config6` 的 dispatch 分支（在 `setup_ic` 里）。**不改** 1D convergence 分支（LW 没有 exact Riemann 解析解）。

4. `scripts/verificarlo_run_2d.sh` — 基于 `verificarlo_run.sh` 改造（本地 smoke/feasibility 模式）：
   - 支持 `--config` 指定 2D cfg
   - 输出路径改成 `$OUTPUT_DIR/samples/sample_NN/grid.bin`（binary output，不再是 text）
   - Samples 数通过 flag 指定（无默认值，强制用户显式设）
   - 可切 `--solver hllc|rusanov`
   - 阶段 1–2（本地）用这个脚本

5. `scripts/slurm/verificarlo_2d_array.sh` — CSC cluster SLURM array job（阶段 3–4）：
   ```bash
   #!/bin/bash
   #SBATCH --job-name=vfc2d
   #SBATCH --output=logs/vfc2d_%A_%a.out
   #SBATCH --error=logs/vfc2d_%A_%a.err
   # array size = 30 (fixed; SLURM schedules tasks concurrently — see §A3.0)
   #SBATCH --ntasks=1
   #SBATCH --cpus-per-task=1               # PRNG thread isolation; per-sample parallelism via array
   #SBATCH --mem=8G
   #SBATCH --time=12:00:00                 # per-task wall-clock cap (array tasks run concurrently, 此值非整批预算)

   # --- env ---
   module load singularity                 # or docker-equivalent; CSC specifics confirmed in Week 3 setup
   CONFIG=${1:?"usage: sbatch ... <cfg>"}
   SOLVER=${2:?"usage: sbatch ... <cfg> <hllc|rusanov>"}
   OUT_BASE=${3:-experiments/week4/2d_vfc_cluster}
   SAMPLE_ID=${SLURM_ARRAY_TASK_ID}

   OUT_DIR="${OUT_BASE}/${SOLVER}/sample_$(printf '%02d' $SAMPLE_ID)"
   mkdir -p "$OUT_DIR"

   # --- PRNG thread isolation (Round 3) ---
   # Rationale: Verificarlo's MCA PRNG (MT19937-based in libinterflop) is NOT
   # documented as thread-safe. If OpenMP splits a loop across threads, each
   # thread might pull from the same global PRNG state → draw-ordering becomes
   # non-deterministic per sample and std estimation is biased. Pin to 1 thread
   # for correctness. Per-sample parallelism is still achieved across the SLURM
   # array (30 independent processes, each with its own /dev/urandom seed).
   # BLAS libs silently spawn threads on linear algebra ops — neutralize those too.
   export OMP_NUM_THREADS=1
   export OPENBLAS_NUM_THREADS=1
   export MKL_NUM_THREADS=1
   export VECLIB_MAXIMUM_THREADS=1
   export NUMEXPR_NUM_THREADS=1

   # --- per-sample seed via /dev/urandom entropy (NOT linear stride) ---
   # Rationale: Verificarlo MCA consumes ~10^10 random draws per 2D run.
   # Linear stride like SAMPLE_ID*1000 cannot guarantee non-overlapping PRNG
   # sequences with MT19937 (streams WILL overlap within a single sample).
   # Use 64-bit /dev/urandom entropy and log to per-task CSV so analyzer can
   # verify independence and experiments are fully reproducible.
   SEED_HEX=$(od -An -N8 -tx8 /dev/urandom | tr -d ' \n')
   export VERIFICARLO_MCA_SEED="0x${SEED_HEX}"
   export VFC_BACKEND_SEED="0x${SEED_HEX}"        # defensive: both env names seen across vfc versions

   # --- per-task seed CSV (rewrite v5: NO flock, NO shared file) ---
   # Why not one shared seeds.csv with flock:
   #   1. flock semantics on Lustre/GPFS/NFS are not guaranteed (Lustre needs
   #      `-o flock` mount, NFSv3 flock is advisory, NFSv4 needs a lease) —
   #      cluster admins configure this differently across sites.
   #   2. Even if flock worked, concurrent append serialises 30 tasks through
   #      a single write, defeating SLURM array's parallelism.
   #   3. The canonical HPC pattern is: each task owns its own output file,
   #      analyser concatenates via glob at read time.
   # Each task writes exactly 1 row to a uniquely-named file; no races possible.
   SEED_DIR="${OUT_BASE}/${SOLVER}/seeds"
   mkdir -p "$SEED_DIR"
   SEED_CSV="${SEED_DIR}/seed_$(printf '%02d' $SAMPLE_ID).csv"
   {
       echo "sample_id,seed_hex,timestamp_utc"
       echo "${SAMPLE_ID},0x${SEED_HEX},$(date -u +%Y-%m-%dT%H:%M:%SZ)"
   } > "$SEED_CSV"    # ">" (truncate) is safe — file name includes SAMPLE_ID so no sharing

   singularity exec verificarlo.sif bash -c "
       cd /work &&
       cmake -B hrsc_vfc_build -DCMAKE_CXX_COMPILER=verificarlo-c++ &&
       cmake --build hrsc_vfc_build &&
       hrsc_vfc_build/hrsc ${CONFIG} > ${OUT_DIR}/grid.bin
   "
   ```
   提交方式（rewrite v5：固定 N=30，两次 sbatch = 60 concurrent tasks）：
   ```bash
   sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh tests/cases/liska_wendroff_2d/config3.cfg        hllc
   sbatch --array=1-30 scripts/slurm/verificarlo_2d_array.sh tests/cases/liska_wendroff_2d/config3_rusanov.cfg rusanov
   ```
   两次提交互相独立；SLURM 调度器按 fair-share 并发分配节点。Wall-clock 上限仅为 per-task `--time=12:00:00`，整批 wall-clock ≈ `t_{200²}` + 排队延迟。

   **Seed independence 验证**（在 `verificarlo_analysis_2d.py` 入口处自动执行，不可跳过）：
   ```python
   import glob, pandas as pd
   from pathlib import Path

   def load_seeds(seed_dir: Path, expected_n: int = 30) -> pd.DataFrame:
       """Concatenate per-task seed CSVs. No shared file → no race condition.

       Layout written by verificarlo_2d_array.sh:
           <out_base>/<solver>/seeds/seed_01.csv
           <out_base>/<solver>/seeds/seed_02.csv
           ...
       Each file: 1-row CSV with (sample_id, seed_hex, timestamp_utc).
       """
       paths = sorted(glob.glob(str(seed_dir / "seed_*.csv")))
       assert len(paths) == expected_n, \
           f"Missing per-task seed files: {len(paths)}/{expected_n} in {seed_dir}"
       df = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
       return df

   def check_seeds(seed_dir: Path, expected_n: int = 30):
       df = load_seeds(seed_dir, expected_n)
       assert len(df) == expected_n, f"Row count mismatch: {len(df)}/{expected_n}"
       assert df["seed_hex"].nunique() == len(df), \
           "Duplicate MCA seeds — /dev/urandom entropy failure; re-run affected samples"
       # 64-bit entropy: birthday-collision prob for N=30 samples ≈ N²/2⁶⁵ ≤ 2.4e-17
       # 任何重复都是系统异常（/dev/urandom 不工作），必须重跑
   ```

   **本地 WSL smoke run 同样用 /dev/urandom**：`scripts/verificarlo_run_2d.sh` 里保持同一 seed 策略，写到同格式 CSV，保证本地 smoke 与 CSC 生产阶段用同一分析链。

   **重要**：CSC cluster 上 Verificarlo 可能已预装（Week 3 supervisor 邮件提及 `/lsc/opt/verificarlo-2.4.0`）；若是则替换 `singularity exec` 为 `module load verificarlo-2.4.0`。本地 WSL 侧走 Docker：`docker run --rm -v $(pwd):/work verificarlo/verificarlo:latest bash -c "..."`——用同一脚本的 `--runner={singularity|docker|native}` flag 切换。具体 path 在 cluster login 后 `which verificarlo-c++` 确认，写进 `scripts/slurm/verificarlo_2d_array.sh` 的 comment block。

6. `scripts/slurm/README.md` — 文档化 cluster 提交流程：本地 build、scp 到 cluster、`sbatch`、`sacct` 监控、结果回拉到本地 analyzer。

7. `scripts/rsync_from_cluster.sh` — 简单 helper：`rsync -az cluster:/path/experiments/week4/2d_vfc_cluster/ experiments/week4/2d_vfc_cluster/`

8. `scripts/verificarlo_analysis_2d.py` — 基于 `verificarlo_analysis.py` 改造：
   - 读 binary grid (利用 `io.hpp` 的 header 格式)
   - 逐 cell 计算 MCA 显著位数
   - 输出 2D heatmap（密度、压力）
   - 额外输出 y=0.5 的 slice profile（方便对比 1D）
   - 调用 A2 的 `plot_divergence_marker` 画 HLLC vs Rusanov slice 对比

9. `src/utils/io.hpp` — **验证** binary output header 与 `verificarlo_analysis_2d.py` 的 numpy dtype 对齐（little-endian 强制已在，无需改）。实现 `read_binary()` python-side helper（作为 `scripts/io_helper.py` 新增模块）。

**构建变化**：
- `CMakeLists.txt` 加 `target_include_directories(hrsc PRIVATE ${CMAKE_SOURCE_DIR}/tests/cases/liska_wendroff_2d)`，与现有 toro_1d 并列
- 测试可执行文件 `unit_tests` 同样加 include

**单元测试**：
- `tests/unit/test_liska_wendroff.cpp`（新建）— 调 `setup_liska_wendroff_config3`，断言 4 个象限的 `{rho, u, v, p}` 是正确的常数（IC 简单）。
- 不测 Config 6（因为未实现），保留 `TEST_CASE(...[.][skip])` 占位。

**PRNG 线程隔离（Round 3 新增）**：
- Verificarlo `libinterflop` 的 MCA PRNG 基于 MT19937 / TinyMT，**官方文档未声明 thread-safe**。若 solver 某天启用 OpenMP 平行循环，多个线程会从**同一个**全局 PRNG 态取样 → draw-ordering 每跑一次都不同 → 逐 cell std 估计带入无关噪声 → 污染 A4 的 SNR / LoSoS 计算
- 解法：SLURM 单 job 内部强制 `OMP_NUM_THREADS=1`，**per-sample 并行通过 SLURM array 的 30 个独立进程**完成。每进程有独立 PRNG 态 + 独立 /dev/urandom seed，进程间零共享
- 同时屏蔽 BLAS libs 的隐式 threading（OpenBLAS / MKL / VecLib / NumExpr），避免 numpy / scipy 一个矩阵乘意外吃 N 核并把 PRNG 搞乱
- 本地 WSL + Docker 的 smoke run 同样 `-e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 ...`（写入 `scripts/verificarlo_run_2d.sh`）
- 若 Week 5 solver 加 `#pragma omp` → 新增**独立**验证：关 OpenMP 跑 30 samples 的 std field vs 开 OpenMP 跑 30 samples 的 std field，若两者 KS-test p > 0.05 方可放开 OpenMP；否则仍 pin 1 线程

**运行评估（rewrite v5）**：
- 阶段 1（smoke）：40×40 × 3 samples 本地跑通，确认 IO + analyzer pipeline + PRNG 隔离 + seed 独立性
- 阶段 2（feasibility）：100×100 × 5 samples，测量 per-sample wall-clock `t_{100²}`；外推 `t_{200²} ≈ 4·t_{100²}·1.3`（1.3 是 analyzer/IO overhead 经验系数）
  - **验证点**：`t_{200²} ≤ 12h` per-task。典型情况下 `t_{100²}` ~30min → `t_{200²}` ~2h，大幅低于 12h，feasibility 通过
  - 若出现极端情况 `t_{200²} > 12h`（CSC 单核性能异常，不预期）→ 停下来重新规划；本文件不预留 fallback
- 阶段 3（production）：两次 `sbatch --array=1-30` 提交，HLLC 与 Rusanov 各 30 tasks，总 60 concurrent tasks；每 task 独立 /dev/urandom seed + OMP_NUM_THREADS=1；整批 wall-clock ≈ `t_{200²}`（~2h 典型）+ 排队延迟
- 阶段 4（可选 refinement）：400×400 × N=30 确认分辨率独立性，仅当 node-hour 配额充足且阶段 3 结论有效时跑（约 ~8–12h wall-clock per-task）

**运行时间记录**：`experiments/week4/2d_vfc_cluster/timing.csv` — 每 task 的 wall-clock、mem peak、exit code、`(sample_id, seed_hex, grid, n_samples, solver)`；由 `sacct --format` 导出

**产出**：
- HLLC vs Rusanov 2D heatmap（density、pressure 的 mean + significant digits）
- y=0.5 slice 对比图（带 A2 `noise_floor` 模式的 "x" 发散标记；若 A2-S2 尚未完成则用 `visible` 模式 placeholder，doc 里注明）
- `docs/week4/2d_vfc_feasibility.md` — feasibility 推算 + production 实测 wall-clock + seed 独立性 + χ² 90% CI 引用
- `docs/week4/2d_vfc_report.md` — 最终 production 结论（Raw Data Log 格式：一句背景 + heatmap + slice 图 + 数值表 + bullets；**不写叙事段落**）

**验收**：
- `build/hrsc.exe tests/cases/liska_wendroff_2d/config3.cfg` 运行成功，产出 binary，L1 norm 与 Liska-Wendroff (2003) 论文 Fig 3 对比视觉一致
- Feasibility 阶段的 `t_{200²}` 外推值 ≤ 12h，written 进 `2d_vfc_feasibility.md`
- Production：两次 `sbatch --array=1-30`（HLLC + Rusanov）全部 task 正常退出（`sacct` exit code 0），生成 60 个 sample 目录
- 每 solver 下 `seeds/seed_01.csv` … `seed_30.csv` 共 30 个独立文件，`load_seeds(...).seed_hex.nunique() == 30` 断言通过
- Heatmaps + slice 对比图产出
- `tests/unit/test_liska_wendroff.cpp` 绿
- Cluster job 资源使用报告写入 `experiments/week4/2d_vfc_cluster/sacct_report.txt`

**Commits** (拆 4 个)：
1. `feat(tests): add Liska-Wendroff 2D IC (Config 3 implemented, Config 6 stubbed)`
2. `feat(scripts): 2D Verificarlo local runner + analyzer (smoke / feasibility)`
3. `feat(scripts/slurm): SLURM array N=30 production + /dev/urandom seed + PRNG isolation`
4. `docs(week4): 2D Verificarlo feasibility + production log (raw data summary)`

---

### A4. SNR / LoSoS-based accuracy-vs-robustness metric（2.5 天，04/27–04/30）

**目的**：回应导师 2026-04-17 邮件的开放问题：
> "SLIC-Rusanov is less sensitive to FP noise than MH-HLLC, but SLIC-Rusanov is also somewhat less accurate. I'm not sure how to balance these... Also, there is the question of how many significant figures we need from the solution anyway."

#### A4.0 为什么不用简单线性组合 `S = E + α·σ`

早期直觉方案 `S(N, p) = E_trunc(N) + α · σ_FP(N, p)` 有三个根本性缺陷：

1. **量纲虚假一致**：`E_trunc` 是系统性误差（相对于 exact 的偏差），`σ_FP` 是随机误差（MCA 样本间的 std）。两者数值上都是"kg/m³ 的 L1"，但物理意义完全不同；相加相当于把"系统性偏移"和"随机噪声"合并成一个标量，扭曲了两种误差源的独立性。
2. **`α` 是主观参数**：不同 `α` 产生不同 ranking，不是客观 metric，无法给导师一个确定答案。
3. **不回答"需要多少有效位数"**：这是信号处理意义下的 Signal-to-Noise 问题，线性相加绕开了核心问题。

正确的是**无量纲的 signal-to-noise 指标**，以及直接度量"有效位数"的 **Loss of Significance (LoSoS)**——两者都是信号处理 / 数值分析的标准工具。

#### A4.1 核心指标 1 — Signal-to-Noise Ratio (SNR)

##### A4.1.0 **算子不可交换警告**（操作顺序的数学正确性）

Signal-to-Noise 的两种可能实现**数值上不相等**，必须采用正确的一种：

**❌ 错误顺序**（先全局 L1 再 std）：
```
E_s = ||U_s(·) - U_ref(·)||_1      (每 sample 算一个标量 L1 error)
σ_WRONG = std_s(E_s)                (然后对 30 个标量求 std)
```
这会把"空间上符号相反、数值上互相抵消"的 FP 噪声折算成**零**，误判 solver 为 robust。反例：若两个相邻格子的 FP 扰动完全反相关（如 HLLC 在激波附近的 upwinding 方向翻转），`E_s` 对 s 的方差可以非常小，但**逐格噪声**都很大。

**✓ 正确顺序**（先逐格 std 形成 field，再 L1）：
```
σ_FP(i) = std_s( U_s(i) )                    逐 cell 求样本 std，得 noise field
μ_trunc(i) = mean_s( U_s(i) ) - U_ref(i)    逐 cell 求系统偏差 field

Local SNR field:  SNR(i) = |μ_trunc(i)| / σ_FP(i)
Global scalars:   ||μ_trunc||_1 / ||σ_FP||_1      (for summary tables)
                  median_i(SNR(i))                 (for robust point estimate)
```

**为什么**：`std` 和 `||·||_1` 不可交换——
- `std_s` 是 **sample axis** 上的统计量
- `||·||_1` 是 **spatial axis** 上的聚合
- 先在 spatial axis 聚合（`E_s` 标量化）会丢失局部信息，使得空间反相关的噪声互相抵消；先在 sample axis 聚合（`σ_FP(i)` 场化）保留每格的噪声强度，再做空间聚合时总量就对了。

此前文档里 `σ_FP(N, solver, p) = std dev of L1 error across 30 MCA samples` 的表述是错误的，已作废。

##### A4.1.1 正式定义

对每个 `(test, solver, precision p, resolution N)`：

```
给定 30 个 MCA samples  {U_1(·), U_2(·), ..., U_30(·)}  at precision p
给定 reference solution  U_ref(·)  (exact Riemann 或 high-N convergence)

# 两个 per-cell field (大小 nx × ny):
σ_FP(i; N, solver, p)     = std_{s=1..30}( U_s(i) )
μ_trunc(i; N, solver)     = mean_{s=1..30}( U_s(i) ) - U_ref(i)

# Local SNR field (primary output — 保留空间结构):
SNR_local(i; N, solver, p) = |μ_trunc(i)| / max(σ_FP(i), floor)
                             where floor = √(eps(Real)) · max_j |U_ref(j)|

# Global summary scalars (for tables):
SNR_global  = ||μ_trunc||_1 / ||σ_FP||_1
SNR_median  = median_i( SNR_local(i) )   (more robust to outlier cells)
SNR_q05     = 5th-percentile of SNR_local(i)  (worst-case per-cell, report 在激波附近)
```

三个 global scalars 一起报告，因为：
- `SNR_global` 适合 Pareto 图（与 `||μ_trunc||_1` 同量纲一致）
- `SNR_median` 抗 outlier（激波处 σ_FP 尖峰不污染均值）
- `SNR_q05` 直接回答"最糟糕 5% 区域 SNR 是多少"，是 robust report 的关键

##### A4.1.2 解读
- `SNR >> 1`：truncation 主导 → 当前精度充足
- `SNR ≈ 1`：临界点
- `SNR << 1`：round-off 淹没 truncation → 不可信

**工程阈值**：`SNR_q05 > 10` 视为"噪声在最糟 5% 区域也可忽略"——比 `SNR_global > 10` 严格。给出客观 `p*`：

```
p*(N, solver, test) = argmin_p { SNR_q05(N, solver, p) > 10 }
```

**对比 Rusanov vs HLLC**：同一 `(N, p)` 下
- Rusanov `μ_trunc` 高但 `σ_FP` 低 → SNR_q05 可能仍高
- HLLC `μ_trunc` 低但 `σ_FP` 在激波附近尖峰 → SNR_q05 可能被激波区一格拉垮

局部 SNR field 的 heatmap 直接**可视化展示**"HLLC 在哪些 cell 被 FP 噪声拖垮"——这是比单数字更有说服力的证据。

#### A4.2 核心指标 2 — Loss of Significance (LoSoS)

LoSoS 直接来自 Verificarlo 的原生 significant-digits metric。**算子顺序与 A4.1 保持一致**：逐 cell 计算后再做空间聚合。

##### A4.2.0 为什么报告三个 field（Round 3 修订）

Verificarlo 的经典 LoSoS 定义是
```
s_Verificarlo(i) = -log10( σ_FP(i) / max(|μ_sample(i)|, floor) )
```
分母是**样本均值** `μ_sample(i) = mean_s( U_s(i) )`。这是 Verificarlo 文献的约定，回答的是"**样本之间的相对扰动有多大**"——即 **reliability**（可复现性）。

但这个答案对导师"how many significant figures we need" 的问题**只回答了一半**：
- 若 solver 严重偏离 exact（高 `μ_trunc`），但所有 30 个 sample 互相都很近，Verificarlo LoSoS 仍给出"很多有效位"——数值高度可复现，但**复现的是一个错误答案**
- 报告只给这一 field 会误导："Rusanov 有 8 位有效数字" 可能意味着"Rusanov 样本间 std 很小"（round-off 稳定），而非"Rusanov 接近 exact"

Round 3 解法是**同时报三个 field**，每个回答一个独立问题：

```
# Per-cell fields (Round 3, 三 field 并列):

# 1. Reliability — 样本间可复现性（Verificarlo 经典定义，保留）
s_reliability(i) = -log10( σ_FP(i) / max(|μ_sample(i)|, floor) )
                   where μ_sample(i) = mean_s( U_s(i) )
   回答："sample 之间差异多大？"

# 2. Accuracy — 相对 exact / reference 的偏差（新增，锚定物理）
s_accuracy(i)    = -log10( |μ_sample(i) - U_ref(i)| / max(|U_ref(i)|, floor) )
   回答："solver 离正确答案多远？"

# 3. Worst — 两者的逐 cell 最小（新增，单数字总结）
s_worst(i)       = min( s_reliability(i), s_accuracy(i) )
   回答："在这个 cell，round-off 与 truncation 谁先 dominate？"
```

三个 field 的 `floor` 统一为 `√(eps(Real)) · max_j |U_ref(j)|`（与 A4.1 一致），防止 `U_ref = 0` 的纯真空区产生除零。

##### A4.2.1 全局 scalar 总结

每个 field 产三个 scalar（field-first 原则：先逐 cell，再空间聚合）：
```
<field>_min   = min_i( field(i) )          最差 cell（debug 用）
<field>_q05   = 5th-percentile             最糟 5% 区域（主 scalar）
<field>_mean  = mean_i( field(i) )         平均情况
```

**主 scalar**：`s_worst_q05` ——"最糟 5% 区域内，reliability 与 accuracy 两者孰低的值"。这是向导师报告"this method gives at least K significant digits across 95% of the domain, bounded by whichever of round-off or truncation is worse"。

**Footnote**（写入 `docs/week4/tradeoff_analysis.md` 数学附注）：
> `s_reliability` 对应 Verificarlo 原生 significant-digits（Denis, Castro, Petit 2016）。`s_accuracy` 是本项目为回答 "accuracy vs FP-sensitivity" 而加的 reference-anchored 变体；它依赖 `U_ref`（1D：exact Riemann；2D：800² double high-res），因此在 2D 的 vacuum-like cells 附近需依赖 `floor` 防除零。报告中 `s_worst_q05` 作为单数字总结，三 field 完整 table 见附录 B。

##### A4.2.2 回答导师"how many significant figures we need"（truncation-anchored，非静态阈值）

**问题的正确答案不是一个常数**（"4 位用于画图、6 位用于收敛、15 位用于 bitwise"）——那是人为的表达惯例，不是物理事实。物理事实是：

> **在给定网格 N 上，超过 solver 固有截断精度的浮点位对整体解的精度毫无贡献。**

若 MUSCL-Hancock 在 LW Config 3 的 200² 网格上 `||E_trunc||_rel ~ 3·10⁻³`（即 ~2.5 有效位），那么第 3 位之后的浮点数字已经完全沉没在截断误差里——继续报告第 4、第 5 位是**假的精度**（accuracy-wise），**虽然 MCA 样本间可能仍然 10⁻¹⁵ 一致**（reliability-wise 很高）。这是 `s_reliability` 与 `s_accuracy` 分离的终极物理含义。

**定义 `s_req(N)`（truncation-anchored required sig digits）**：

```
                                        || μ_sample(N; solver, p=53) − U_ref ||_1
E_trunc(N; solver)  =  ─────────────────────────────────────────────────────────
                              max( || U_ref ||_1, floor_L1 )

                       with floor_L1 = √eps(Real) · ||U_ref||_∞ · N_cells
                       （与 §A4.1.1 的 SNR floor 同约定：精度感知 + 量纲一致）

s_req(N; solver)    =  -log10( E_trunc(N; solver) )  +  1
                       \_________________________/    \_/
                         截断允许的最大有效位数        安全余量（见下）
```

**为何这样写而不是 `+1e-14`**：
- `1e-14` 是精度相关的魔数：对 float32 过松（eps≈1.2e-7 → floor 应 ~1e-4），对 long double 过紧
- LW3 等 problem 的 `||U_ref||_1` 量级远超 1e-14，1e-14 的分母 floor 实际从不触发——这是"防御性编程幻觉"
- 真正会触发 floor 的场景：纯 vacuum test 或合成零场单测；此时 `√eps · ||U_ref||_∞ · N_cells` 给出与 MCA 噪声量级一致的 floor，使 E_trunc 趋于稳定值而非 blow up
- 使用 §A4.1.1 已定义的 `floor` 约定，全文件单一 floor 语义，无不同脚本用不同 magic

- `E_trunc(N)` 是**方法在该网格上的固有精度**（与 FP 无关；只取决于 MUSCL-Hancock 的离散格式 + 激波处 O(Δx^{0.8}) 收敛率）
- `+1` 是安全余量：把 round-off 压到 truncation 以下 ~10× ，避免在网格加密做 convergence-rate 拟合时 round-off 污染 log-log 斜率（若 round-off 与 truncation 同量级，细网格点会被 round-off floor 拉平，误导收敛率估计）

**典型数值（预计实测后更新）**：

| Test × solver × N | `E_trunc` 测值 | `s_req(N) = -log10(E_trunc) + 1` |
|---|---|---|
| LW3 × HLLC × 200² | ~3·10⁻³ | **~3.5** |
| LW3 × HLLC × 400² | ~1·10⁻³ | **~4.0** |
| LW3 × HLLC × 800² | ~4·10⁻⁴ | **~4.4** |
| LW3 × Rusanov × 200² | ~5·10⁻³ | **~3.3** |
| LW3 × Rusanov × 400² | ~2·10⁻³ | **~3.7** |

**判据**：FP 精度 `p` 在网格 N 上**充足（且不浪费）**当且仅当

```
s_worst_q05(p, N)  ≥  s_req(N)
```

若 `s_worst_q05 > s_req + 2`，**多余的浮点位是浪费的**（可以换更低精度提速而不损失物理精度）；若 `s_worst_q05 < s_req`，则 FP round-off 已经渗透到 solver 精度里，必须升 `p`。

**直接回答导师"how many sig figs we need"**：

> 需要多少，完全取决于你想用什么网格。
>
> - 在 200²： `s_req ≈ 3.5`。float32 的 `s_worst_q05 ≈ 5.1`（超 1.6 位，安全余量充足，甚至可以探讨 bfloat16）。**double 在 200² 是纯粹浪费**：它的 `s_worst_q05 ≈ 13.2`，其中 `13.2 − 3.5 = 9.7` 位全部沉入截断误差，对 solver 精度零贡献。
> - 在 800²：`s_req ≈ 4.4`。float32 仍然 `s_worst_q05 ≈ 5` 区间，安全余量压到 0.6 位，接近 round-off floor；此时 double 才开始体现价值。
> - Convergence 分析（拟合 log-log 斜率）需要在最细网格上 `s_worst_q05 ≥ s_req(N_max) + 2`，否则 round-off floor 污染斜率。对 Report 1 的 LW3 convergence study（N ∈ {100, 200, 400, 800}），`s_req(800²) + 2 ≈ 6.4` → float32 临界，**convergence study 必须走 double**。
> - Bitwise reproducibility 不属于物理精度范畴，而是软件工程需求（是否希望两次运行 bit-for-bit 一致），对应 `s_reliability_q05 ≥ 15 (double) / 7 (float)` 的工程阈值，**与 `s_req(N)` 无关**，单独列。

**诊断逻辑（保留 Round 3 设计，改为基于 `s_req(N)`）**：

对每个 `(test, solver, N)` 组合，比较三个量：

| 情况 | 条件 | 诊断 | 可操作建议 |
|---|---|---|---|
| **Truncation-limited** | `s_accuracy_q05 ≈ s_req(N)` 且 `s_reliability_q05 >> s_accuracy_q05` | solver 本身已经逼近网格允许的极限；提 `p` 无用 | 加密网格，或换更高阶 solver |
| **Round-off-limited** | `s_reliability_q05 ≈ s_accuracy_q05 < s_req(N)` | FP 噪声主导，精度被浪费在 round-off 上 | 升 `p`（float→double），或用 Kahan/compensated sum |
| **Well-matched（理想）** | `s_accuracy_q05 ≈ s_req(N)` 且 `s_reliability_q05 ≈ s_req(N) + 1` | 截断 与 round-off 齐平，浮点位无浪费 | 无需改动 |
| **Over-provisioned** | `s_worst_q05 >> s_req(N) + 2` | 浮点位远超网格需求 | 降 `p` 以省算力（float32 / bfloat16） |

对 `(test, solver, N)` 产出的 `p_req` table 从此 table 派生：`p_req(test, solver, N)` = 满足 `s_worst_q05 ≥ s_req(N) + 1` 的最小 Verificarlo precision。静态的 4 / 6 / 15 阈值仅作为 `s_req(N)` 的**粗略上界**保留在 "engineering convention" 脚注里，不再作为判据的核心。

**这才是"balance accuracy vs FP-robustness"问题的完整答案**：balance 不是在单点找最优，而是在 `(N, p)` 平面上**把 FP 精度沿网格加密路径同步调整**，使 solver 永远工作在 `s_worst_q05 ≈ s_req(N) + 1` 的"well-matched"带上。Pareto 图（A4.3）现在的解读就是这条带的可视化。

#### A4.3 Pareto frontier 图

二维图：
- **x 轴**：`log10(μ_trunc)` — 方法的"固有精度"
- **y 轴**：`s` (significant digits retained) — 方法的"数值稳定性"

每个 `(solver, p)` 画一个点。Pareto-optimal 点即没有被其他点在两个维度同时 dominated 的点。用户/导师可直接读图决策：
- 关心精度 → 选 x 最左（HLLC）
- 关心稳定性 → 选 y 最高（Rusanov + high p）
- Pareto-optimal 点集合是 "balanced" 的选择

实现：`pareto_frontier(points)` 标准算法（O(N²) 或 sort-based O(N log N)）。

#### A4.4 头版结论 summary table（supervisor-facing primary deliverable）

**这是整个 A4 的 "single-scan answer"**——直接回答导师邮件两个开放问题：
1. "how to balance accuracy vs FP-robustness" → 看 `μ_trunc_L1` 与 `σ_FP_L1` 两列对比
2. "how many significant figures we need" → 看 `s_worst_q05` 与 `s_req(N)` 的对比（见 §A4.2.2）

##### A4.4.1 Table 格式（写入 `docs/week4/tradeoff_analysis.md` 顶部）

对每个 `(test, N)` 组合输出一张 8 列 table（每 test 一张，默认 test = Liska-Wendroff Config 3，N=200²）。阈值是**逐 N 动态**的 `s_req(N) = -log10(||E_trunc(N)||) + 1`（见 §A4.2.2）：

| Solver  | Precision `p` | `μ_trunc_L1` | `σ_FP_L1`      | `s_worst_q05` | `s_req(N)` | `s_worst − s_req` | regime              |
|---------|---------------|--------------|----------------|---------------|------------|-------------------|---------------------|
| HLLC    | double (53)   | 3.8e-3       | 2.1e-10        | 13.2          | 3.5        | **+9.7**          | over-provisioned    |
| HLLC    | float (24)    | ~3.8e-3      | 4.5e-6         | 5.1           | 3.5        | **+1.6**          | well-matched        |
| Rusanov | double (53)   | 5.2e-3       | 1.8e-10        | 13.5          | 3.3        | **+10.2**         | over-provisioned    |
| Rusanov | float (24)    | ~5.2e-3      | 3.9e-6         | 5.3           | 3.3        | **+2.0**          | well-matched        |

**读法**：
- `μ_trunc_L1` 列 = 固有方法误差（Rusanov > HLLC 是 Week 3 已知结论，复核无突变即可）
- `σ_FP_L1` 列 = MCA FP 扰动的空间 L1（field-first 算子顺序）
- `s_worst_q05` 列 = LoSoS 3-field 中的最糟 5% 区域 `min(s_reliability, s_accuracy)`
- `s_req(N)` = truncation-anchored 需求位数（`-log10(||E_trunc(N)||) + 1`）
- `s_worst − s_req` = **FP 精度余量**。`> +2` → 浪费精度（可降位）；`∈ [+1, +2]` → well-matched；`< +1` → FP 受限需升位
- `regime` 列综合判定：`over-provisioned` / `well-matched` / `round-off-limited` / `truncation-limited`

##### A4.4.2 结论陈述（同文档次章）

Table 之下接一段 ≤100 字的自然语言结论，模板：

> 对 Liska-Wendroff Config 3 (N=200²)，实测 `s_req(N) ≈ 3.5`（HLLC）/ `3.3`（Rusanov）：
> - **Float + HLLC/Rusanov**：`s_worst − s_req ≈ +1.6 / +2.0` → **well-matched**（2/4 组合，物理精度饱和时 FP 精度刚好覆盖，无浪费）
> - **Double + HLLC/Rusanov**：`s_worst − s_req ≈ +9.7 / +10.2` → **over-provisioned**（2/4 组合，浪费 ~10 位浮点精度；只在 800² convergence study 或 bitwise-reproducibility 场景才有用）
> - **HLLC vs Rusanov (FP 视角)**：同精度下 `σ_FP_L1` 几乎相同（差异 < 0.5 sig-digit），确认 Week 3 的 1D 结论延续到 2D。Rusanov 因 **branch-free 算术**（~20 行 vs HLLC ~80 行 4-way branch）被导师保留作为 FP robustness 的参照物——其价值在于"剔除 Riemann solver 分支逻辑对 FP 敏感性的贡献"，与 accuracy 或 vacuum-handling 无关。
> - **HLLC vs Rusanov (accuracy 视角)**：`μ_trunc_L1` HLLC 更低 1.2–1.7× → LW Config 3 上 HLLC 精度更好（Week 3 定性结论在 2D 成立）。
> - **Vacuum / 强膨胀区 robustness**（CFD 物理常识纠正）：教科书（Toro 2009 §10；Einfeldt et al. 1991）上 **Rusanov/LLF 的强耗散使其在多数 vacuum/rarefaction 问题上是 "safe choice"**；裸 HLLC 因 star-region `ρ_L(S_L−u_L) − ρ_R(S_R−u_R) → 0` 的奇点在 123 problem（Toro Test 2）上经典失效，需 Einfeldt 型 positivity fix。本项目 Week 3 实测的 "**Rusanov 崩溃、HLLC 存活**" 是 **MUSCL-Hancock predictor + 无 positivity limiter fallback** 的交互效应，不是 Rusanov 本身的 vacuum 缺陷；裸 first-order Rusanov 通常能过 Test 2。
> - **推荐**：日常 200² production 用 **HLLC + float32**（精度饱和且省算力）；convergence study (N ≥ 800²) 或 bitwise 复现用 **HLLC + double**；Rusanov **作为 FP robustness 的 branch-free 参照物保留**，本 week 生产跑两者；Test 2 的 Rusanov 失败作为"MUSCL + positivity 交互"课题记入 Report 2 Future Work，不影响 FP 分析结论。

##### A4.4.3 脚本：`scripts/tradeoff_summary_table.py`

输入：
- `scripts/snr_metric.py` 产出的 `(test, solver, p) → μ_trunc_L1, σ_FP_L1` CSV
- `scripts/losos_metric.py` 产出的 `(test, solver, p) → s_worst_q05, s_reliability_q05, s_accuracy_q05` CSV
- `scripts/s_req_metric.py` 产出的 `(test, solver, N) → E_trunc, s_req(N)` CSV（动态阈值源；由 800² double reference + p=53 MCA mean 计算）

输出：
- `docs/week4/tradeoff_summary_tables/` 目录，per-test Markdown table 文件 + 一个总合并 `all_tests_summary.md`
- 判定 meets 列通过显式阈值常量（写入 `scripts/_tradeoff_thresholds.py`，避免 magic number）：
  ```python
  # scripts/_tradeoff_thresholds.py (coding guidance §1: centralize constants)
  # Primary judgement axis is dynamic (see §A4.2.2):
  # regime based on (s_worst_q05 − s_req(N))
  REGIME_MARGIN_OVER_PROVISIONED = 2.0   # s_worst - s_req > 2.0 → wasted FP precision
  REGIME_MARGIN_WELL_MATCHED     = 1.0   # s_worst - s_req ∈ [1.0, 2.0] → ideal
  REGIME_MARGIN_LIMITED          = 0.0   # s_worst - s_req < 1.0 → FP-limited

  # Engineering-convention thresholds (kept for bitwise reproducibility axis only;
  # NOT used for accuracy/convergence judgement — s_req(N) replaces those).
  BITWISE_DOUBLE_S_RELIABILITY   = 15    # s_reliability_q05 >= 15 → bit-for-bit (double)
  BITWISE_FLOAT_S_RELIABILITY    = 7     # s_reliability_q05 >= 7  → bit-for-bit (float)
  ```

**Commits**（拆 2 个，接在 A4.5 的 6 commits 之后）：
- `feat(scripts): s_req(N) = -log10(||E_trunc||) + 1 (truncation-anchored required sig digits)`
- `docs(week4): supervisor conclusion summary table (μ_trunc / σ_FP / s_worst_q05 / s_req / regime)`

#### A4.5 代码与产出

**新脚本**：

1. `scripts/snr_metric.py` — SNR 计算（先逐格 σ/μ → fields → global/median/q05 三 scalar）+ heatmap of SNR_local
2. `scripts/losos_metric.py` — LoSoS **三 field**（`s_reliability`, `s_accuracy`, `s_worst`）+ 每 field 三 scalar（min/q05/mean）+ 4-regime diagnostic（over-provisioned / well-matched / round-off-limited / truncation-limited，基于 `s_worst_q05 − s_req(N)` 的符号与量级）
3. `scripts/s_req_metric.py` — 从 `(solver, N)` 的 p=53 MCA mean 与 800² double reference 计算 `E_trunc(N) = ||μ − U_ref||_1 / ||U_ref||_1`，再给 `s_req(N) = -log10(E_trunc) + 1`
4. `scripts/pareto_plot.py` — Pareto frontier 图（使用 `SNR_global` × `s_worst_q05`），叠加 `s_req(N)` 水平虚线作为"目标带"参考
5. `scripts/tradeoff_summary_table.py` — A4.4 头版 table 生成器（见 §A4.4.3），调用 `s_req_metric.py` 算动态阈值
6. `tests/py/test_snr_operator_order.py` — **单测**：构造已知反例数据（空间反相关噪声），验证 `σ_WRONG ≈ 0` 但 `||σ_FP||_1 > 0`，防止未来改动把正确顺序改回错误
7. `tests/py/test_losos_three_fields.py` — **单测**：(a) `s_worst ≤ s_reliability` 与 `s_worst ≤ s_accuracy` 处处成立；(b) 构造 `σ_FP ≈ 0` 但 `μ_sample ≠ U_ref` 的反例，断言 `s_reliability` 很高而 `s_accuracy` 很低（诊断正确分离 reliability vs accuracy）
8. `tests/py/test_s_req_scaling.py` — **单测**：构造已知 `E_trunc(N) ∝ Δx` 的合成数据，验证 `s_req(2N) − s_req(N) ≈ log10(2) ≈ 0.3`，防止 s_req 公式符号或 log 底数回归

**数据源**：
- 1D: Week 3 已有的 VPREC sweep（48→16 位，5 samples/level）；为统计有效性需补跑到 30 samples/level（本地 1D 即可，~2 小时）
- 2D: A3 的 30-sample MCA 结果（HLLC + Rusanov × LW Config 3）

**新文件**（全部定位为 **Raw Data Log / Experiment Summary**，非 Report 1 章节素材）：
- `scripts/snr_metric.py`
- `scripts/losos_metric.py`
- `scripts/pareto_plot.py`
- `scripts/tradeoff_summary_table.py`
- `scripts/_tradeoff_thresholds.py` — 集中管理 4 个阈值常量（coding guidance §1：避免 magic number）
- `docs/week4/tradeoff_analysis.md` — **Raw Data Log 格式**：顶部 = §A4.4 头版 table + 结论陈述；中部 = 3-field LoSoS table（9 列，附录性质）+ Pareto 图 + `p_req` table；底部 = 方法论声明 "why SNR/LoSoS, not S=E+ασ"（引用 §A4.0 rationale，不重复推导）

**关键 design decision 声明**：
`tradeoff_analysis.md` 底部的方法论段落明确声明"为何放弃 `S = E + α·σ` 的线性相加方案"，让导师看到我们转向标准信号处理工具——这是对其"I'm not sure how to balance these" 的**方法论答复**。但声明控制在 ≤ 半页，不做 Report 1 级别的完整数学推导（Report 1 的 mathematical theory 章节在 Week 8-9 单独撰写，本周不预产素材）。

**Commits**（6 个）：
1. `feat(scripts): SNR metric with field-first operator order (σ per cell, then spatial L1/median/q05)`
2. `test(scripts): regression guard against std-L1 operator swap in SNR computation`
3. `feat(scripts): LoSoS 3-field output (s_reliability / s_accuracy / s_worst) + p_req table`
4. `test(scripts): LoSoS 3-field invariants (s_worst = min of reliability/accuracy)`
5. `feat(scripts): Pareto frontier plot using SNR_global × s_worst_q05`
6. `docs(week4): raw data log — SNR/LoSoS + 3-field rationale + operator non-commutativity note`

**验收**：
- 五脚本（`snr_metric.py` / `losos_metric.py` / `s_req_metric.py` / `pareto_plot.py` / `tradeoff_summary_table.py`）+ 三单测（`test_snr_operator_order.py` / `test_losos_three_fields.py` / `test_s_req_scaling.py`）产出 SNR table、LoSoS **3-field** table（`s_reliability`, `s_accuracy`, `s_worst` × min/q05/mean = 9 列）、`s_req(N)` table、Pareto 图（含 `s_req(N)` 目标带）、**头版 conclusion table**
- `test_losos_three_fields.py` 绿；`s_worst ≤ min(s_reliability, s_accuracy)` 逐 cell 全场成立
- `docs/week4/tradeoff_analysis.md` 作为 **Raw Data Log**：以 §A4.4 头版 table + ≤ 100 字结论开头；方法论声明 ≤ 半页；不做 Report 1 级别推导

---

## 4. Phase B — Week 4 本职（overall.md 266–275 行）（04/30 → 05/03）

### B1. `cmake/PrecisionConfig.cmake` + explicit instantiation + 分离编译（1 天，04/30–05/01）

**目的**：overall.md Week 4 line 268 原文：
> `Template solver for float and double (explicit instantiations in euler_solver.cpp)`

严格执行此指令——**放弃 header-only**，把 `EulerSolver` class 的长方法定义下沉到新 `src/euler/euler_solver.cpp`，在文件末尾显式实例化 `float` 和 `double` 两个版本。这带来四个好处：

1. **编译时间**：solver 代码只编译一次（per precision），而不是每个 TU 重复 instantiate（单测文件就有 6 个 TU）
2. **精度严格控制**：若试图用 `EulerSolver<long double>`，link error 立即出现，而不是神秘的 template-deduction error
3. **诚实的 "precision build"**：`build-float` 产物就是**真的只含 float 代码**的二进制，不再有"header 里两精度都 available 只看 main.cpp typedef 决定"的虚假分离
4. **符合 overall.md 明文要求**，为 Report 1 的 "code description (ease-of-implementation features)" 章节提供真实的 design decision 叙事

**保持 header-only 的**：`hllc_flux`, `rusanov_flux`, `muscl_reconstruct_*`, `muscl_hancock_*`, `euler_flux_*`, `exact_riemann_sample` 等 **free function templates**。原因：
- 单测直接测这些函数，分离 .cpp 反而需要更多 `template` instantiation 模板
- 它们是小函数，header-only 的编译时间 cost 可接受
- 它们被 GPU kernels 复用（Week 5+），必须 header-only

**只对 `EulerSolver` class 做 explicit instantiation**。

#### B1.1 新文件：`cmake/PrecisionConfig.cmake`

```cmake
# ------------------------------------------------------------------------
# PrecisionConfig.cmake -- selects the Real type for the HRSC project.
#
# Supported: float, double.
# Quad (long double / __float128) deferred to Week 17 per overall.md:
# it needs Boost.Multiprecision or libquadmath wiring and is 1D-CPU-only.
#
# Usage:  cmake -B build -DFLOAT_PRECISION=float ...
# ------------------------------------------------------------------------

set(FLOAT_PRECISION "double" CACHE STRING
    "Floating-point precision for the solver: float | double")
set_property(CACHE FLOAT_PRECISION PROPERTY STRINGS float double)

if(NOT FLOAT_PRECISION STREQUAL "float" AND
   NOT FLOAT_PRECISION STREQUAL "double")
    message(FATAL_ERROR
        "FLOAT_PRECISION must be 'float' or 'double' (got '${FLOAT_PRECISION}')")
endif()

# Expose the choice to C++ as a compile definition, used by main.cpp:
#   using Real = HRSC_REAL;
target_compile_definitions(hrsc_core INTERFACE HRSC_REAL=${FLOAT_PRECISION})
target_compile_definitions(hrsc_core INTERFACE HRSC_PRECISION_NAME="${FLOAT_PRECISION}")

message(STATUS "HRSC precision: ${FLOAT_PRECISION}")
```

#### B1.2 拆分 `src/euler/euler_solver.hpp` → .hpp + .cpp

**`src/euler/euler_solver.hpp`**（保留 class 声明 + 短/inline 方法）：

```cpp
#pragma once
#include "..."  // unchanged includes
#include "core/types.hpp"   // brings in TimeReal typedef (see §B1.2)

namespace hrsc {

enum class FluxScheme { HLLC, Rusanov };

template <typename Real>
class EulerSolver {
    Grid2D<Real, EulerNVars> m_grid;
    Real m_xmin, m_ymin, m_gamma, m_cfl;                   // spatial / state — follow Real
    TimeReal m_t_end, m_time, m_kahan_c;                   // time accumulator — ALWAYS double (see §B1.2)
    int  m_step;
    FluxScheme m_flux;

    void x_sweep(TimeReal dt);         // declared, defined in .cpp
    void y_sweep(TimeReal dt);         // declared, defined in .cpp

public:
    // Constructors (short, inline in header — needed by call sites)
    EulerSolver(int nx, int ny, Real dx, Real dy, Real xmin, Real ymin,
                Real gamma, Real cfl, TimeReal t_end,
                FluxScheme flux = FluxScheme::HLLC);

    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, TimeReal t_end,
                FluxScheme flux = FluxScheme::HLLC);

    // Trivial accessors remain inline
    GridView<Real, EulerNVars> grid_view() { return m_grid.view(); }
    TimeReal time()       const { return m_time; }         // double regardless of Real
    int      step_count() const { return m_step; }
    Real     xmin()       const { return m_xmin; }
    Real     ymin()       const { return m_ymin; }

    // Longer methods -- defined in .cpp to benefit from explicit instantiation
    TimeReal compute_dt() const;                           // returns double; caller passes to x/y_sweep
    void step();
    void run();
};

} // namespace hrsc
```

##### B1.2 `TimeReal = double`：时间累加器独立于 Real（防止 float 精度下 "大数吃小数"）

**Bug**（rewrite v5 修正）：若 `m_time` 跟随 `Real` 模板化，float32 精度下时间累加会在长演化问题上静默丢失步长：

```
float32 eps ≈ 1.19e-7
在 t ≈ 0.25 时，m_time 的 ULP ≈ 3e-8
在 t ≈ 0.90 时，m_time 的 ULP ≈ 1.2e-7

LW Config 3 @ 800² × t_end=0.5：
    dt ~ 5e-5  →  约 10000 steps
    在 t ≈ 0.9 时 dt 与 ULP 同量级  →  m_time += dt 可能零增量  →  simulation 时间停滞
```

**修正 — 时间变量统一为 `double`，独立于 state 数组的 Real**：

```cpp
// src/core/types.hpp（新增）
#pragma once
namespace hrsc {
    // State arrays follow the template precision (float / double).
    // Time accumulator is ALWAYS double, independent of Real, because:
    //   (1) t_end, dt, m_time only accumulate; their round-off dominates
    //       over state round-off for long evolutions.
    //   (2) float32 eps ≈ 1.2e-7 causes "large-number-eats-small" in
    //       m_time += dt once t > ~0.25 and dt ~ 1e-7. Classical bug.
    //   (3) double precision for time costs 8 bytes of solver state per
    //       time-step — negligible vs O(N²) state array.
    // This does NOT violate overall.md "template solver for float/double":
    // the STATE is templated; the TIME ACCUMULATOR is a separate concern.
    using TimeReal = double;
}
```

**dt 的精度推广**：`compute_dt()` 内部计算 `dt = cfl * min(dx / (|u| + c))`，其中 `u, c` 是 `Real`，`cfl, dx` 是 `Real`。表达式乘除后转 `TimeReal`：

```cpp
template <typename Real>
TimeReal EulerSolver<Real>::compute_dt() const
{
    Real max_speed(0);
    for (auto& cell : m_grid) {
        Real c = sound_speed(cell, m_gamma);
        Real u = std::abs(cell[RHOU] / cell[RHO]);
        max_speed = std::max(max_speed, u + c);
    }
    // Cast to TimeReal AT the point of accumulation. The multiplication
    // stays in Real (matching state precision); only the final time-step
    // value is stored as double. `-Wdouble-promotion` will not trigger
    // because the cast is explicit.
    return static_cast<TimeReal>(m_cfl * m_grid.dx / max_speed);
}
```

**Real / TimeReal 边界约定**（避免 `-Wdouble-promotion` 警告与模板歧义）：

`x_sweep` / `y_sweep` 接口声明为 `TimeReal dt`（来自 `compute_dt()` 的 double），但内部调用 `hancock_half_step<Real>(...)` / `muscl_reconstruct_x<Real>(...)` 等 free function template 期望 `Real dt`。在 sweep 入口做**唯一一次**显式降精度：

```cpp
template <typename Real>
void EulerSolver<Real>::x_sweep(TimeReal dt)
{
    // Down-cast at sweep entry: state updates use Real-precision dt.
    // Time-accumulator precision is preserved by m_time (TimeReal) in step();
    // within a single sweep the dt * (flux derivative) term is local and
    // Real-precision is sufficient — no accumulation inside one step.
    const Real dt_real = static_cast<Real>(dt);

    // Now all internal calls pass dt_real (Real), unchanged from Week 3 code.
    muscl_hancock_x(m_grid.view(), dt_real, m_grid.dx, m_gamma, m_flux);
    // ...
}
```

这一行 cast 是 `TimeReal` 设计与既有 `<Real>` 模板 free function 的唯一耦合点。Week 3 所有 flux / reconstruction 代码一行不动。

**Kahan compensated summation**（零成本强化，可选）：

```cpp
template <typename Real>
void EulerSolver<Real>::step()
{
    TimeReal dt = compute_dt();
    if (m_time + dt > m_t_end) dt = m_t_end - m_time;

    x_sweep(dt);
    y_sweep(dt);

    // Kahan compensated summation: keeps full double precision even for
    // ~1e8 accumulations. m_kahan_c is the running "lost bits" correction.
    TimeReal y = dt - m_kahan_c;
    TimeReal t_new = m_time + y;
    m_kahan_c = (t_new - m_time) - y;    // catches the lost low bits
    m_time = t_new;

    ++m_step;
}
```

对 Week 4 的 200² × t_end=0.3 (~600 steps) 这是 overkill；但为 Week 5+ 的 800² 长演化、GPU mixed-precision 和 Week 12 MHD 提前埋好。实现成本：3 行代码 + 1 个成员变量。

**向后兼容性验证**（加入 §9 acceptance）：
- Sod 1D double bit-identical 回归：m_time 改 double 后产出应与 Week 3 完全一致（double == TimeReal 时无任何数值差异）
- float 回归：新增单测 `test_time_accumulator_precision.py` 跑 `t_end=10.0` × `dt=1e-6` 的合成 case，断言 `m_time ≈ 10.0` 到 1e-10（double 精度应 PASS，若不走 TimeReal 的 float 实现应 FAIL）

**新 `src/euler/euler_solver.cpp`**（方法定义 + 实例化）：

```cpp
#include "euler/euler_solver.hpp"

namespace hrsc {

template <typename Real>
EulerSolver<Real>::EulerSolver(int nx, int ny, Real dx, Real dy,
                                Real xmin, Real ymin,
                                Real gamma, Real cfl, TimeReal t_end,
                                FluxScheme flux)
    : m_grid(nx, ny),
      m_xmin(xmin), m_ymin(ymin),
      m_gamma(gamma), m_cfl(cfl),
      m_t_end(t_end), m_time(TimeReal(0)), m_kahan_c(TimeReal(0)),
      m_step(0), m_flux(flux)
{
    m_grid.dx = dx;
    m_grid.dy = dy;
}

template <typename Real>
EulerSolver<Real>::EulerSolver(int nx, Real dx, Real xmin,
                                Real gamma, Real cfl, TimeReal t_end,
                                FluxScheme flux)
    : EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end, flux)
{}

template <typename Real>
void EulerSolver<Real>::x_sweep(TimeReal dt) { /* ... moved from header ... */ }

template <typename Real>
void EulerSolver<Real>::y_sweep(TimeReal dt) { /* ... moved from header ... */ }

template <typename Real>
TimeReal EulerSolver<Real>::compute_dt() const { /* ... moved from header ... */ }

template <typename Real>
void EulerSolver<Real>::step() { /* ... moved from header ... */ }

template <typename Real>
void EulerSolver<Real>::run() { /* ... moved from header ... */ }

// ========================================================================
// Explicit instantiations -- expose only float and double builds.
// long double / __float128 intentionally NOT instantiated (see overall.md
// quad-precision policy: 1D CPU only, Week 17 scope).
// ========================================================================
template class EulerSolver<float>;
template class EulerSolver<double>;

} // namespace hrsc
```

#### B1.3 CMake 分离库

**根 `CMakeLists.txt` 改动**：

```cmake
# ... existing include(cmake/PrecisionConfig.cmake)

# --- Separated Euler solver library (precision-controlled) ---
add_library(hrsc_euler STATIC src/euler/euler_solver.cpp)
target_link_libraries(hrsc_euler PUBLIC hrsc_core)

# --- Main executable ---
add_executable(hrsc src/main.cpp)
target_link_libraries(hrsc PRIVATE hrsc_core hrsc_euler)

# --- Unit tests ---
add_executable(unit_tests ${TEST_SOURCES})
target_link_libraries(unit_tests PRIVATE hrsc_core hrsc_euler)
```

**验证分离生效**：
```bash
cmake --build build-float --target hrsc_euler -- -v | grep -c "euler_solver.cpp"
# 应输出 1（只编译一次，证明 class 不再 header-only）
```

#### B1.4 `src/main.cpp` 修改

文件顶部：
```cpp
#ifndef HRSC_REAL
#define HRSC_REAL double   // fallback if built without PrecisionConfig
#endif

// Per overall.md "Precision-Generic Design": the build system selects one
// Real type per binary. All solver objects in main use this single type.
using Real = HRSC_REAL;
```

全文 `double` → `Real` 替换策略：
- `EulerSolver<double>` → `EulerSolver<Real>`
- `Vec<double, EulerNVars>` → `Vec<Real, EulerNVars>`
- `GridView<double, EulerNVars>` → `GridView<Real, EulerNVars>`
- 局部变量 `double gamma, cfl, ...` → `Real`
- **保留 `double`**：`cfg.get_double()` 返回 `double`，读入后 cast：`Real gamma = static_cast<Real>(cfg.get_double("gamma", 1.4))`
- **保留 `double`**：`exact_riemann_sample()` 参考解永远双精度（reference 必须最准），数值解与之对比时把数值 cast 到 `double`

#### B1.5 Unit tests

已用 `TEMPLATE_TEST_CASE(..., float, double)` 在两精度下运行（bridge §1.5 已验证），单测**不需要改**。编译时 unit_tests 链接 `hrsc_euler`，其包含的 `EulerSolver<float>` 和 `EulerSolver<double>` 实例化会被测试直接使用。

#### B1.6 约束与验收

**约束**：
- 无新增魔术数字
- `euler_solver.cpp` 末尾 explicit instantiation 行带注释解释 why（为什么不 `long double`）
- 注释：`main.cpp` 顶部加 3 行 why

**验收**：
```bash
cmake -B build-double -DFLOAT_PRECISION=double && cmake --build build-double
cmake -B build-float  -DFLOAT_PRECISION=float  && cmake --build build-float

# (1) 两个 build 都成功
build-double/unit_tests.exe   # >=112 cases pass
build-float/unit_tests.exe    # >=112 cases pass

# (2) Sod 端到端
build-double/hrsc tests/cases/toro_1d/sod.cfg > out_double.txt
build-float/hrsc  tests/cases/toro_1d/sod.cfg > out_float.txt

# (3) 分离编译已经生效
nm build-float/libhrsc_euler.a | grep "EulerSolver<float>::step"    # has symbol
nm build-double/libhrsc_euler.a | grep "EulerSolver<double>::step"  # has symbol
nm build-float/libhrsc_euler.a | grep "EulerSolver<double>::step"   # EMPTY (only float instantiated... wait: NO — we always instantiate both; the BUILD selects via HRSC_REAL which main.cpp uses, but library has both symbols)
```

**注意**：`euler_solver.cpp` 里 `template class EulerSolver<float>; template class EulerSolver<double>;` **都会** instantiate，不论 `HRSC_REAL` 是什么。这是设计：库始终支持两种精度，`HRSC_REAL` 只控制 main.cpp 用哪个。这样 unit_tests 的 `TEMPLATE_TEST_CASE(float, double)` 在任何 build 下都可运行。 `build-float` 和 `build-double` 的区别是 `hrsc` 二进制用哪个精度；库层面两者一致。

**Commits**（3 个）：
1. `refactor(euler): split EulerSolver into .hpp/.cpp with explicit instantiation for float and double`
2. `feat(cmake): PrecisionConfig module; separate hrsc_euler library; HRSC_REAL selects main.cpp precision`
3. `fix(euler): time accumulator uses TimeReal=double regardless of Real (prevents float32 clock stall)`

---

### B2. periodic + reflective BC（1 天，05/01）

**目的**：overall.md Week 4 第 2 项。当前 `boundary.hpp` 只有 `apply_outflow_bc`。Week 5 开始的 Kelvin-Helmholtz 需要 periodic；shock-bubble 可能需要 reflective。

**文件**：[src/core/boundary.hpp](../../src/core/boundary.hpp)（扩展，不重写）

**新接口（rewrite v5：flip_indices std::array，一次适配 Euler 与 MHD）**：

```cpp
// ----------------------------------------------------------------------
// Periodic BC: wraps physical cells [0, n) into ghost layers [-ng, -1]
// and [n, n+ng-1]. Applied independently on X and Y; 1D (ny=1) skips Y.
//
// Design note: periodicity is a pure copy -- no momentum sign change --
// so this overload is identical for Euler and MHD (no template NVars
// specialization needed).
// ----------------------------------------------------------------------
template <typename Real, int NVars>
void apply_periodic_bc(GridView<Real, NVars> grid);

// ----------------------------------------------------------------------
// Reflective (solid-wall) BC: mirrors physical cells into ghosts and
// negates ALL components whose variable index appears in flip_indices_x
// (x-boundary) and flip_indices_y (y-boundary).
//
// Physics-agnostic design: the BC routine knows nothing about "momentum"
// or "B field" -- it only knows which variable indices flip sign at a
// solid wall. This cleanly decouples the BC from the equation set:
//
//   Euler (NVars=4, flips normal momentum only):
//       apply_reflective_bc<Real, 4>(grid,
//           std::array{RHOU},                 // x-wall flips rho*u
//           std::array{RHOV});                // y-wall flips rho*v
//
//   MHD (NVars=9, flips normal momentum AND normal B):
//       apply_reflective_bc<Real, 9>(grid,
//           std::array{RHOU, BX},             // x-wall flips rho*u and Bx
//           std::array{RHOV, BY});            // y-wall flips rho*v and By
//
//   GLM-MHD (9+psi, if needed in Week 12): just extend the flip list.
//
// NFlipsX / NFlipsY are compile-time sizes → zero heap, zero branch on
// NVars inside the BC. The loop over flip indices is N_flips <= 3 in
// practice and the compiler unrolls it. Passing std::array{} (empty) is
// well-formed and skips all flips → degenerates to a pure mirror copy
// (useful for symmetric scalar fields, e.g. passive tracer validation).
// ----------------------------------------------------------------------
template <typename Real, int NVars,
          std::size_t NFlipsX, std::size_t NFlipsY>
void apply_reflective_bc(GridView<Real, NVars> grid,
                         const std::array<int, NFlipsX>& flip_indices_x,
                         const std::array<int, NFlipsY>& flip_indices_y);
```

**实现要点（mirror-then-flip 两阶段，保证可读 + 可 unroll）**：

```cpp
template <typename Real, int NVars,
          std::size_t NFlipsX, std::size_t NFlipsY>
void apply_reflective_bc(GridView<Real, NVars> grid,
                         const std::array<int, NFlipsX>& flip_indices_x,
                         const std::array<int, NFlipsY>& flip_indices_y)
{
    constexpr int ng = GridView<Real, NVars>::ng;
    const int nx = grid.nx, ny = grid.ny;

    // --- X boundaries: mirror, then flip the x-wall-normal variables ---
    for (int j = -ng; j < ny + ng; ++j) {
        for (int g = 1; g <= ng; ++g) {
            // Stage 1: pure mirror copy (same as reflective-for-scalars)
            for (int v = 0; v < NVars; ++v) {
                grid(-g,       j, v) = grid( g - 1,      j, v);
                grid(nx - 1 + g, j, v) = grid(nx - g,     j, v);
            }
            // Stage 2: flip signs on the listed indices only.
            // NFlipsX is constexpr → this loop is unrolled by the compiler.
            for (int v : flip_indices_x) {
                grid(-g,       j, v) = -grid(-g,        j, v);
                grid(nx - 1 + g, j, v) = -grid(nx - 1 + g, j, v);
            }
        }
    }

    // --- Y boundaries: same pattern with flip_indices_y ---
    // (1D case ny=1 still executes harmlessly; matches outflow precedent.)
    for (int i = -ng; i < nx + ng; ++i) {
        for (int g = 1; g <= ng; ++g) {
            for (int v = 0; v < NVars; ++v) {
                grid(i, -g,       v) = grid(i,  g - 1,    v);
                grid(i, ny - 1 + g, v) = grid(i, ny - g,   v);
            }
            for (int v : flip_indices_y) {
                grid(i, -g,       v) = -grid(i, -g,        v);
                grid(i, ny - 1 + g, v) = -grid(i, ny - 1 + g, v);
            }
        }
    }
}
```

- 与现有 `apply_outflow_bc` 的 loop 结构完全一致（外层 y、内层 var、`for g in 1..ng`）
- Periodic：`grid(-g, j, var) = grid(n - g, j, var)` 和 `grid(n - 1 + g, j, var) = grid(g - 1, j, var)`
- Reflective：**mirror-then-flip** 两阶段（见上），`NFlips` 编译期常数保证编译器展开 flip loop
- 角落 cell 处理：先做 X，再做 Y（与 outflow 一致，已被 test 覆盖）
- 1D 兼容：`ny=1` 时 Y-loop 的 ghost 填充仍执行（保持对称，已有 outflow 的先例）

**解耦优势（核心 rationale）**：

| 属性 | 旧签名 `int normal_x_index, int normal_y_index` | 新签名 `std::array<int, NFlipsX/Y>` |
|---|---|---|
| **向 MHD 的扩展** | 必须再加一对参数（`int normal_bx_index, int normal_by_index`），或写 overload，或在 enum 里加 `BoundaryType::ReflectiveMHD`——物理变了就改 BC signature | **签名不变**，调用端把 `{RHOU, BX}` 传进去即可 |
| **向 GLM / relativistic / multi-fluid** | 每加一种方程组就改一次 BC signature | 签名不变，flip list 延长即可 |
| **运行时开销** | 每 cell 2 个 `if (v == normal_index)` 分支 | `NFlips ≤ 3` 编译期常量，编译器 unroll；branch-free |
| **BC 对物理的依赖** | BC 必须"知道" momentum 是哪个变量（一种耦合） | BC 只接 index list，完全不知道物理含义（纯数学操作） |
| **单测简洁性** | 必须配合一个 Euler-specific 的 struct 才能测 | 传 `std::array<int, 0>{}` 可测 pure-mirror 情形；传任意 index list 测任意组合 |
| **`-1 sentinel`（skip axis）** | 旧接口靠魔术值 `-1` 表示"跳过"（magic number） | 新接口传空 `std::array<int, 0>{}`，或根本不调 apply_reflective_bc 的那一边（干净） |

这个签名是 **Week 12 MHD 对接的前置决定**：Week 4 定死之后 `src/mhd/mhd_solver.hpp` 不需要动 boundary layer，只需在调用点换 flip list。**不为 MHD 过度设计**（如 `enum class BoundaryType { ReflectiveMHD }`），但**留好扩展槽**——这是 coding guidance §5 "modularisation" 的精神。

**常量与魔术数字**：
- 所有循环用 `ng = GridView<Real, NVars>::ng`（= `NgHost` = 2）
- `Real(-1)` 不再需要（改用 unary `-`，C++ 会推导为 `Real(0) - x`；编译器优化等价，无 cast）
- 不存在 `-1 sentinel` for skip——传空 array 即是明示

**约束**：
- 不新增 cpp 文件（header-only 保留）
- `#include <array>` 加到 `boundary.hpp`（若尚未有）
- 在函数头部的 docblock 里解释 why：**为什么用 std::array 而不是 int, int**（列出上面解耦优势表作为摘要）

**B3 dispatcher 随动更新**：`apply_boundary` 的签名同步改成接收 `flip_indices_x / flip_indices_y`（在 B3 章节详述）；`EulerSolver` 内部在构造器里把 `{RHOU}` 与 `{RHOV}` 作为成员 `std::array` 固定下来，step() 内传给 dispatcher。

**单测（配合 B4）**：
- Pure-mirror：`apply_reflective_bc(grid, std::array<int,0>{}, std::array<int,0>{})` 应复制 ghost 而不翻任何符号
- Euler momentum flip：`{RHOU}, {RHOV}` → rho 不翻，rho*u 在 x-ghost 翻，rho*v 在 y-ghost 翻，E 不翻
- 多 index flip（模拟 MHD）：`{1, 5}, {2, 6}` → index 1,5 在 x-wall 翻；index 2,6 在 y-wall 翻；其余不动（这个 case 用 NVars=7 的 dummy 场跑，验证接口无 Euler 假设）

**验收**：见 B4 的单元测试

**Commit**: `feat(boundary): periodic BC + reflective BC with compile-time flip_indices array`

---

### B3. `BoundaryType` enum + cfg `bc_x`/`bc_y` + solver 集成（1 天，05/02）

**目的**：让 BC 类型**可配置**。当前 `EulerSolver::step()` hard-code `apply_outflow_bc`；需要通过 cfg 切换 outflow/periodic/reflective，**独立控制 X 和 Y 方向**（因为有些测试 X 是 periodic、Y 是 outflow）。

**实现偏离说明（Phase B 实际落地）**：最终没有引入这里规划的 `apply_boundary(...)` dispatcher 模板，而是采用了 `apply_outflow_bc/apply_periodic_bc/apply_reflective_bc` 的 per-axis 原语，由 `EulerSolver::apply_boundary_conditions()` 逐轴 `switch` 调度。该实现与计划目标等价且可直接扩展到 Week 12 MHD（`BoundaryType` 已上移到 `src/core/boundary.hpp` 供复用）；另外，`euler_solver.cpp` 中 Kahan 累加“中段”按数值稳定性优化，保持数值等价但不承诺跨平台/编译选项的 bitwise 一致。

**新文件/改动**：

1. `src/core/boundary.hpp` 加 enum + dispatcher（signature 与 B2 的 flip_indices 对齐）：
   ```cpp
   enum class BoundaryType {
       Outflow,
       Periodic,
       Reflective,
   };

   // Dispatcher applied per-axis; the solver calls this once per step() (handles both X and Y).
   // flip_indices_{x,y} only consulted when the corresponding axis is Reflective;
   // otherwise ignored (safe to pass empty arrays).
   //
   // Default template args NFlipsX=0 / NFlipsY=0 + default empty std::array
   // let outflow/periodic call sites stay uncluttered:
   //     apply_boundary(grid, Outflow, Outflow);                         // valid (no flips needed)
   //     apply_boundary(grid, Periodic, Periodic);                       // valid (no flips needed)
   //     apply_boundary(grid, Reflective, Reflective, {RHOU}, {RHOV});   // Euler
   //     apply_boundary(grid, Reflective, Reflective, {RHOU,BX}, {RHOV,BY}); // MHD
   template <typename Real, int NVars,
             std::size_t NFlipsX = 0, std::size_t NFlipsY = 0>
   void apply_boundary(GridView<Real, NVars> grid,
                       BoundaryType bc_x,
                       BoundaryType bc_y,
                       const std::array<int, NFlipsX>& flip_indices_x = std::array<int, 0>{},
                       const std::array<int, NFlipsY>& flip_indices_y = std::array<int, 0>{});
   ```
   实现里就是 `switch` 4 分支组合，调 A1/B2 的底层 BC。Euler 层面由 solver 在调用点固定传 `std::array{RHOU}` 与 `std::array{RHOV}`（见下）；dispatcher 本身不知道物理含义。

2. `src/euler/euler_solver.hpp`：
   - 构造器增加 `BoundaryType bc_x = BoundaryType::Outflow, BoundaryType bc_y = BoundaryType::Outflow` 参数（默认向后兼容）
   - 成员 `BoundaryType m_bc_x, m_bc_y;`
   - 成员 `static constexpr std::array<int, 1> FlipX = {RHOU};` 与 `static constexpr std::array<int, 1> FlipY = {RHOV};`（编译期常量，零开销）
   - `step()` 里把 `apply_outflow_bc(m_grid.view())` 三处调用都改成 `apply_boundary(m_grid.view(), m_bc_x, m_bc_y, FlipX, FlipY)`
   - 未来 `MHDSolver<Real>` 在同一个 dispatcher 上传 `std::array<int, 2>{RHOU, BX}` 与 `std::array<int, 2>{RHOV, BY}`，**不动 dispatcher 代码**

3. `src/main.cpp`：
   - 新增 `parse_bc()`：
     ```cpp
     static BoundaryType parse_bc(const std::string& s) {
         if (s == "outflow")    return BoundaryType::Outflow;
         if (s == "periodic")   return BoundaryType::Periodic;
         if (s == "reflective") return BoundaryType::Reflective;
         throw std::runtime_error("Unknown boundary type: " + s);
     }
     ```
   - cfg keyword resolution 逻辑（**决策顺序**）：
     1. 先读 `bc`（若缺省，default `"outflow"`）
     2. 再读 `bc_x`（若缺省，取 `bc` 的值）
     3. 再读 `bc_y`（若缺省，取 `bc` 的值）

     即 `bc` 是 shortcut，`bc_x`/`bc_y` 可单独 override。只写 `bc = periodic` 等价于 `bc_x = periodic, bc_y = periodic`。
   - `run_normal` / `run_convergence` 里读取并传入构造器

4. 所有现有 `.cfg` 不需改（默认 outflow 仍生效）。

**约束**：
- 不为 MHD 提前泛化（enum 里**不**加 `BoundaryType::GLMOutflow`）；Week 12 再在 MHD 代码里用同一 `BoundaryType` 但加一个 `mhd/mhd_boundary.hpp` 做 psi 特殊处理。现在**锁死** Euler enum 不动。
- BoundaryType enum class 的底层类型保持默认 `int`，Week 12 MHD 可以 `static_cast<int>(bc)` 做日志。

**新 cfg 示例**（Week 5 Kelvin-Helmholtz 用）：
```
test = kh
nx = 256
ny = 512
...
bc_x = periodic
bc_y = reflective
```

**验收**：
- Week 3 全部 cfg 不改动且继续绿
- 新增 `tests/cases/liska_wendroff_2d/config3.cfg` 用 `bc = outflow`
- 后续 Week 5 Kelvin-Helmholtz 可直接用 `bc_x = periodic, bc_y = reflective`

**Commit**: `feat(solver): configurable boundary conditions (bc_x/bc_y cfg keys)`

---

### B4. `test_boundary.cpp` 扩展（0.5 天，05/03）

**目的**：为 B2 / B3 加 Catch2 单测，覆盖 periodic wrap / reflective 法向翻转 / 1D + 2D 角落。

**文件**：[tests/unit/test_boundary.cpp](../../tests/unit/test_boundary.cpp)（扩展）

**新 TEST_CASE**：

```cpp
TEMPLATE_TEST_CASE("apply_periodic_bc wraps 1D ghost cells", "[boundary][periodic]", float, double) {
    // ... n=5, single row, fill with i+1, apply, check grid(-1,0,0)==5, grid(5,0,0)==1 ...
}

TEMPLATE_TEST_CASE("apply_periodic_bc wraps 2D ghost cells", "[boundary][periodic]", float, double) {
    // 5x5 with unique value per cell, check ghost = wrapped
}

TEMPLATE_TEST_CASE("apply_reflective_bc negates normal X momentum", "[boundary][reflective]", float, double) {
    // Fill RHOU with +1 everywhere, apply reflective with normal_x=RHOU,
    // Check ghost -1 has RHOU = -1, RHO stays +1
}

TEMPLATE_TEST_CASE("apply_reflective_bc negates normal Y momentum", "[boundary][reflective]", float, double) {
    // Same for RHOV and bottom/top ghosts
}

TEMPLATE_TEST_CASE("apply_boundary dispatcher: outflow+periodic", "[boundary][dispatcher]", float, double) {
    // Mixed: X=outflow, Y=periodic, check corners are outflow-copies of Y-periodic-wrapped row
}
```

**验收**：`build/unit_tests.exe "[boundary]"` 全绿；总 case 数 107 → 112 左右。

**Commit**: `test(boundary): unit tests for periodic and reflective BC (1D + 2D + dispatcher)`

---

## 5. Phase C — 依赖 Phase B 的导师要求（05/04 → 05/10）

### C1. float 精度全回归：6 × 1D Toro + 2D LW Config 3 + 相移分离（4 天，05/04–05/07）

**目的**：overall.md Week 4 requires "1D tests run in both float and double"，**同时** overall.md 整体架构明确 2D 也要 float vs double 对比。纯 1D 测试不能 exercise 2D 代码路径（`muscl_hancock_y`、`y_sweep`、`swap_momentum` 的 float 行为未经验证）。因此 C1 升级为**包含 2D LW Config 3**，与 1D Toro 一起走统一回归 harness。

#### C1.1 1D Toro 回归（6 cases）

**操作**：

1. 新建 `scripts/float_regression_1d.sh`：
   ```bash
   #!/usr/bin/env bash
   set -eu
   BUILD_FLOAT="build-float"
   BUILD_DOUBLE="build-double"
   TESTS=(sod toro2 toro3 toro4 toro5 stationary_contact)
   OUT="experiments/week4/float_regression/1d"
   mkdir -p "$OUT"
   for t in "${TESTS[@]}"; do
       # Use convergence cfg to auto-compute L1/L2/Linf vs exact
       "$BUILD_DOUBLE/hrsc" "tests/cases/toro_1d/convergence_${t}.cfg" \
           > "$OUT/${t}_double.csv"
       "$BUILD_FLOAT/hrsc"  "tests/cases/toro_1d/convergence_${t}.cfg" \
           > "$OUT/${t}_float.csv"
   done
   python scripts/float_regression_report.py --mode 1d --input "$OUT"
   ```

2. 新建 **缺的 convergence cfg**：Toro 2-5、Stationary Contact 需要各自 `convergence_{t}.cfg` + `convergence_{t}_rusanov.cfg`（10 个新 cfg）。
   - 模板：从 `convergence_sod.cfg` 复制，改 `test` 和 `t_end`；`resolutions = 50,100,200,400,800`
   - Toro 4 blast 的 t_end 小、CFL 要降

**参考解**：1D 有 exact Riemann（Week 3 已有 `exact_riemann_sample`），直接做 L1/L2/Linf。

#### C1.2 2D LW Config 3 回归（新加入）

2D 无 exact 解析解，必须用 **high-resolution double-precision reference**（overall.md line 183）。

**策略**：

1. **生成 reference**：`build-double/hrsc` 跑 LW Config 3 at **800×800**（4 倍精细于测试分辨率），保存为 `experiments/week4/float_regression/2d/reference_800.bin`。耗时 ~20–40 分钟（本地可接受）。

2. **生成候选**：
   - `build-double` at 200×200 → `dot_200.bin`（测试 4x truncation）
   - `build-float` at 200×200 → `float_200.bin`
   - `build-double` at 400×400 → `dot_400.bin`
   - `build-float` at 400×400 → `float_400.bin`

3. **降采样比较**：`scripts/downsample_2d.py`
   - 读 800×800 reference，块平均（4×4 → 1 或 2×2 → 1）降采样到目标分辨率
   - 保守策略：用守恒量的 cell-averaged 降采样（`rho` 守恒），保持 FV 一致性
   - 对每对 (候选, 降采样 reference) 计算 L1/L2/Linf × {rho, u, v, p}

4. **2D 回归脚本** `scripts/float_regression_2d.sh`：
   ```bash
   #!/usr/bin/env bash
   set -eu
   BUILD_FLOAT="build-float"; BUILD_DOUBLE="build-double"
   OUT="experiments/week4/float_regression/2d"
   mkdir -p "$OUT"

   # Reference
   "$BUILD_DOUBLE/hrsc" tests/cases/liska_wendroff_2d/config3_ref800.cfg
   mv output/grid.bin "$OUT/reference_800.bin"

   for res in 200 400; do
       "$BUILD_DOUBLE/hrsc" "tests/cases/liska_wendroff_2d/config3_n${res}.cfg"
       mv output/grid.bin "$OUT/double_${res}.bin"
       "$BUILD_FLOAT/hrsc"  "tests/cases/liska_wendroff_2d/config3_n${res}.cfg"
       mv output/grid.bin "$OUT/float_${res}.bin"
   done

   python scripts/float_regression_report.py --mode 2d --input "$OUT"
   ```

5. **新 cfg 文件**：
   - `tests/cases/liska_wendroff_2d/config3_n200.cfg` — `nx=ny=200`
   - `tests/cases/liska_wendroff_2d/config3_n400.cfg` — `nx=ny=400`
   - `tests/cases/liska_wendroff_2d/config3_ref800.cfg` — `nx=ny=800`（参考用，建议 `cfl=0.4` 更稳）

**注意**：Config3 at 800×800 在 double 下大约 1e6 cells × ~2000 steps = 2e9 cell-updates，约 20–40 分钟 single-core。若超 1 小时，把 reference 降到 600×600 即可（N/4 仍然足够精细于 200）。

#### C1.2.5 相移误差分离（Phase Error Separation）

**动机**：L1 / L2 / Linf 对激波 **双重惩罚**——若 float 解的主激波比 reference 晚 1 个 cell，L1_rho 会按 ≈ `2 · |[ρ]|_jump · Δx` 计算，既罚"reference 位置没有 shock"又罚"float 位置多出 shock"。这使得"float 的激波位置稍偏但幅值正确"和"float 的激波位置正确但幅值错"**完全无法区分**。对 LW Config 3 这种含 4 个象限 slip line + 多激波的 2D 场，传统范数几乎必然误判。

**解法（两种并列报告）**：

##### (i) 激波坐标追踪（Shock coordinate tracking）

适用：主激波位置相对明显的 slice。

```python
def track_shock_1d(rho_slice: np.ndarray, x: np.ndarray,
                   threshold_frac: float = 0.5) -> float:
    """对 1D slice（y=0.5 或 x=0.5），高斯平滑后找 |dρ/dx| 最大点作为 shock 位置。"""
    rho_smooth = gaussian_filter1d(rho_slice, sigma=0.5)
    grad = np.abs(np.gradient(rho_smooth, x))
    # threshold_frac of max to avoid spurious noise peaks
    mask = grad > threshold_frac * grad.max()
    # weighted centroid inside the peak region
    return np.sum(x[mask] * grad[mask]) / np.sum(grad[mask])
```

对 LW3：取 y=0.5 slice 追水平激波，x=0.5 slice 追垂直激波，共 2 个坐标。

**输出**：
```
Test = LW Config 3
                         float 200²  double 200²  float 400²  double 400²
x_shock (y=0.5)          0.7123      0.7145       0.7132      0.7148     (ref 0.7151)
y_shock (x=0.5)          0.2881      0.2862       0.2873      0.2860     (ref 0.2858)
Δx_shock (float - ref)   -0.0028     -0.0006      -0.0019     -0.0003
```

直观告诉导师："float 200² 的激波位置比 reference 偏移 ≈ 0.3%，double 200² 偏移 ≈ 0.06%。"

##### (ii) SSIM 单 scalar（rewrite v5.1：lean 路线，取代 axis-aligned W1，三因子分解延后 Report 2）

适用：全场定量比较，不依赖人工挑 shock，**原生支持 2D 不需要投影**。

**为何废弃 axis-aligned W1（前一版方案）**：

先前 v4 的 axis-aligned W1 方案仅在**激波法向严格与 x 或 y 轴对齐**时成立。LW Config 3 的 4-shock axis-aligned 结构勉强适用，但一旦考虑 Mach stem / 斜激波 / 滑移线，沿 `axis=0` 求和会把整条斜激波 smear 成 1D 分布里的一个宽峰——相移与幅值信息同时丢失，Δx_shock 无法从投影里恢复。Sliced-W1 的 Cartesian 离散化 aliasing 问题也未解决。结论：W1 作为 1D 的 phase-shift metric 很优秀，但**搬到 2D 上没有干净的实现**。

**替代方案（lean）— SSIM 单 scalar**：

SSIM（Wang et al. 2004, *IEEE T-IP*）是图像质量评估的标准工具，直接作用于 2D 场（不需要投影或插值），其局部形式按 Gaussian window 滑动计算，结果是一个 `[-1, 1]` 之间的标量，`1` 表示两场同一。原理上可分解成 luminance × contrast × structure 三个正交因子对应 conservation × amplitude × phase，但**本 week 只用单 scalar 作 L1 的补充指标**——完整三因子分解列入 **Report 2 Future Work**。

**实现（3 行代码，直接调 skimage）**：

```python
# scripts/phase_error_metrics.py
from skimage.metrics import structural_similarity

def ssim_scalar(a: np.ndarray, b: np.ndarray, data_range: float) -> float:
    """Standard SSIM as a single scalar. Higher = more similar, 1.0 = identical.

    Wang et al. 2004 defaults (11x11 Gaussian window, K1=0.01, K2=0.03).
    Returns the global SSIM mean; per-cell map + 3-factor decomposition
    (luminance / contrast / structure) deferred to Report 2 Future Work.
    """
    return float(structural_similarity(a, b, data_range=data_range,
                                       gaussian_weights=True, sigma=1.5))
```

**data_range**：`field_ref.max() - field_ref.min()`（与图像像素 `255` 角色一致）。

**skimage 依赖**：本 week 确认 CSC module + 本地 WSL Docker 均可用；若 skimage 不可用则退化到裸 L1 + heatmap（在 `phase_error_metrics.py` 入口 try-import，fallback 时在 summary.md 顶部打一行 WARN）。

##### 统一输出

`scripts/phase_error_metrics.py`：
- 输入：两张 2D 场（candidate + reference，**相同分辨率**——通过 `downsample_2d.py` 预处理到同大小）
- 输出 table：
  ```
  metric                float_200   double_200   float_400   double_400
  L1_rho                2.34e-2     8.11e-3      1.02e-2     3.42e-3
  ssim_rho              0.9812      0.9965       0.9903      0.9987        ← 值越接近 1 越相似
  Δx_shock (y=0.5)      2.8e-3      6.0e-4       1.9e-3      3.0e-4
  Δy_shock (x=0.5)      2.3e-3      4.0e-4       1.5e-3      2.0e-4
  ```
  外加 4 张 2D 差值 heatmap（candidate − reference），与 L1 数值并列——**肉眼判读**哪些 cell 误差主导。

**集成**：`float_regression_report.py --mode 2d` 调用 `phase_error_metrics.py`，在 `summary.md` 里同时列出 L1 + SSIM + 激波坐标 + heatmap。

**Future Work 备注**（写入 `docs/week4/float_vs_double_regression.md` 讨论小节）：

> 注：L1 范数在激波问题上会受到双重惩罚（reference 位置无 shock + candidate 位置多 shock）；本 week 用 SSIM 单 scalar 作定性补充，相移与幅值的拓扑级分离（SSIM 三因子 luminance × contrast × structure、或 1D axis-aligned W1）留作 Report 2 Future Work 探索。

**依赖**：`skimage.metrics.structural_similarity`（新增 `scikit-image` 到 `requirements.txt`，MIT license，~60MB install）。

#### C1.3 统一 report 脚本

`scripts/float_regression_report.py`：
- `--mode 1d`：读 1D Toro CSV，per-test log-log error vs N 图，float/double 两条线
- `--mode 2d`：读 2D bin，画 density slice (y=0.5) float vs downsampled-reference，用 A2 的 `plot_divergence_marker` 在 `strict_fp` 模式下标 "x"
- 两模式都产出 `summary.md`：含 L1/L2/Linf 表 + float/double ratio

#### C1.4 结果呈现

`docs/week4/float_vs_double_regression.md`（统一 1D + 2D 报告）：
- Section 1: 1D Toro 6 case summary（convergence rate + float/double ratio）
- Section 2: 2D LW Config 3（slice 比较 + downsampled norms）
- Section 3: 结论
  - 哪些测试 float 足够（truncation-dominated）
  - 哪些测试 float 出现明显精度丢失
  - 2D vs 1D 的 float 敏感度差异（回答导师 2026-04-17 "may become more obvious for more complex 2D simulations"）

**验收**：
- 12 份 1D CSV + 5 份 2D bin（ref + 4 候选）齐全
- 1D summary.md + 2D summary.md + `float_vs_double_regression.md` 合并报告
- float 和 double 二进制都能跑通 1D/2D 全部 case（无 crash/NaN）
- 2D reference 800×800 可视化密度场与 Liska-Wendroff (2003) Fig 3 视觉一致

**Commits**（6 个）：
1. `test(toro_1d): add convergence cfgs for toro2/3/4/5 + stationary_contact`
2. `test(lw_2d): add config3 regression cfgs (n=200, 400, ref 800)`
3. `feat(scripts): 2D downsampling helper for high-res reference comparison`
4. `feat(scripts): shock-tracking + SSIM 3-factor phase-vs-amplitude decomposition (luminance/contrast/structure)`
5. `feat(scripts): unified float-vs-double regression harness (1D + 2D)`
6. `docs(week4): float vs double regression report (with phase/amplitude split)`

---

### C2. Verificarlo 真·float 编译（1.5 天，05/08–05/10）

**目的**：Week 3 的 Verificarlo 通过 VPREC p24 **模拟** float 精度；现在 B1 完成后，可以让 Verificarlo 直接编译**真正的 float 代码**（即 `FLOAT_PRECISION=float` + verificarlo 的 MCA 后端），对比 VPREC 模拟与真 float 的 MCA noise 差异。

**改动**：

1. `scripts/verificarlo/verificarlo_run.sh` 扩展：
   - 新增 flag `--real-float`：若设，执行 `CXX=verificarlo-c++ cmake -B hrsc_vfc -DFLOAT_PRECISION=float ...`
   - 否则保持现状（`FLOAT_PRECISION=double` + VPREC 后端模拟 p=24）
   - 新增 flag `--compare-float`：两次都跑，输出到不同子目录 `real_float/` 和 `vprec_p24/`

2. 新脚本 `scripts/figures/plot_real_vs_vprec.py`：
   - 读两份 MCA 结果
   - 逐 cell 对比 mean + stddev
   - 出图：y=cells, x=significant digits, 两条 (real-float, vprec-p24) 叠加
   - 结论应该是：两者几乎一致（VPREC 是 valid float simulation），任何差异说明 VPREC 模拟有偏差

3. 跑一遍 Sod + Stationary Contact 两个 case（Toro 4 开销太大，留给 Week 5 以后）

**结果文档**：`docs/experiment_logs/c2_real_float_vs_vprec.md`

**验收**：
- Verificarlo 在 `FLOAT_PRECISION=float` 下编译成功（可能需要调 Verificarlo 的 `--inst-func` interaction，见 Week 3 VPREC bug note）
- 两份 MCA 结果产出
- 对比图清晰

**风险**：
- Verificarlo + float 编译可能触发 Week 3 记录过的 `VPREC + --inst-func` 崩溃类似的 bug。如果 48 小时内无法解决 → 降级：仍用 VPREC p24 但在 report 中明确标注"direct float compilation failed due to Verificarlo-compiler interaction"，把 bug 写成 future work。
- 时间预算给 1.5 天。

**Commits**：
1. `feat(scripts): Verificarlo real-float build support (--real-float flag)`
2. `docs(week4): real float compile vs VPREC p24 simulation comparison`

---

## 6. Git 策略

### 6.1 分支

- **源分支**: `week3-implementation`（当前）
- **目标分支**: `week4-implementation`（新建，off `week3-implementation`）
- 所有 Week 4 工作在 `week4-implementation` 上，**不回头改** `week3-implementation`
- 最终完成（Phase C 结束）后统一 PR 到 `main`

### 6.2 Commit 粒度

- **1 个子项 ≈ 1 个 commit**（小项）或 **一组相关 commits**（大项如 A3、C1）
- 每个 commit 前单测必须绿（Phase B1 一个 commit，但实际 build 要跑两次 cmake）
- 不 squash；保留 chronological history 方便 Week 5+ 的 `git bisect`

### 6.3 Commit message 风格

Conventional commits（与 Week 3 风格一致）：
- `feat(<scope>): ...`
- `fix(<scope>): ...`
- `test(<scope>): ...`
- `docs(<scope>): ...`
- `refactor(<scope>): ...`
- `chore(<scope>): ...`

Scopes: `solver`, `cmake`, `boundary`, `scripts`, `tests`, `docs`, `build`。

### 6.4 不进 Git 的产物

已经在 `.gitignore`：
- `/hrsc_vfc`
- `/build*`（`build-float`, `build-double` 都自动命中）
- `*.o`, `*.exe`
- `experiments/**/samples/**`（MCA 原始数据太大）

**本计划新增**需要加进 `.gitignore`：
- `experiments/week4/vfc_2d/samples/` — 2D MCA 30 samples × 200² × double = 每次 GB 级
- `experiments/week4/vfc_2d/logs/` — SLURM stdout / stderr（保留少量到 `docs/week4/` 作证据）
- `experiments/week4/noise_floor/**/sample_*.txt` — A2 的每 30-sample 原始文本（~100 MB/份 × 8 份）；**保留** `noise_floor.npz`（聚合后 MB 级）与 `seeds.csv`（KB 级）
- `experiments/week4/float_regression/npz/` — 2D 解场 `.npz` (~60 MB/份)
- `experiments/week4/float_regression/*.csv` 保留（~KB），`.png` 保留
- `build-float/`, `build-vfc-p53/`, `build-vfc-real/` — Week 4 新增的平行 build 目录（A2 MCA p=53 build + C2 real-float build）

### 6.5 避免回归

- 每个 Phase 结束（A 完、B 完）跑一次 `build-double/unit_tests.exe` + `build-float/unit_tests.exe` 全跑，确认 112+ cases 绿
- **B1 完成后**（explicit instantiation 迁移）立即跑全端到端 Sod double，与 Week 3 最终版 `diff` 为 0；若有差异（即便是 ULP 级），必须在 commit message 里记录原因或回滚
- Phase B 完成后跑一次完整 Sod 端到端 double + float，对比之前 Week 3 的输出（应当 **double 完全一致**，float 是新 baseline）
- A3 的 SLURM 任务返回前，不进入 A4 代码实现；feasibility (100²×5) 跑完后才 sbatch production (200²×30)，防止 wall-clock 估错

---

## 7. Phase 2 接口锁定（与 Week 5+ 的对接）

### 7.1 Week 5: 2D tests + GPU start

- Liska-Wendroff Config 3 的 IC 在 Phase A3 中已实现，Config 6 已声明；Week 5 直接补 Config 6 实现
- Kelvin-Helmholtz、shock-bubble 需要 `BoundaryType::Periodic` 和 `BoundaryType::Reflective` — Phase B3 已就绪
- GPU 路径复用 `HRSC_REAL` typedef；`gpu/euler_kernels.cuh` 里的 kernel 模板参数 `Real` 直接用

### 7.2 Week 6: GPU 完整 Euler solver

- GPU 版 `apply_boundary` kernel 复用相同的 enum `BoundaryType`
- GPU kernel 的 reflective 需要同样的 `normal_x_index` 参数

### 7.3 Week 12: MHD Solver

- `BoundaryType` enum 不加分支；MHD 的 `apply_boundary_mhd` 接受额外的 `normal_bx_index, normal_by_index`
- `EulerSolver<Real>` 的构造器签名 (bc_x, bc_y) 会被 `MHDSolver<Real>` 参考，但 MHD 多一个 GLM psi 的 BC，MHD 构造器签名独立

### 7.4 Week 15-17: 系统性精度扫描

- `FLOAT_PRECISION={float, double}` × `RIEMANN_STRICT_INEQUALITY={ON, OFF}` × `solver={hllc, rusanov}` × `bc={outflow,periodic,reflective}` 的 build matrix 已全通过 CMake options / cfg keywords 暴露
- `scripts/build_all.sh`（Week 7）只需 loop cmake options 即可

### 7.5 接口 checklist（完成后勾选）

- [x] `HRSC_REAL` 宏在所有 `#include` 之前定义
- [x] `BoundaryType` enum 类的底层类型固定 (`enum class BoundaryType` 默认 `int`，不改)
- [x] 采用 per-axis BC primitive + flip-index 列表（MHD 可复用），替代原单入口 `apply_boundary(..., sentinel)` 设计
- [ ] 所有新 cfg keywords (`bc`, `bc_x`, `bc_y`) 在 `docs/week4/cfg_reference.md` 记录
- [x] Liska-Wendroff header `lw_tests.hpp` 声明 Config 6 让 Week 5 直接填

---

## 8. 日历排期

| 日期 | 周几 | Phase | 子项 | 本地/集群 | Deliverable |
|---|---|---|---|---|---|
| 04/22 | Wed | A | A1 + A2-S1 + A2-S2 kickoff | WSL + Docker | default Rusanov 完成；**A2 Stage 1** `--mode visible` rel_tol=1e-3 先出 8 张带 x 标记图并回复导师邮件；`noise_floor_run.sh` 写完；Stage 2 overnight batch 启动 |
| 04/23 | Thu | A | A2-S2 batch + A3 kickoff | WSL + Docker | 8 次 noise-floor run (sod, sc, toro2, toro4) × (hllc, rusanov) × 30 samples overnight 跑完；`plot_divergence_marker.py` 三 mode 实现；LW3 IC + cfg |
| 04/24 | Fri | A | A2-S2 完（补发图） + A3 smoke | WSL + Docker | 8 张 noise_floor-mode 图 + `k_grad` 拟合 + `noise_floor_calibration.md`；**S2 补发同一图给导师（MCA-calibrated 覆盖 S1）**；本地 40²×3 smoke（Docker，含 OMP_NUM_THREADS=1） |
| 04/25 | Sat | A | A3 feasibility + thread safety | WSL + Docker | 100²×5 feasibility；`2d_vfc_feasibility.md` 初稿；SLURM 脚本含 /dev/urandom seed + OMP_NUM_THREADS=1 block；§A3.3 thread-safety 写入 |
| 04/26 | Sun | A | A3 production submit | CSC | 两次 `sbatch --array=1-30`（HLLC + Rusanov）并发 60 tasks；每 task 写独立 `seeds/seed_NN.csv`（无 flock）+ sacct 监控启动；feasibility 外推 `t_{200²}` 写入 `2d_vfc_feasibility.md` |
| 04/27 | Mon | A | A3 监控 + A4.1 设计 | — / WSL | 集群跑（wall-clock ≈ `t_{200²}` + queue，单位小时级）；本地写 SNR field-first 公式文档 + 算子不可交换反例 |
| 04/28 | Tue | A | A3 收尾 + A4.1 代码 | WSL | 下载样本、seed 独立性校验（`check_seeds(expected_n=30)`）；`snr_metric.py` + 算子顺序回归测试 |
| 04/29 | Wed | A | A4.2 / A4.3 | WSL | `losos_metric.py`（**3-field**：reliability / accuracy / worst）+ `s_req(N)` 计算（基于 800² double reference）+ `pareto_plot.py`，heatmap 产出 |
| 04/30 | Thu | A→B | **A4.4 conclusion table + A4.5 代码** + B1 | WSL | `tradeoff_summary_table.py` 产出 7 列头版 table；`tradeoff_analysis.md` 作为 **Raw Data Log** 定稿；`PrecisionConfig.cmake` + `euler_solver.cpp` 分离编译 |
| 05/01 | Fri | B | B1 完 + B2 | WSL | float/double 两 build 都绿；periodic + reflective BC 实现 |
| 05/02 | Sat | B | B3 | WSL | BoundaryType enum + cfg `bc_x`/`bc_y` 集成 |
| 05/03 | Sun | B | B4 + B 回归 | WSL | 5 个 BC 单测；112+ cases 全绿（float + double） |
| 05/04 | Mon | C | C1.1 | WSL | float × 6 个 1D Toro 回归 12 CSV + summary |
| 05/05 | Tue | C | C1.2 (references) | WSL | 800×800 LW3 reference（double, 20–40 min）；200²/400² float + double 候选 |
| 05/06 | Wed | C | C1.2.5 phase-error | WSL | `phase_error_metrics.py`：shock-track + **SSIM 单 scalar**（skimage 3 行调用）+ 4 张 2D 差值 heatmap |
| 05/07 | Thu | C | C1.3/C1.4 | WSL | `float_regression_report.py` 合并 1D+2D+phase；`float_vs_double_regression.md` |
| 05/08 | Fri | C | C2 kickoff | WSL + Docker | Verificarlo real-float 构建尝试 |
| 05/09 | Sat | C | C2 | WSL + Docker | real-vs-vprec 对比跑完 |
| 05/10 | Sun | C | C2 完 + 文档 | WSL | `docs/week4/` 所有报告齐；merge 回 main |

**缓冲**：05/11–05/13 留给 C2 Verificarlo bug 排查、2D SLURM 任务 OOM 重跑、float 回归异常调查、MCA p=53 build 在 CSC 上的兼容性验证（若 Week 4 切到 CSC 跑 A2 noise floor）。Report 1 截止 05/29，余 >2 周。

**关键并行窗口**：
- **04/22 白天**：A2 Stage 1 `--mode visible` 先出 8 张带 x 标记图，当天邮件回复导师（0.5d 窗口内）
- **04/22 晚上**：A2 Stage 2 启动 8 次 × 30-sample MCA p=53 noise-floor runs（overnight ~2–4 小时）；04/23 白天产 MCA 图 + 04/24 补发同图给导师
- **04/26 production submit**：feasibility 验证 `t_{200²} ≤ 12h` per-task 后，两次 `sbatch --array=1-30` 把 60 tasks 同时推给 SLURM 调度器；SLURM 并发执行，wall-clock ≈ `t_{200²}`
- 04/26 `sbatch` 后，04/27 白天本地推进 A4 SNR 代码；samples 在 cluster 上独立完成，无需 babysitting
- 05/05 启动 800×800 reference（本地 laptop 20–40 分钟）后继续 200²/400² 跑（同机上串行即可）
- 05/08 Verificarlo real-float 构建同时可准备 C2 分析脚本骨架

**跨环境注意事项**：
- A2 Noise Floor：Verificarlo via WSL+Docker 或 CSC module，与 A3 共用 Verificarlo 工具链；不依赖 GCC `-ffp-contract`；Windows native 编译链不参与
- A3 SLURM job：每个 task 强制 `OMP_NUM_THREADS=1 + OPENBLAS_NUM_THREADS=1 + MKL_NUM_THREADS=1` 防 PRNG 污染；per-sample 并行走 SLURM array 进程级
- A3：本地 WSL 通过 Docker 跑 Verificarlo，CSC 侧用 module 或 singularity——同一脚本 `--runner={docker|singularity|module}` 切换
- `/dev/urandom`：WSL 与 CSC Linux 均可用

---

## 9. 总验收清单（Week 4 完成判据）

在 `week4-implementation` 分支上 merge 回 `main` 前必须满足：

**代码（B 相关）**：
- [x] `build-double/unit_tests.exe` 与 `build-float/unit_tests.exe` 都绿（>=112 cases）
- [x] `libhrsc_euler.a` 成功构建，包含 `EulerSolver<float>` 与 `EulerSolver<double>` 的 explicit instantiation（`nm` 可见对应符号）
- [x] **`TimeReal = double`** 在 `src/core/types.hpp` 声明；`m_time` / `m_t_end` / `m_kahan_c` 三个成员均为 `TimeReal`（非 `Real`）；`compute_dt()` 返回 `TimeReal`；`x_sweep` / `y_sweep` 接 `TimeReal dt` 参数（dt 是 step() 内局部变量，不建成员）
- [x] `tests/unit/test_time_accumulator.cpp` 绿（Catch2 C++ 单测，而非 Python）：`TEMPLATE_TEST_CASE("m_time survives 1e7 accumulations", "[time][TimeReal]", float, double)` 构造 `EulerSolver<TestType>`，循环 1e7 次 `step()` 用 dummy dt≈1e-7，断言 `solver.time() ≈ 1.0` 到 1e-10（TimeReal=double 下两种 TestType 都 PASS；若回归成 `Real m_time` 则 `float` 版本 FAIL）
- [x] Sod double 端到端 bit-identical 回归：改 TimeReal 后 diff=0 与 Week 3 最终版比对（double==TimeReal 时无任何数值差异）
- [x] Kahan compensated summation 的 `m_kahan_c` 成员写入 `euler_solver.cpp` 的 step() 实现，初始化为 0；注释解释 "keeps full double precision for ~1e8 accumulations (Week 12 MHD 长演化铺垫)"
- [x] `src/euler/euler_solver.hpp` 中不再包含成员函数定义，`euler_solver.cpp` 文件末尾有 `template class EulerSolver<float>;` 与 `template class EulerSolver<double>;`
- [x] Periodic + reflective BC 单测全绿（含 X-only / Y-only / X+Y 混合）
- [x] 1D Sod `bc=outflow` 输出 bit-by-bit 与 Week 3 最终版本一致（无回归，diff=0）

**代码（A 相关）**：
- [x] `src/main.cpp` 默认 `solver=rusanov`（cfg 未显式指定时），Week 3 cfg 全部显式写明 solver 后行为不变
- [x] `scripts/noise_floor_run.sh` 跑通 × 4 test × 2 solver = 8 份 `noise_floor.npz`，每份含 30 个 MCA p=53 样本的逐 cell std field
- [x] 每份 `noise_floor.npz` 的 metadata `precision_bits == 53` 与 `n_samples == 30` 在 analyzer 入口处断言通过
- [x] `docs/experiment_logs/week4_a2_noise_floor_calibration.md` 给出 `k_grad` 在本 test suite 上的拟合值（或保留 1.0 + 拟合散点图证据）
- [x] `scripts/plot_divergence_marker.py` 支持 `--mode {noise_floor, strict_fp, visible}` 三种；`noise_floor` 默认，`strict_fp` 为 fallback 并打 WARN
- [x] `tests/py/test_plot_divergence_marker.py` **8 case** 全绿（含 3-mode 切换、noise_floor-only 专属 case、noise-floor 吸收、shock-offset 吸收、fallback warning）

**A2 — 两阶段交付**：
- [x] **Stage 1 (0.5d)** 04/22 当日：`--mode visible rel_tol=1e-3` 产 8 张带 x 标记图，邮件回复导师（证据：`docs/emails/week4_email_a2_s1_2026-04-22.md`）
- [x] **Stage 2 (1.5d)** 04/23–04/24：overnight MCA p=53 batch 跑完 8 个 noise-floor；04/24 补发同一图给导师，正文注明 "same figure with MCA-calibrated noise floor overrides Stage 1"
- [x] `docs/experiment_logs/week4_a2_noise_floor_calibration.md` 记录 S1 vs S2 的 x 标记位移（若有差异则分析原因）

**C1 回归**：
- [x] **1D**：6 个 Toro 1D 测试在 float 和 double 下都跑通，L1_rho 符合预期（double ≤ 1e-3 level；float 相对 double 增量在 0.1%–5% 区间，不出现 NaN/inf）
- [x] **2D**：`build-double/hrsc tests/cases/liska_wendroff_2d/config3_ref800.cfg` 产出 800×800 reference 密度场（与 Liska-Wendroff 2003 Fig 3 视觉一致）
- [x] **2D**：200²/400² × (float, double) 四组候选场通过 `scripts/downsample_2d.py` 块平均到 200×200 后与 reference 计算 L1/L2/Linf（float 200² vs double 200² 差距 < 1%）
- [x] **Phase-error 定性补充（SSIM scalar）**：`scripts/phase_error_metrics.py` 对 4 组 2D 候选输出 L1 / `ssim_rho` / Δx_shock / Δy_shock 表，外加 4 张 2D 差值 heatmap
- [x] `phase_error_metrics.py` 对 `skimage.metrics.structural_similarity` 做 try-import；失败时 fallback 裸 L1 + heatmap 并在 summary.md 顶部打 WARN
- [x] `tests/py/test_ssim_scalar.py` 绿：纯相移合成数据的 `ssim_rho` 明显 < 1；相同数据的 `ssim_rho ≈ 1 − 10⁻⁸`
- [x] `float_vs_double_regression.md` 含 "Why SSIM over axis-aligned W1" 短节 + **"Future Work: 3-factor SSIM & phase topology in Report 2"** 备注
- [x] `docs/experiment_logs/week4_c1_float_vs_double_regression.md` 含 12 个 1D CSV 表 + 4 张 2D 差值 heatmap + L1/SSIM 对比小节

**A3 — 2D Verificarlo（SLURM array 并发 200²×N=30）**：
- [x] `scripts/slurm/verificarlo_2d_array.sh` 两次 `sbatch --array=1-30`（HLLC + Rusanov）全部 60 tasks 成功退出（sacct exit code 0）
- [x] SLURM 脚本 `#SBATCH --time=12:00:00` 是 per-task wall-clock 上限（comment 中明示此值非整批预算，整批 wall-clock 由 SLURM 并发调度决定）
- [x] SLURM 脚本与本地 `scripts/verificarlo_run_2d.sh` 都在运行前 `export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1`（PRNG 线程隔离，避免 MT19937 全局态被共享）
- [x] 每 solver 目录下 `seeds/seed_01.csv` … `seed_30.csv` 共 30 个独立 CSV（无 flock / 无 shared file），`load_seeds(seed_dir, expected_n=30).seed_hex.nunique() == 30` 全部通过（/dev/urandom 熵源）
- [x] 本地 WSL 的 smoke run 通过 Docker 执行 Verificarlo，同样产出 `seeds/seed_NN.csv` 分片与 thread-pinning
- [x] `docs/experiment_logs/week4_a3_2d_vfc_feasibility.md` 记录：40²×3 smoke + 100²×5 feasibility 的 wall-clock 与内存；外推 `t_{200²} ≈ 4·t_{100²}·1.3`；production 阶段 sacct 实测 per-task wall-clock + queue latency；χ² 90% CI σ ±15% 引用作为 N=30 的 justification
- [x] `scripts/verificarlo_analysis_2d.py` 产出 σ(rho) 与 significant digits 两张 heatmap（HLLC、Rusanov 各一对）
- [x] `experiments/week4/vfc_2d/samples/` 已由 `.gitignore` 拦截；`seeds/seed_NN.csv` 分片入库（每 solver 30 × ~100 bytes = 3 KB 级）

**A4 — trade-off metric（SNR / LoSoS）**：
- [x] `scripts/snr_metric.py` 采用 **field-first 算子顺序**：先逐 cell 计算 σ_FP(i) 与 μ_trunc(i)，再做空间聚合；报告 SNR_global / SNR_median / SNR_q05 三个 scalar
- [x] `tests/py/test_snr_operator_order.py` **回归防线**：构造空间反相关噪声测试数据，断言 `std(||E||_1) ≠ ||std_s(U)||_1`，并验证实现走的是后者
- [x] `scripts/losos_metric.py` 同样 field-first，输出 **3 个 field × 3 个 scalar = 9 列**：`s_reliability_{min,q05,mean}` + `s_accuracy_{min,q05,mean}` + `s_worst_{min,q05,mean}`
- [x] `tests/py/test_losos_three_fields.py` 绿：(a) `s_worst ≤ min(s_reliability, s_accuracy)` 逐 cell 成立；(b) 构造 `σ_FP ≈ 0` 但 `μ_sample ≠ U_ref` 的反例，`s_reliability` 很高 / `s_accuracy` 很低（正确分离 reliability vs accuracy）
- [x] `scripts/pareto_plot.py` 使用 `SNR_global` + **`s_worst_q05`** 在 (log10 μ_trunc, significant digits) 平面画 HLLC vs Rusanov 的 Pareto 前沿
- [x] **§A4.4 头版 conclusion table**：`scripts/tradeoff_summary_table.py` 产出 8 列 Markdown table `(solver, p, μ_trunc_L1, σ_FP_L1, s_worst_q05, s_req(N), s_worst−s_req, regime)`，至少覆盖 `(test=LW3, N=200²) × (HLLC, Rusanov) × (double, float)` = 4 行
- [x] **`s_req(N)` 动态计算**：`scripts/s_req_metric.py` 从 p=53 MCA mean 与 800² double reference 实测 `E_trunc(N)` 并计算 `s_req(N) = -log10(E_trunc) + 1`；`tests/py/test_s_req_scaling.py` 绿（`s_req(2N) − s_req(N) ≈ 0.3` 当 `E_trunc ∝ Δx`）
- [x] `scripts/_tradeoff_thresholds.py` 集中声明 regime 判定边际 + bitwise-reproducibility 工程阈值；**不再**包含 `PUBLICATION_QUALITY` / `CONVERGENCE_STUDY` 静态阈值（已被动态 `s_req(N)` 取代）
- [x] `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md` 定位为 **Raw Data Log**：顶部 = §A4.4 头版 table + ≤ 100 字结论陈述；中部 = 3-field LoSoS 9 列 table + Pareto 图（含 `s_req(N)` 目标带叠加）+ 4-regime diagnostic 表；底部 = 方法论声明（≤ 半页，不展开 Report 1 级推导）
- [x] 文档含：(a) §A4.1.0 算子不可交换警告 + 反例、(b) §A4.2.0 为什么 LoSoS 报 3 field、(c) §A4.2.2 truncation-anchored `s_req(N)` 的定义与物理含义、(d) 对"balance"与"多少位"两个开放问题的定量回答（基于 4-regime 诊断：over-provisioned / well-matched / round-off-limited / truncation-limited）

**C2 — real-float vs VPREC p24**：
- [x] `scripts/verificarlo/verificarlo_run.sh --real-float` 成功构建并运行
- [x] `scripts/figures/plot_real_vs_vprec.py` 产出双曲线重叠图（Sod + Stationary Contact，另含 FMA 与 Rusanov 稳健性对照）
- [x] `docs/experiment_logs/c2_real_float_vs_vprec.md` 结论：两者是否一致，差异是否来自 FMA、舍入模式

**文档**：
- [x] `docs/week4/week4-plan.md`（本文档）
- [x] `docs/experiment_logs/week4_a3_2d_vfc_report.md`
- [x] `docs/experiment_logs/week4_a3_2d_vfc_feasibility.md`
- [x] `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md`
- [x] `docs/experiment_logs/week4_c1_float_vs_double_regression.md`
- [x] `docs/experiment_logs/c2_real_float_vs_vprec.md`
- [ ] `docs/week4/cfg_reference.md`（汇总所有 cfg keyword）

**Git**：
- [x] 每 commit 单测绿（pre-commit hook：`cmake --build build-double --target unit_tests && ./build-double/unit_tests.exe`）
- [x] `.gitignore` 拦截 `experiments/week4/**/samples/`、`experiments/week4/noise_floor/**/sample_*.txt`、`build-float/`、`build-vfc-p53/`、`build-vfc-real/`
- [x] 无二进制产物被追踪（`.vtk`、`.npz`、`.png` 除 `docs/` 下少量示意图外不入库）
- [ ] Branch `week4-implementation` 线性历史（按 §6 的 commit graph），merge 干净到 `main`（prefer `--no-ff` 保留 branch 标签）

---

## 附录 A: cfg keyword catalogue（Week 4 后）

### A.1 运行时 cfg（solver & runner）

| Key | Type | Default | Allowed | Scope |
|---|---|---|---|---|
| `mode` | str | `normal` | `normal`, `convergence` | runner |
| `test` | str | — | `sod`, `toro2`, …, `stationary_contact`, `lw_config3`, `lw_config6` | IC |
| `nx`, `ny` | int | `200`, `1` | ≥1 | grid |
| `xmin`, `xmax`, `ymin`, `ymax` | double | `0.0`, `1.0`, `0.0`, `1.0` | any | grid |
| `gamma` | double | `1.4` | >1.0 | EOS |
| `cfl` | double | `0.8` | (0, 1] | time step |
| `t_end` | double | `0.25` | >0 | time |
| `solver` | str | `rusanov` (A1 后) | `hllc`, `rusanov` | flux |
| `bc` | str | `outflow` | `outflow`, `periodic`, `reflective` | BC shortcut |
| `bc_x` | str | = `bc` | same | per-axis BC |
| `bc_y` | str | = `bc` | same | per-axis BC |
| `resolutions` | int-list | — | comma-separated ints | convergence 模式 |
| `x0` | double | `0.5` | any | convergence interface |
| `output_precision` | int | `17` | 1–17 | text output |

**解析顺序**（B3）：`bc` 先解析（默认 `outflow`）→ `bc_x` 若缺省则沿用 `bc` 的值 → `bc_y` 若缺省则沿用 `bc` 的值。`EulerSolver` 在 `step()` 内根据 `bc_x` / `bc_y` 分别在 X/Y sweep 前后施加。

### A.2 编译时宏（B1，PrecisionConfig.cmake 控制）

| 宏 / 变量 | Scope | 取值 | 说明 |
|---|---|---|---|
| `HRSC_REAL` | C++ typedef | `float` 或 `double` | `src/core/types.hpp` 中 `using Real = HRSC_REAL;`；全体模板实例化到它 |
| `HRSC_PRECISION` | CMake 选项 | `float` / `double` | `cmake -DHRSC_PRECISION=float ..` 切换 |
| `HRSC_EPS` | C++ constexpr | `std::numeric_limits<HRSC_REAL>::epsilon()` | 分析脚本可通过 cfg 比对 |

### A.3 分析脚本 CLI（A2, A3, A4, C1, C2）

| 脚本 | Flag | Default | 含义 |
|---|---|---|---|
| `noise_floor_run.sh` | positional: test_cfg | — | 跑 N×MCA p=53 samples 产 `noise_floor.npz`（逐 cell std field） |
| `noise_floor_run.sh` | positional: solver | — | `hllc` \| `rusanov` |
| `noise_floor_run.sh` | positional: out_dir | — | 输出路径（含 seeds.csv + samples） |
| `noise_floor_run.sh` | positional: n_samples | `30` | MCA 样本数（统计 ≥30 推荐） |
| `plot_divergence_marker.py` | `--mode` | `noise_floor` | `noise_floor` \| `strict_fp` \| `visible`（见 §3 A2） |
| `plot_divergence_marker.py` | `--noise-floor-a` / `-b` | — | `noise_floor` 模式下两 solver 的 noise_floor.npz（必需） |
| `plot_divergence_marker.py` | `--safety` | `3.0` | 3σ 包络系数（统计学标准，非魔术数） |
| `plot_divergence_marker.py` | `--k-grad` | `1.0` | 梯度加权系数；从 noise-floor run 拟合（见 §A2.4） |
| `plot_divergence_marker.py` | `--source-precision` | `float64` | strict_fp fallback 下决定 eps |
| `plot_divergence_marker.py` | `--k-eps` | `10.0` | strict_fp fallback，带 WARN |
| `plot_divergence_marker.py` | `--rel-tol` | `1e-3` | visible 模式相对容差 |
| `snr_metric.py` | `--samples-dir` | — | A3 样本根目录 |
| `snr_metric.py` | `--reference` | — | convergence 模式产出的高分辨率解 |
| `snr_metric.py` | `--aggregate` | `all` | 报告 `global` \| `median` \| `q05` \| `all`（field-first → 空间聚合）|
| `losos_metric.py` | `--quantile` | `0.05` | 报告 `s_worst_q05` 作为主 scalar；3 field 全部输出到 CSV |
| `losos_metric.py` | `--reference` | — | reference field（1D：exact Riemann；2D：800² double），用于 `s_accuracy` |
| `losos_metric.py` | `--output-fields` | `all` | `reliability` \| `accuracy` \| `worst` \| `all`（默认 `all`） |
| `pareto_plot.py` | `--solvers` | `hllc,rusanov` | 在图上分组 |
| `pareto_plot.py` | `--x` | `log10_mu_trunc` | x 轴量 |
| `pareto_plot.py` | `--y` | `s_worst_q05` | y 轴量（Round 3：默认 `s_worst_q05`，可切 `s_reliability_q05` / `s_accuracy_q05`） |
| `pareto_plot.py` | `--overlay-sreq` | `on` | 在 y 轴叠加 `s_req(N)` 水平虚线作为"目标带"参考 |
| `s_req_metric.py` | `--reference` | — | 800² double reference 文件（或 exact Riemann for 1D） |
| `s_req_metric.py` | `--samples-dir` | — | p=53 MCA 样本目录，用于求 mean |
| `s_req_metric.py` | `--output` | — | CSV 输出 `(test, solver, N) → E_trunc, s_req` |
| `tradeoff_summary_table.py` | `--snr-csv` | — | `snr_metric.py` 产出的 `(test, solver, p) → μ_trunc_L1, σ_FP_L1` CSV |
| `tradeoff_summary_table.py` | `--losos-csv` | — | `losos_metric.py` 产出的 `(test, solver, p) → s_worst_q05, ...` CSV |
| `tradeoff_summary_table.py` | `--sreq-csv` | — | `s_req_metric.py` 产出的 `(test, solver, N) → s_req` CSV（动态阈值源） |
| `tradeoff_summary_table.py` | `--out-dir` | `docs/week4/tradeoff_summary_tables/` | 输出 per-test Markdown + `all_tests_summary.md` |
| `tradeoff_summary_table.py` | `--thresholds` | `scripts/_tradeoff_thresholds.py` | 读取 regime 边际常量 + bitwise-reproducibility 工程阈值 |
| `phase_error_metrics.py` | `--ssim` | `on` | 调用 `skimage.metrics.structural_similarity` 产 scalar；`off` 时仅跑 L1 + heatmap（skimage 不可用时自动 fallback） |
| `phase_error_metrics.py` | `--shock-threshold` | `0.5` | shock tracking 梯度峰比例 |
| `phase_error_metrics.py` | `--smooth-sigma` | `0.5` | 高斯平滑 σ（cells） |
| `verificarlo_run.sh` | `--real-float` | off | C2：走 real-float 而非 VPREC p24 |
| `verificarlo_run.sh` | `--runner` | `docker` | WSL 本地用 docker；CSC 用 singularity 或 module |
| `slurm/verificarlo_2d_array.sh` | `--samples` | `30` | SLURM array 长度 |

### A.4 编译/环境（A2 + A3 共用）

| 变量 | Default | 含义 |
|---|---|---|
| `VFC_BACKENDS` | `libinterflop_mca.so --mode=rr --precision-binary64=53` | Verificarlo 后端配置（A2 noise floor 与 A3 2D 生产都用 p=53） |
| `VFC_BACKENDS_SEED` / `VERIFICARLO_MCA_SEED` | — | 64-bit hex，/dev/urandom 生成；同时 export 两者保兼容 |
| `VFC_NSAMPLES` | `30` | 每个 cell 的样本数（生产态） |
| `OMP_NUM_THREADS` | `1`（**强制**） | PRNG 线程隔离；Verificarlo libinterflop 未保证 MT19937 thread-safety |
| `OPENBLAS_NUM_THREADS` / `MKL_NUM_THREADS` / `VECLIB_MAXIMUM_THREADS` / `NUMEXPR_NUM_THREADS` | `1`（**强制**） | 屏蔽 BLAS 隐式 threading，防 numpy/scipy 意外吃多核扰乱 PRNG |
| `SLURM_ARRAY_TASK_ID` | — | 由 SLURM 填入，用作 sample index |

## 附录 B: 新增/改动文件清单

### 新增（按子项归类）

**B1 — PrecisionConfig + 分离编译**
```
cmake/PrecisionConfig.cmake                 # HRSC_PRECISION option -> HRSC_REAL macro + numeric flags
src/core/types.hpp                          # TimeReal = double typedef（独立于 Real）
src/euler/euler_solver.cpp                  # EulerSolver 成员函数定义 + explicit instantiation；time accumulator 用 TimeReal + Kahan summation
tests/unit/test_time_accumulator.cpp        # Catch2 TEMPLATE_TEST_CASE：float/double 在 1e7 次 dt≈1e-7 累加后 m_time ≈ 1.0 到 1e-10
```

**B2/B3/B4 — 边界条件**
```
tests/unit/test_boundary.cpp                # 新增 periodic/reflective/dispatcher case（合并进已存在的文件或新建）
```

**A3 — 2D Liska-Wendroff + Verificarlo (SLURM array 并发 200²×N=30)**
```
tests/cases/liska_wendroff_2d/lw_tests.hpp
tests/cases/liska_wendroff_2d/config3.cfg              # production 200×200（HLLC；smoke 用 --nx 40 override）
tests/cases/liska_wendroff_2d/config3_feas.cfg         # feasibility 100×100
tests/cases/liska_wendroff_2d/config3_rusanov.cfg      # 200×200 Rusanov
tests/unit/test_liska_wendroff.cpp                     # LW3 IC 对称性 / 质量守恒单测
scripts/slurm/verificarlo_2d_array.sh                  # SLURM array --array=1-30 + /dev/urandom seed + per-task seeds/seed_NN.csv (no flock) + per-task --time=12:00:00
scripts/slurm/verificarlo_2d_submit.sh                 # 包装 sbatch + 参数校验（solver + cfg）
scripts/verificarlo_run_2d.sh                          # WSL + Docker 本地 smoke/feasibility（同一 seed 策略）
scripts/verificarlo_analysis_2d.py                     # 聚合 samples 产 σ / significant-digits heatmap + seed 独立性校验
scripts/io_helper.py                                   # 加载 cfg + samples 的共用函数
experiments/week4/vfc_2d/{hllc,rusanov}/seeds/seed_NN.csv  # 30 per-task CSV shards (跟进 git，3 KB 级，用于复现)
docs/week4/2d_vfc_feasibility.md                       # 40²/100² 两阶段 wall-clock + production 实测 + χ² CI 引用
docs/week4/2d_vfc_report.md                            # 最终分析结论（N=30 samples × 2 solvers）
```

**A2 — 发散标记 (MCA p=53 Noise-Floor 校准)**
```
scripts/noise_floor_run.sh                              # N×30 samples MCA p=53 + /dev/urandom seed per sample
scripts/compute_noise_floor.py                          # 把 N 个 MCA 样本的逐 cell std 存 .npz（含 seed 校验）
scripts/plot_divergence_marker.py                       # 三 mode: noise_floor / strict_fp / visible
tests/py/test_plot_divergence_marker.py                 # 8-case pytest（含 3-mode 切换 + noise-floor 吸收）
experiments/week4/noise_floor/**/noise_floor.npz        # 跟进 git（MB 级；保留作 Report 1 引用依据）
experiments/week4/noise_floor/**/seeds.csv              # 30 samples × (sample_id, seed_hex, ts)
docs/week4/noise_floor_calibration.md                   # k_grad 拟合、MCA p=53 noise-floor 分布直方图
```

**A4 — trade-off metric (Field-First + 3-Field LoSoS + truncation-anchored s_req(N) + §A4.4 Conclusion Table)**
```
scripts/snr_metric.py                                   # field-first: σ_FP(i), μ_trunc(i) → global/median/q05
tests/py/test_snr_operator_order.py                     # 回归防线：防止算子顺序被改回错误
scripts/losos_metric.py                                 # 3 field: s_reliability / s_accuracy / s_worst；4-regime 诊断（基于 s_worst − s_req(N)）
tests/py/test_losos_three_fields.py                     # 3-field invariants: s_worst = min(rel, acc) + 诊断反例
scripts/s_req_metric.py                                 # s_req(N) = -log10(||E_trunc(N)||) + 1（truncation-anchored 动态阈值）
tests/py/test_s_req_scaling.py                          # s_req 随网格加倍 → 增 ~0.3（log10 of refinement factor 2）
scripts/pareto_plot.py                                  # (log10 μ_trunc, s_worst_q05) Pareto；叠加 s_req(N) 目标带
scripts/tradeoff_summary_table.py                       # §A4.4 头版 table 生成器：8 列 Markdown（含 s_req 与 regime 列）
scripts/_tradeoff_thresholds.py                         # regime 边际常量 + bitwise-reproducibility 工程阈值（静态 pub/conv 阈值已废弃）
docs/week4/tradeoff_analysis.md                         # Raw Data Log：§A4.4 头版 table → 3-field 9 列 table → Pareto（含 s_req 带）→ 4-regime 诊断表 → 方法论声明（≤半页）
docs/week4/tradeoff_summary_tables/                     # per-test Markdown 汇总（all_tests_summary.md + lw3_n200.md ...）
```

**C1 — float 全回归（1D + 2D LW3 + Phase-Error 分解）**
```
tests/cases/toro_1d/convergence_toro2.cfg               # 1D 5 个新增（已有 sod + sod_rusanov）
tests/cases/toro_1d/convergence_toro3.cfg
tests/cases/toro_1d/convergence_toro4.cfg
tests/cases/toro_1d/convergence_toro5.cfg
tests/cases/toro_1d/convergence_stationary_contact.cfg
tests/cases/toro_1d/convergence_*_rusanov.cfg           # 同 5 份的 Rusanov 版本
tests/cases/liska_wendroff_2d/config3_n200.cfg          # 200×200 候选（float 与 double 共用）
tests/cases/liska_wendroff_2d/config3_n400.cfg          # 400×400 候选
tests/cases/liska_wendroff_2d/config3_ref800.cfg        # 800×800 reference（double only）
scripts/float_regression_1d.sh                          # 1D 编排
scripts/float_regression_2d.sh                          # 2D 编排（含 800² reference 生成）
scripts/float_regression_report.py                       # CSV/NPZ → summary.md
scripts/downsample_2d.py                                 # 400→200 / 800→200 块平均（保守 cell-average）
scripts/phase_error_metrics.py                           # shock-track + SSIM 单 scalar（skimage 3 行调用）+ L1 + 2D 差值 heatmap；try-import skimage 失败时 fallback 裸 L1
tests/py/test_ssim_scalar.py                             # 纯相移合成数据的 SSIM 明显 < 1；相同数据 SSIM ≈ 1
docs/week4/float_vs_double_regression.md                 # 含 L1/SSIM 对比小节 + "Future Work: 3-factor SSIM in Report 2" 备注
```

**C2 — real-float vs VPREC**
```
scripts/figures/plot_real_vs_vprec.py
docs/experiment_logs/c2_real_float_vs_vprec.md
```

**汇总文档**
```
docs/week4/cfg_reference.md                             # 汇总附录 A 的 cfg keyword + 脚本 CLI
```

### 改动（按子项归类）

```
# B1
CMakeLists.txt                        # include(PrecisionConfig)；add_library(hrsc_euler STATIC src/euler/euler_solver.cpp)
src/core/types.hpp                    # using Real = HRSC_REAL（宏由 PrecisionConfig 注入）
src/euler/euler_solver.hpp            # 成员函数定义迁出，仅保留声明；头部声明不含实现

# A1 / B3
src/main.cpp                          # default solver -> rusanov；using Real = HRSC_REAL；parse_bc

# B2 / B3
src/core/boundary.hpp                 # + apply_periodic_bc, apply_reflective_bc, BoundaryType, apply_boundary
src/euler/euler_solver.hpp            # + bc_x/bc_y members；replace apply_outflow_bc with apply_boundary
tests/unit/test_boundary.cpp          # + periodic/reflective/dispatcher cases

# C2
scripts/verificarlo/verificarlo_run.sh # + --real-float flag

# A2
scripts/plot_vfc_hllc_vs_rusanov.py   # 改为调用 plot_divergence_marker 的公共函数
scripts/plot_stationary_contact_vfc.py # 同上

# 其他
.gitignore                            # + experiments/week4/**/samples, experiments/week4/noise_floor/**/sample_*.txt, build-float/, build-vfc-p53/, build-vfc-real/
```

### 不动

Week 3 已完成的全部：`euler_flux.hpp`, `muscl.hpp`, `hancock.hpp`, `hllc.hpp`, `rusanov.hpp`, `exact_riemann.hpp`, `eos.hpp`, `vec.hpp`, `grid.hpp`, `config.hpp`, `io.hpp`, `error_norms.hpp`（模板化早已就绪，无需动）。`types.hpp` 仅新增 `using Real = HRSC_REAL;`，不改动既有内容。

---

_最后更新: 2026-04-22. 作者: Yudong Tang._
