# Week 5 → Week 6 衔接文档

**Date:** 2026-05-02
**Branch:** `week4-implementation`（Week 5 与 Week 6 持续在此 branch；merge 时机见 `week5-plan.md` §5.4）
**Target phase:** Week 6（`overall.md` 308–321）

本文档用于 Week 5 向 Week 6 的交接，聚焦三件事：
- 上周已交付内容（哪些不用重做）
- Week 6 按总体计划还需要补齐什么
- 现在可直接复用的接口与脚本

---

## Part 1. Week 5 已完成内容（可直接继承）

### 1.1 Week 5 核心里程碑（overall.md 286–304）已落地

| 项目 | 状态 | 关键文件 |
|---|---|---|
| `Timer` + 可选 `ProfilingRegistry` / `ScopedTimer` | ✅ | `src/utils/timer.hpp`, `src/utils/profiling.hpp` |
| `[timing] total_s=<v>` 写入 stderr（每次 solver run） | ✅ | `src/main.cpp` |
| Harness 解析 `[timing]` 为 `metadata.json.timing.total_s` | ✅ | `scripts/run_matrix.py` |
| Liska-Wendroff Config 6 IC + 单元测试 | ✅ | `tests/cases/liska_wendroff_2d/lw_tests.hpp`, `tests/unit/test_lw_config6.cpp` |
| LW Config 6 cfg（200×200, 400×400） | ✅ | `tests/cases/liska_wendroff_2d/config6_n{200,400}.cfg` |
| Half-symmetric shock-bubble IC + cfg + 单元测试 | ✅ | `tests/cases/shock_bubble/shock_bubble_tests.hpp`, `shock_bubble_n400x100{,_rusanov}.cfg` |
| `main.cpp` 接入 `test=shock_bubble` 派发 | ✅ | `src/main.cpp` (`setup_ic`) |
| GPU 工具链 bring-up（opt-in `ENABLE_CUDA`） | ✅ | `cmake/CUDASetup.cmake`, `src/gpu/gpu_smoke.cu` |
| GPU 数据路径骨架（`HRSC_CUDA_CHECK`, `DeviceArray<T>`, `GpuGrid<Real,NVars>`） | ✅ | `src/gpu/cuda_utils.cuh`, `src/gpu/gpu_grid.cuh` |
| Catch2 `[gpu]` host↔device roundtrip 测试 | ✅ | 2 cases / 400 assertions |
| `scripts/figures/plot_2d.py`（rho/p/vmag/schlieren，物理 dx/dy 梯度） | ✅ | `scripts/figures/plot_2d.py`, `tests/py/test_plot_2d.py` |
| 6-run harness smoke matrix 全链路验证 | ✅ | `experiments/week5/smoke/matrix.json` |
| Philip supervisor metric（fmd/d_err，1D + 2D） | ✅（post-Week-5 add） | `src/main.cpp`, `scripts/regression/float_regression_{1d,report}.py`, `tests/py/test_float_regression_report.py` |

参考总结：`docs/week5/week5-summary.md`、`docs/week5/week5-verification.md`。

### 1.2 对 Week 6 直接有用的前置结果

1. **GPU 数据路径骨架就绪**：`GpuGrid<Real,NVars>` 与 `Grid2D` 共享 row-major、var-last 布局（含 ghost cells）。Week 6 kernel 应沿用同一 indexing 模型，禁止引入 ad-hoc `cudaMalloc`。
2. **CUDA 工具链已 opt-in**：`ENABLE_CUDA` 默认 OFF；CPU build、cfg 默认值、输出格式均不受影响。Week 6 新增 kernel 同样在 `ENABLE_CUDA` 下定义。
3. **Timer + harness 时序记录已成型**：每次 run 的 `total_s` 自动落到 `metadata.json`，可直接用于 CPU/GPU 性能对照。
4. **2D test matrix 已扩展**：LW Config 3/6 + half-symmetric shock-bubble 三个 case 都有 cfg、IC、单元测试与 baseline 网格，可作为 Week 6 GPU 验证的 ground truth。
5. **Plot/regression 链路对 GPU 输出零成本兼容**：`plot_2d.py` 和 `float_regression_report.py` 都按 binary header 读取，不区分输出方是 CPU 还是 GPU。
6. **Smoke matrix 范式已落地**：Week 6 GPU smoke 应在新 matrix 中加 row，不要绕过 `scripts/run_matrix.py`。
7. **Float regression metric 已对齐导师反馈**：`||float - double||_1 / ||double - exact||_1`（Philip metric）已与原 d/f legacy ratio 并列 emit；CPU-vs-GPU same-precision diff（Week 6 milestone）可复用同一 ratio 形式（`||cpu - gpu||_1 / ||cpu - exact||_1`）。

### 1.3 Week 5 未完成项（已转入 deferred 列表）

