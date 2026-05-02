# Week 4 → Week 5 衔接文档

**Date:** 2026-04-29  
**Branch:** `week4-implementation`  
**Target phase:** Week 5（`overall.md` 278–296）

本文档用于 Week 4 向 Week 5 的交接，聚焦三件事：
- 上周已交付内容（哪些不用重做）
- Week 5 按总体计划还需要补齐什么
- 现在可直接复用的接口与脚本

---

## Part 1. Week 4 已完成内容（可直接继承）

### 1.1 Week 4 核心里程碑（overall.md 266–275）已落地

| 项目 | 状态 | 关键文件 |
|---|---|---|
| PrecisionConfig（float/double） | ✅ | `cmake/PrecisionConfig.cmake`, `src/main.cpp`, `src/core/types.hpp` |
| EulerSolver 分离编译 + explicit instantiation | ✅ | `src/euler/euler_solver.hpp`, `src/euler/euler_solver.cpp` |
| periodic + reflective BC | ✅ | `src/core/boundary.hpp`, `tests/unit/test_boundary.cpp` |
| `bc` / `bc_x` / `bc_y` 配置接入 | ✅ | `src/main.cpp` (`parse_boundary`) |
| 1D/2D float regression（C1） | ✅ | `scripts/regression/float_regression_{1d,2d}.sh` |
| C2 real-float vs p24 surrogate 对比 | ✅ | `docs/experiment_logs/c2_real_float_vs_vprec.md` |
| A4 p53 + p24-real-float tradeoff table | ✅ | `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md`, `docs/experiment_logs/week4_a4_p24_real_float_execution_summary.md` |
| 最小 experiment harness 入口 | ✅ | `docs/HARNESS.md`, `scripts/build_all.sh`, `scripts/run_matrix.py`, `scripts/aggregate_metrics.py` |

参考总结：`docs/week4/week4-summary.md`。

### 1.2 对 Week 5 直接有用的前置结果

1. 2D 框架已可稳定运行（`x/y sweep` + 交替分裂 + per-axis BC）。
2. `lw_config3` 已有 IC 与回归配置，可作为 Week 5 2D 基线。
3. OpenMP 已在 `EulerSolver` sweeps 与 CFL reduction 接入（`#pragma omp parallel for`）。
4. 数据与分析脚本链路已成型（回归、heatmap、summary JSON/MD）。
5. A4 headline table 已包含 `p53` 与 `p24-real-float` 四行（HLLC/Rusanov × precision），可直接用于 Report 1/2 的 precision tradeoff 论证。
6. 最小 harness 已落地：后续实验应优先通过 matrix build/run/aggregate 入口保存 cfg、command、commit、stdout/stderr 与 summary。

### 1.3 A4 p24-real-float 交接要点

Athena 上的 Liska-Wendroff Config 3 (`200 x 200`, `t_end=0.3`) p24-real-float MCA 已完成：

| Solver | Samples | 结果 |
|---|---:|---|
| HLLC | 30 | success |
| Rusanov | 30 | success |

正式四行 headline table：

- `docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md`

执行与复现记录：

- `docs/experiment_logs/week4_a4_p24_real_float_execution_summary.md`
- `docs/experiment_logs/week4_a4_p24_real_float_readme.md`

关键结论：

- `p24-real-float` 与 `p53` 在 headline rho row 上共享相同的 `s_worst_q05` / regime，因为该行受 accuracy limit 主导。
- precision effect 主要体现在 `sigma_FP_L1`：HLLC 从 `5.216e-11` 升至 `2.956e-02`，Rusanov 从 `2.278e-11` 升至 `8.199e-03`。
- 两个 p24-real-float rows 均为 `round-off-limited`，可作为 Week 5/Report 1 中“低精度噪声显著抬升”的核心证据。

---

## Part 2. Week 5 计划对照（基于 overall.md）

`overall.md` Week 5（278–296）要求：
- 2D tests：Liska-Wendroff（config 3 + 6）、shock-bubble、2D plotting
- GPU 启动：`gpu/cuda_utils.cuh`、`gpu/gpu_grid.cuh`、`gpu/euler_kernels.cuh` 起步

当前对照状态：

| Week 5 项 | 当前状态 | 说明 |
|---|---|---|
| `lw_tests.hpp` Config 3 | ✅ | 已实现并用于 C1 |
| `lw_tests.hpp` Config 6 | ⚠️ stub | 当前会抛异常（待 Week 5 实现） |
| `tests/cases/shock_bubble/*` | ❌ | 目录/IC 尚未落地 |
| `common/timer.hpp` | ❌ | 尚未落地 |
| `analysis/plot_2d.py` | ❌ | 当前等效能力散布在 `scripts/figures` 与 regression 脚本 |
| `src/gpu/*` 初始设施 | ❌（目录在，文件空） | Week 5 起步任务 |
| OpenMP sweep 并行 | ✅（已超前） | 位于 `src/euler/euler_solver.cpp` |

---

## Part 3. Week 5 可直接复用接口清单

### 3.1 2D IC 与入口选择

- IC 文件：`tests/cases/liska_wendroff_2d/lw_tests.hpp`
  - `setup_liska_wendroff_config3(...)`：可直接用
  - `setup_liska_wendroff_config6(...)`：当前为 Week 5 stub（调用即抛错）
- `main.cpp` 已支持：
  - `test=lw_config3`
  - `test=lw_config6`（待实现后可直接启用）

### 3.2 边界条件接口（Week 5 可直接用于 KH/2D）

- `src/core/boundary.hpp`
  - `apply_outflow_bc(grid, Axis::{X|Y})`
  - `apply_periodic_bc(grid, Axis::{X|Y})`
  - `apply_reflective_bc(grid, Axis::{X|Y}, flip_indices)`
- `src/main.cpp` 配置解析：
  - `bc=...`（全局）
  - `bc_x=...`, `bc_y=...`（按轴覆盖）
  - 可选值：`outflow | periodic | reflective`

示例（Week 5 常用混合边界）：
```ini
bc_x = periodic
bc_y = reflective
```

### 3.3 Solver 与运行配置接口

- `FluxScheme`: `hllc | rusanov`（`solver` 配置项）
- 输出格式：
  - `output_format = table | binary`
  - `output_file = ...`（binary 必填）
- 进度输出：
  - `progress_interval_s`（`<=0` 关闭）

### 3.4 现成脚本（Week 5 可复用）

- 2D 回归脚本：`scripts/regression/float_regression_2d.sh`
- 2D 指标：`scripts/metrics/phase_error_metrics.py`
- 2D 降采样：`scripts/metrics/downsample_2d.py`
- 结果汇总：`scripts/regression/float_regression_report.py`

### 3.5 Harness 与 A4 指标入口

- Harness 规范：`docs/HARNESS.md`
- Build matrix：`scripts/build_all.sh`
- Run matrix：`python scripts/run_matrix.py <matrix.json>`
- Summary 聚合：`python scripts/aggregate_metrics.py --output <out.json> <summary.json>...`
- A4 headline table 生成：

```bash
python scripts/figures/tradeoff_summary_table.py \
  --snr-csv experiments/week4/metrics/a4_snr_with_float.csv \
  --losos-csv experiments/week4/metrics/a4_losos_with_float.csv \
  --s-req-csv experiments/week4/metrics/s_req_lw_config3_200.csv \
  --N 200 \
  --out docs/experiment_logs/week4_a4_lw_config3_200_tradeoff_table.md
```

Week 5 新实验若产生可比较数据，应尽量沿用同一 summary/table 结构，而不是新建一次性表格。

---

## Part 4. Week 5 建议执行顺序（最小阻塞）

1. **先补 Config 6 IC**（`lw_tests.hpp`）并加对应 cfg。  
2. **补 shock-bubble IC + cfg**（`tests/cases/shock_bubble/`）。  
3. **统一 2D 图输出入口**（新增/整理 `plot_2d.py` 等效脚本）。  
4. **GPU 起步骨架**：先落 `src/gpu/cuda_utils.cuh`、`src/gpu/gpu_grid.cuh`、`src/gpu/euler_kernels.cuh` 的可编译空实现。  
5. 用现有 regression/summary/harness 流程做 Week 5 第一轮基线，确保 CPU 2D 结果可复现，再进入 Week 6 完整 GPU solver。  
6. GPU 数据落地后，优先补 CPU-vs-GPU same-precision diff summary；不要先扩展新实验轴。  

---

## Part 5. Week 5 开工前快速命令

```bash
# 双精度构建（2D baseline）
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double

# 直接跑现有 2D LW3 case
./build-double/hrsc tests/cases/liska_wendroff_2d/config3_n200.cfg

# 运行边界条件与核心单测
./build-double/unit_tests "[boundary]"

# Harness dry-run smoke（只生成 cfg/metadata，不跑 solver）
python scripts/run_matrix.py <matrix.json> --dry-run
```

---

_维护约定：本 bridge 放在目标周目录（Week 5），作为 Week 5 计划与实现的前置上下文。_