| 项 | 当前状态 | 下一步 |
|---|---|---|
| ScopedTimer 5-way phase split | ⚠️ 当前 3 phase（`bc`, `cfl`, `sweep`） | Week 6 不阻塞；如需要再补 `flux`, `update` 即可 |
| CSC GPU build | ❌ 未启动 | 等本地 CUDA kernels 稳定后再跨集群 |
| Verificarlo `vfc_precexp` + unstable-branch detection | ❌ 从 Week 5 推迟 | 视 Report 1 时间窗口决定 |

---

## Part 2. Week 6 计划对照（基于 overall.md 308–321）

`overall.md` Week 6（308–321）要求：
- `gpu/euler_kernels.cuh`：补齐 reconstruct、predict、HLLC、CFL reduction 等剩余 kernel
- `gpu/euler_gpu_solver.cu`：完整 GPU solver orchestration
- `main.cpp`：通过 cfg 选择 CPU / GPU solver
- `cmake/CUDASetup.cmake` + `cmake/CompilerFlags.cmake`：完善 build flag
- 视情况补齐剩余 2D Euler test（LW Config 4、Config 12）
- **GPU is mandatory for Report 1**；如延期，Week 7 早期必须补齐
- **Milestone**：GPU Euler solver 与 CPU 在 machine epsilon 量级一致；可在 CSC GPU 节点运行
- **Carry-over from Week 5**：补完剩余 2D Euler tests；将 Phase-C float-regression 流水线扩展到 GPU 输出（同一 `summary.{md,json}` schema、SSIM / L1 / phase 指标）；CPU-vs-GPU same-precision diff 必须 ≤ ULP-level

当前对照状态：

| Week 6 项 | 当前状态 | 说明 |
|---|---|---|
| `src/gpu/euler_kernels.cuh`（剩余 kernel） | ❌（仅 skeleton） | Week 5 已落 outflow BC + 一个 copy kernel；reconstruct/predict/HLLC/CFL 待写 |
| `src/gpu/euler_gpu_solver.{hpp,cu}` orchestration | ❌ | Week 6 主体工作 |
| `main.cpp` 通过 cfg 选 CPU/GPU | ❌ | 需新增 cfg key（如 `device = cpu | gpu`） |
| `cmake/CUDASetup.cmake` 完善 | ⚠️（最小可用） | Week 6 视需要再补 `CompilerFlags.cmake` 等 |
| LW Config 4 / Config 12（可选） | ❌ | overall.md 标记为 "if needed"；Week 6 优先级低于 GPU |
| CPU-vs-GPU same-precision diff（C-pipeline 扩展） | ❌ | 复用 `summary.{md,json}` schema；ratio 形式可复用 Philip metric |
| GPU 在 CSC 集群上可运行 | ❌ | 本地 CUDA 稳定后再迁移 |

---

## Part 3. Week 6 可直接复用接口清单

### 3.1 GPU 数据路径（已就绪）

- **设备分配 / 错误检查**：
  - `HRSC_CUDA_CHECK(expr)` — 统一 cudaError 检查宏
  - `hrsc::DeviceArray<T>` — RAII 设备数组，避免 ad-hoc `cudaMalloc`/`cudaFree`
  - `hrsc::GpuGrid<Real,NVars>` — `Grid2D` 的设备镜像，row-major、var-last、含 ghost cells
- **Host↔Device 拷贝**：`GpuGrid` 提供 `copy_from_host(Grid2D&)` / `copy_to_host(Grid2D&)`，Week 6 kernel 不应另写 `cudaMemcpy` 路径
- **Build gating**：所有 GPU 代码用 `#ifdef ENABLE_CUDA` / cmake target_compile_features 控制；CPU 默认 build 仍保持字节级一致

### 3.2 CPU 端 Solver 与 IC（GPU 验证 ground truth）

- `EulerSolver<Real>`：CPU 全功能 solver（HLLC/Rusanov × MUSCL-Hancock）
- IC headers：
  - `tests/cases/liska_wendroff_2d/lw_tests.hpp`：`setup_liska_wendroff_config{3,6}`
  - `tests/cases/shock_bubble/shock_bubble_tests.hpp`：`setup_shock_bubble`
  - `tests/cases/toro_1d/`：6 个 1D 经典 case
- 边界条件：`apply_{outflow,periodic,reflective}_bc(grid, Axis::{X|Y})` — Week 6 GPU BC kernel 应对齐 CPU 行为

### 3.3 Float regression / 2D 指标（C-pipeline，可对 GPU 输出直接套用）

- 2D 回归脚本：`scripts/regression/float_regression_2d.sh`
- 1D 回归脚本：`scripts/regression/float_regression_1d.sh`（已带 Philip metric）
- 2D 指标：`scripts/metrics/phase_error_metrics.py`、`scripts/metrics/downsample_2d.py`
- 结果汇总：`scripts/regression/float_regression_report.py`
  - 1D `_report_1d`：legacy d/f + Philip fmd/d_err 双列输出
  - 2D `_report_2d`：legacy L1/L2/Linf + ssim + Philip ratio 双列输出
- **CPU-vs-GPU diff 推荐复用同一 schema**：把 `float_NNN.bin` / `double_NNN.bin` 换成 `cpu_NNN.bin` / `gpu_NNN.bin`，就能直接得到 ULP-level diff 报告

### 3.4 Harness 与 timer

- Build matrix：`bash scripts/build_all.sh`
- Run matrix：`python scripts/run_matrix.py <matrix.json>`
- Summary 聚合：`python scripts/aggregate_metrics.py --output <out.json> <summary.json>...`
- Plotting：`python scripts/figures/plot_2d.py`（rho / p / vmag / schlieren）
- Timer：`hrsc::Timer`（默认 always-on）；`HRSC_ENABLE_PROFILING` 时启用 `ScopedTimer` + `ProfilingRegistry`
- Smoke matrix 模板：`experiments/week5/smoke/matrix.json`（Week 6 应在 `experiments/week6/smoke/matrix.json` 加 row，不要绕过 harness）

### 3.5 cfg key 速查

| key | 取值 | 说明 |
|---|---|---|
| `solver` | `hllc \| rusanov` | flux scheme |
| `bc` / `bc_x` / `bc_y` | `outflow \| periodic \| reflective` | 全局 / 按轴边界 |
| `output_format` | `table \| binary` | 输出格式；GPU run 推荐 `binary` |
| `output_file` | path | binary 必填 |
| `progress_interval_s` | float | `<=0` 关闭进度输出 |
| `device`（**待 Week 6 新增**） | `cpu \| gpu` | overall.md 308–313 要求；Week 6 在 `main.cpp` 中加 |

---

## Part 4. Week 6 建议执行顺序（最小阻塞）

1. **Outflow BC kernel + CPU-vs-GPU grid diff**：最简单 kernel，立刻验证 `GpuGrid` 数据路径在真实 stencil 下的正确性。
2. **CFL reduction kernel**：deterministic reduction（建议 block-level reduce + atomic CAS for max），先做单元测试验证与 CPU 一致。
3. **Reconstruction / predictor device helpers**：MUSCL-Hancock 的逐 cell 计算；先在小 grid（如 16×16）做 unit test。
4. **HLLC flux kernel**：复用 `src/euler/hllc.hpp` 的纯函数实现（已 `__host__ __device__` 友好）；按 sweep 方向 dispatch。
5. **`EulerGpuSolver<Real>` orchestration**：组装 step loop（reconstruct → predict → flux → update + CFL），与 `EulerSolver` 对照 step-by-step grid diff（同一 IC + 同一 dt）。
6. **`main.cpp` cfg 接入 `device = gpu`**：保持 CPU 默认字节一致（即 `device` 缺省时走旧路径）。
7. **End-to-end CPU-vs-GPU regression**：对 Sod (1D) + LW Config 3 (2D) 跑 same-precision diff，要求 ≤ ULP-level；复用 `float_regression_report.py` 的 schema，把 float/double 行换成 cpu/gpu 行。
8. **C-pipeline 扩展**：如时间允许，补 LW Config 4 / Config 12 cfg（overall.md "if needed"）；否则推 Week 7。
9. **CSC GPU 节点 smoke**：本地 CUDA 稳定后再跑集群（Week 6 末或 Week 7 初）。

---

## Part 5. Week 6 开工前快速命令

```bash
# CPU 双精度 baseline 验证（保证 Week 5 状态可复现）
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double
./build-double/unit_tests "[boundary]" "[lw]" "[shock_bubble]"

# 启用 CUDA build（本地 GPU laptop）
cmake -B build-cuda-double -G Ninja \
  -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_CUDA=ON
cmake --build build-cuda-double

# Week 5 GPU roundtrip smoke（Week 6 起步基准）
./build-cuda-double/unit_tests "[gpu]"

# Week 5 已交付 IC 的 baseline 网格（GPU 验证 ground truth）
./build-double/hrsc tests/cases/liska_wendroff_2d/config6_n200.cfg
./build-double/hrsc tests/cases/shock_bubble/shock_bubble_n400x100.cfg

# Harness dry-run（Week 6 GPU smoke matrix 模板对照）
python scripts/run_matrix.py experiments/week5/smoke/matrix.json --dry-run
```

---

_维护约定：本 bridge 放在目标周目录（Week 6），作为 Week 6 计划与实现的前置上下文。Week 6 的 `week6-plan.md` / `week6-summary.md` 落地后，将本文件与 Part 1 的 "delivered" 状态保持同步。_
