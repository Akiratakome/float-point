# Week 3 → Week 4 衔接文档

**Date:** 2026-04-21
**Branch:** `week3-implementation`
**Current phase:** Week 4 starting (based on overall.md schedule: Week 4 = 2026-04-13 ~ 2026-04-19, Week 5 = 2026-04-20 ~ 2026-04-26)

本文档作为 Week 3 → Week 4 的交接:
- Part 1. **Week 3 已完成工作**（比原计划多做了一些 Week 4 的内容）
- Part 2. **Week 4 剩余工作**（按 `overall.md` 的原计划）
- Part 3. **可用接口清单与使用示例**

---

## Part 1. Week 3 已完成工作（Summary）

### 1.1 原 Week 3 计划（overall.md 第 244–264 行）完成情况

| 计划项 | 文件 | 状态 |
|---|---|---|
| 完整 Toro 1-5 IC | [tests/cases/toro_1d/toro_tests.hpp](../../tests/cases/toro_1d/toro_tests.hpp) | ✅ (Week 2 提前完成) |
| 各 Toro 的 `.cfg` | [tests/cases/toro_1d/](../../tests/cases/toro_1d/) | ✅ Sod/Toro2/Toro3/Toro4/Toro5/Stationary-contact |
| Stationary contact | [tests/cases/toro_1d/stationary_contact.cfg](../../tests/cases/toro_1d/stationary_contact.cfg) | ✅ S_M=0 edge case 专用 |
| Exact Riemann solver (C++) | [src/euler/exact_riemann.hpp](../../src/euler/exact_riemann.hpp) | ✅ Newton-Raphson + 采样 |
| Binary IO | [src/utils/io.hpp](../../src/utils/io.hpp) | ✅ 64-byte header + 强制 little-endian |
| Error norms | [src/utils/error_norms.hpp](../../src/utils/error_norms.hpp) | ✅ L1 / L2 / Linf, 1D+2D 通用 (`dV = dx` 或 `dx·dy`) |
| Van Leer / MC 限幅器 | [src/euler/muscl.hpp](../../src/euler/muscl.hpp) | ✅ vanleer/superbee/vanalbada；MC 按用户决定**跳过** |
| `analysis/compare.py` | [scripts/run_comparison.py](../../scripts/run_comparison.py) | ✅ 命名与 overall.md 稍异，功能等价 |
| `analysis/plot_1d.py` | [scripts/verify_toro.py](../../scripts/verify_toro.py) | ✅ |

### 1.2 提前完成的 Week 4 内容

Week 3 期间已经把 overall.md **Week 4 计划** 的 2D 扩展也做完了（见近期提交 `c9f3e05`, `cc62cb1`, `ad55c44`）:

| Week 4 planned item | 文件 | 实现状态 |
|---|---|---|
| `euler_flux_y` (G(U)) | [src/euler/euler_flux.hpp](../../src/euler/euler_flux.hpp) | ✅ |
| `muscl_reconstruct_y` | [src/euler/muscl.hpp](../../src/euler/muscl.hpp) | ✅ |
| `muscl_hancock_y` | [src/euler/hancock.hpp](../../src/euler/hancock.hpp) | ✅ |
| `y_sweep()` + 交替分裂 | [src/euler/euler_solver.hpp](../../src/euler/euler_solver.hpp) | ✅ 偶步 X→Y, 奇步 Y→X (Godunov splitting) |
| 2D CFL: `dt = CFL·min(dx/S_x, dy/S_y)` | [src/euler/euler_solver.hpp:144-174](../../src/euler/euler_solver.hpp#L144-L174) | ✅ `compute_dt()` |
| y-direction HLLC (via momentum swap) | [src/euler/euler_flux.hpp:48-51](../../src/euler/euler_flux.hpp#L48-L51) | ✅ `swap_momentum()` |
| 1D 兼容构造 | [src/euler/euler_solver.hpp:129-132](../../src/euler/euler_solver.hpp#L129-L132) | ✅ `ny=1` 走纯 X-sweep |

### 1.3 Week 4 中做的**额外**工作（为回应导师 Philip 的邮件）

Philip 2026-04-10 要求比较 SLIC 与 HLLC 的浮点敏感性。详见 [docs/week3/week3_summary.md](../week3/week3_summary.md)（文件名是 week3 但内容标题是 Week 4，属于邮件回复专题）。核心结论:

- 用 **Rusanov (Local Lax-Friedrichs)** 代替 SLIC，保留原 MUSCL-Hancock 流水线，接口与 `hllc_flux` 完全一致（drop-in）。
- 通过 `FluxScheme` enum + 配置文件 `solver=hllc|rusanov` 运行期切换。
- Verificarlo MCA 结果: HLLC 与 Rusanov 在 double (p=53) 和 float (p=24) 下的最小显著位数几乎相同（差异 <0.5 位），证明 **Riemann solver 选择不是 FP 精度瓶颈**。
- HLLC 的 4-way 分支 (`SL>=0`, `S_star`, `SR<=0`) 在标准 Toro 测试、200 cells、30-bit VPREC 下也不会翻转（无不稳定分支）。

新增资产:
- [src/euler/rusanov.hpp](../../src/euler/rusanov.hpp)
- [tests/cases/toro_1d/*_rusanov.cfg](../../tests/cases/toro_1d/) × 7
- [scripts/plot_vfc_hllc_vs_rusanov.py](../../scripts/plot_vfc_hllc_vs_rusanov.py), [scripts/plot_stationary_contact_vfc.py](../../scripts/plot_stationary_contact_vfc.py), [scripts/run_comparison.py](../../scripts/run_comparison.py)
- [scripts/verificarlo_run.sh](../../scripts/verificarlo_run.sh) 加了 `--solver` flag 与 `--inst-fma` / VPREC 分支检测

### 1.4 刚完成的代码排雷（2026-04-21）

- 引入 [src/core/eos.hpp](../../src/core/eos.hpp#L22) 中的 `constexpr int EulerNVars = 4;`，把散落的硬编码 `4` 全替换为此常量（11 个文件改动），避免将来接入 MHD (NVars=9) 时遗漏同步。
- `.gitignore` 增加 `/hrsc_vfc`，291 KB 的 Verificarlo 二进制不再出现在 status 中。
- 文件 `docs/requirement/staged-sniffing-bunny.md` → `docs/requirement/overall.md` rename 被 git 正确识别。
- **验证**: 重建后 107 个 test cases / 3403 assertions 全绿；Sod 端到端 137 步, t=0.25 正常完成。

### 1.5 测试覆盖（Catch2）

| 文件 | 行数 | 内容 |
|---|---|---|
| [tests/unit/test_vec.cpp](../../tests/unit/test_vec.cpp) | 144 | 通用 `Vec<T,N>` 运算 |
| [tests/unit/test_grid.cpp](../../tests/unit/test_grid.cpp) | 111 | Grid2D / GridView / 索引 |
| [tests/unit/test_eos.cpp](../../tests/unit/test_eos.cpp) | 102 | pressure/sound_speed/prim-cons 往返 |
| [tests/unit/test_boundary.cpp](../../tests/unit/test_boundary.cpp) | 123 | outflow BC（1D + 2D 角落） |
| [tests/unit/test_config.cpp](../../tests/unit/test_config.cpp) | 121 | 配置解析 |
| [tests/unit/test_euler.cpp](../../tests/unit/test_euler.cpp) | 918 | flux / MUSCL / Hancock / HLLC / Rusanov / 2D solver |

运行总计: **107 cases, 3403 assertions, all pass**。

---

## Part 2. Week 4 剩余工作（按 overall.md Week 4 原计划）

Week 4 原计划（overall.md 266-275 行）四项中已完成 2 项，剩 2 项:

### 2.1 Precision templating 基础设施 ⚠️

**状态:** 源码已经 `template <typename Real>` 全覆盖，**但构建系统仍只编译 `double`**。

overall.md 要求:
- `cmake/PrecisionConfig.cmake` — 构建时选 float/double/quad
- Root CMake 选项 `FLOAT_PRECISION = float | double | quad`
- 整条 pipeline 能以 `float` 实例化并跑通 Sod

**需要做的:**
1. 新增 [cmake/PrecisionConfig.cmake](../../cmake/PrecisionConfig.cmake)（文件目前不存在）提供 `HRSC_REAL` 宏或 `using Real = ...` 的 typedef 头。
2. 改 [src/main.cpp](../../src/main.cpp) 的 `EulerSolver<double>` 为 `EulerSolver<Real>`（`Real` 由构建选项决定）。
3. 新增 explicit instantiation 单元 `src/euler/euler_solver_float.cpp` / `_double.cpp` — 其实**不需要**，因为所有 Euler 代码都是 header-only。PrecisionConfig 只需把 `Real` 定义提供给 `main.cpp` 即可。

**最小改动路径（建议）:**
```cmake
# cmake/PrecisionConfig.cmake
set(FLOAT_PRECISION "double" CACHE STRING "float | double")
set_property(CACHE FLOAT_PRECISION PROPERTY STRINGS float double)
target_compile_definitions(hrsc PRIVATE HRSC_REAL=${FLOAT_PRECISION})
```
然后在 `main.cpp`:
```cpp
using Real = HRSC_REAL;
EulerSolver<Real> solver(...);
```
单元测试已经用 `TEMPLATE_TEST_CASE(..., float, double)` 在两个精度下跑过，所以精度分支的计算正确性已经验证。

### 2.2 2D 的 periodic / reflective 边界条件 ⚠️

**状态:** 目前只有 `apply_outflow_bc()`，位于 [src/core/boundary.hpp](../../src/core/boundary.hpp)。overall.md Week 4 要求加 periodic 和 reflective 以支持后续 2D 测试（Kelvin-Helmholtz 需 periodic，Liska-Wendroff 需 outflow，shock-bubble 可能需 reflective）。

**需要新增的接口（建议签名）:**
```cpp
template <typename Real, int NVars>
void apply_periodic_bc(GridView<Real, NVars> grid);          // 左↔右、下↔上 周期性拷贝

template <typename Real, int NVars>
void apply_reflective_bc(GridView<Real, NVars> grid,
                         int momentum_x_index = RHOU,
                         int momentum_y_index = RHOV);         // 法向动量分量取反
```
**要注意:** `apply_reflective_bc` 反射时需要把法向动量（X 边界是 `RHOU`，Y 边界是 `RHOV`）取负号，其他分量镜像。EulerNVars 的顺序是 {RHO, RHOU, RHOV, EN}，所以一般只翻 index 1 或 2。函数模板化、`NVars` 做参数，将来 MHD (B 场法向也要翻) 可以再派生或用 traits。

**调用点:** [src/euler/euler_solver.hpp::step()](../../src/euler/euler_solver.hpp#L176-L200) 当前只调 `apply_outflow_bc`。需要让 BC 类型**可配置**——比如加一个 `BoundaryType` enum + 构造器参数，或在 2D 测试 cfg 中加 `bc = outflow|periodic|reflective`。

**优先级:** 必须在 Week 5 开始 2D 测试（Liska-Wendroff、Kelvin-Helmholtz）前完成。

### 2.3 可选 / 衍生

- **Verificarlo 在 float 精度下重跑**: 现有 MCA 都是 double（p53）和 VPREC 精度扫描。一旦 Week 4 的 float 构建跑通，可以直接把 p24 Verificarlo 运行对齐到**真正的 float 编译产物**而非 VPREC 模拟——这对 Report 1 的"float vs double"章节更有说服力。
- **FMA control** 已经通过 `scripts/verificarlo_run.sh --inst-fma` 做过；原计划写入 `cmake/CompilerFlags.cmake` 的 `FMA_CONTRACT` 选项仍未接入主构建系统。overall.md 把它标为 secondary，可延后到 Week 17。

---

## Part 3. 可用接口清单与使用示例（供 Week 4+ 使用）

### 3.1 核心常量与类型

```cpp
#include "core/types.hpp"       // HD_FUNC, NgHost=2, Constants<Real>::Gamma
#include "core/vec.hpp"         // Vec<Real,N>
#include "core/eos.hpp"         // EulerNVars=4, EulerVar enum, PrimVar enum
```

| 符号 | 定义处 | 说明 |
|---|---|---|
| `HD_FUNC` | `core/types.hpp` | `__host__ __device__` under NVCC, empty otherwise |
| `NgHost` | `core/types.hpp` | `constexpr int = 2`, 每边 ghost 层数 |
| `EulerNVars` | `core/eos.hpp:22` | `constexpr int = 4`, 2D Euler 守恒变量数 |
| `EulerVar` | `core/eos.hpp:13` | `{RHO=0, RHOU=1, RHOV=2, EN=3}` |
| `PrimVar` | `core/eos.hpp:16` | `{PRHO=0, VX=1, VY=2, PRES=3}` |

### 3.2 Grid 与 View

```cpp
#include "core/grid.hpp"

Grid2D<Real, EulerNVars> grid(nx, ny);   // owning, zero-initialised
grid.dx = Lx / nx;
grid.dy = Ly / ny;

auto gv = grid.view();                    // GridView (mutable)
gv(i, j, var) = value;                    // i ∈ [0, nx), j ∈ [0, ny)
gv(-1, j, var);                            // ghost access up to ±NgHost layers

// 1D 用法: ny=1, 所有 j=0
Grid2D<Real, EulerNVars> grid1d(nx, 1);
```

GridView 可以传给 `GridViewBase<Real, EulerNVars, Ptr>` 模板参数，这是 MUSCL/Hancock 的输入类型（同时接受 mutable 和 const）。

### 3.3 EOS

```cpp
Vec<Real, EulerNVars> cons = {rho, rho*u, rho*v, E};
Real p = pressure(cons, gamma);
Real a = sound_speed(rho, p, gamma);
auto prim = cons_to_prim(cons, gamma);    // {rho, u, v, p}
auto back = prim_to_cons(prim, gamma);
```

### 3.4 Flux 与 Riemann solver

```cpp
#include "euler/euler_flux.hpp"
#include "euler/hllc.hpp"
#include "euler/rusanov.hpp"

// Physical flux
Vec<Real, EulerNVars> Fx = euler_flux_x(cons, gamma);
Vec<Real, EulerNVars> Fy = euler_flux_y(cons, gamma);

// Interface flux (x-direction)
Vec<Real, EulerNVars> F = hllc_flux   (qL, qR, gamma);
Vec<Real, EulerNVars> F = rusanov_flux(qL, qR, gamma);

// y-direction: 旋转法向动量后复用 x-方向 solver
auto rotL   = swap_momentum(q_bottom);
auto rotR   = swap_momentum(q_top);
auto F_iface = hllc_flux(rotL, rotR, gamma);
auto G       = swap_momentum(F_iface);   // rotate back
```

`hllc_flux` 的分支不等式受编译宏 `RIEMANN_STRICT_INEQUALITY` 控制（关 = `<=`, 开 = `<`），对应 [overall.md:126-134](../requirement/overall.md#L126-L134) 的核心实验变量。

### 3.5 MUSCL reconstruction + Hancock 半步

```cpp
#include "euler/muscl.hpp"
#include "euler/hancock.hpp"

Vec<Real, EulerNVars> qL, qR;

// X 方向（默认 Minbee）
muscl_hancock_x(gv, i, j, dt, gamma, qL, qR);

// 换限幅器
muscl_hancock_x(gv, i, j, dt, gamma, qL, qR, VanLeerLimiter{});
muscl_hancock_x(gv, i, j, dt, gamma, qL, qR, SuperbeeLimiter{});
muscl_hancock_x(gv, i, j, dt, gamma, qL, qR, VanAlbadaLimiter{});

// Y 方向
Vec<Real, EulerNVars> qB, qT;
muscl_hancock_y(gv, i, j, dt, gamma, qB, qT);
```

Limiter 是通过仿函数对象在编译期注入的（零运行时开销）。如果 Week 4 需要按 cfg 运行期切换，需要在 solver 里加一个 enum dispatch，类似 `FluxScheme` 的做法。

### 3.6 Solver 类

```cpp
#include "euler/euler_solver.hpp"

// 1D convenience
EulerSolver<double> solver(nx, dx, xmin, gamma, cfl, t_end, FluxScheme::HLLC);

// 2D full
EulerSolver<double> solver(nx, ny, dx, dy, xmin, ymin,
                           gamma, cfl, t_end, FluxScheme::HLLC);

// 初始化 IC（通过 grid_view() 拿到可写视图）
setup_sod(solver.grid_view(), gamma);

solver.run();                    // 跑到 t_end
// 或手动:
// while (solver.time() < t_end) solver.step();

std::cout << solver.step_count() << " steps, t = " << solver.time();
```

2D 路径使用交替 Godunov splitting（偶步 X→Y，奇步 Y→X），每个半步之间重新 apply BC。1D 构造器 (`ny=1`) 只走 x-sweep，与 Week 2 字节一致的行为。

### 3.7 Exact Riemann reference

```cpp
#include "euler/exact_riemann.hpp"

// 在 x/t = ξ 位置采样精确解
Real rho, u, p;
exact_riemann_sample(gamma, xi,
    rhoL, uL, pL,
    rhoR, uR, pR,
    rho, u, p);
```

Newton-Raphson 迭代星区压力，然后沿 ξ=x/t 分类采样（左波 / 接触 / 右波）。用于 convergence 模式生成参考解，见 [src/main.cpp:111](../../src/main.cpp#L111)。

### 3.8 Error norms

```cpp
#include "utils/error_norms.hpp"

auto err = compute_error(num_ptr, exact_ptr, total_cells, dV);
// err.L1, err.L2, err.Linf
// dV = dx (1D) 或 dx * dy (2D)
```

### 3.9 IO（numpy 兼容）

```cpp
#include "utils/io.hpp"

write_binary("output/sod.bin", grid.view(), nx, ny, dx, dy, time);
// 64-byte header: magic="HRSC", nx, ny, nvars, sizeof(Real), time
// 强制 little-endian；跨 Win/Linux 一致
```

Python 侧用 `np.fromfile(..., dtype='<f8')` 直接读（shape = `(ny, nx, nvars)`）。

### 3.10 Config 解析

```cpp
#include "utils/config.hpp"

Config cfg(argv[1]);
int    nx    = cfg.get_int   ("nx", 200);
double cfl   = cfg.get_double("cfl", 0.8);
auto   grids = cfg.get_int_list("resolutions");
std::string solver = cfg.get_string("solver", "hllc");   // "hllc" | "rusanov"
```

在 [src/main.cpp](../../src/main.cpp) 中通过 `mode = normal | convergence` 切两种运行模式。

### 3.11 边界条件

**目前只有 outflow**:

```cpp
#include "core/boundary.hpp"

apply_outflow_bc(grid.view());    // 模板生效于任何 NVars（不只 Euler）
```

**Week 4 待加:** `apply_periodic_bc`, `apply_reflective_bc`（见 §2.2）。

### 3.12 构建与运行

```bash
# 配置 + 构建
cmake -B build -S . -G Ninja
cmake --build build

# 运行单元测试
build/unit_tests.exe                 # 全部 107 cases
build/unit_tests.exe "[hllc]"        # 按 tag 过滤
build/unit_tests.exe "[rusanov]"

# 跑 1D Toro 测试（输出 x  rho  u  v  p）
build/hrsc.exe tests/cases/toro_1d/sod.cfg          > out.txt
build/hrsc.exe tests/cases/toro_1d/sod_rusanov.cfg  > out_rusanov.txt

# Convergence 模式（多分辨率, 对比 exact）
build/hrsc.exe tests/cases/toro_1d/convergence_sod.cfg

# Verificarlo MCA（需要 Docker）
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd):/work" -w /work \
    verificarlo/verificarlo bash scripts/verificarlo_run.sh
```

---

## Part 4. Week 4 建议推进顺序

1. **PrecisionConfig.cmake + HRSC_REAL** — 1 天。最小路径（§2.1），立刻解锁 float vs double 真正 compiled 对比。
2. **periodic + reflective BC** — 1 天。按 §2.2 接口加，配 2 个 unit test（1D periodic = 左右卷绕；2D reflective = 动量翻转）。
3. **float 精度回归** — 0.5 天。把现有 6 个 Toro 1D 测试在 float 下跑一遍，对比 exact，看 L1 跟 double 的比值。这是 Report 1 validation 章节的直接素材。
4. **BC 可配置接入 solver** — 0.5 天。`cfg` 增加 `bc` 关键字，solver 构造器接受 `BoundaryType`。
5. **Week 5 切入 2D tests** — Liska-Wendroff config 3/6，shock-bubble。只有 2 和 4 步落地后才能开始。

---

## 附录: 关键文件地图

```
src/
  core/
    types.hpp       HD_FUNC, NgHost, Constants
    vec.hpp         Vec<Real,N>
    grid.hpp        Grid2D / GridView / GridViewBase
    eos.hpp         EulerNVars, EulerVar, PrimVar, pressure, cons<->prim
    boundary.hpp    apply_outflow_bc   (Week 4 待加 periodic/reflective)
  euler/
    euler_flux.hpp  euler_flux_x, euler_flux_y, swap_momentum
    muscl.hpp       minbee/vanleer/superbee/vanalbada, muscl_reconstruct_x/y
    hancock.hpp     muscl_hancock_x / _y
    hllc.hpp        hllc_flux (RIEMANN_STRICT_INEQUALITY 可切)
    rusanov.hpp     rusanov_flux (week 4 新增，无分支)
    exact_riemann.hpp  exact_riemann_sample
    euler_solver.hpp   EulerSolver<Real>, FluxScheme enum, 1D + 2D
  utils/
    config.hpp      Config key=value 解析
    io.hpp          write_binary / read_binary (little-endian)
    error_norms.hpp compute_error -> {L1, L2, Linf}

tests/cases/toro_1d/
  sod.cfg, toro2-5.cfg, stationary_contact.cfg          (HLLC, default)
  *_rusanov.cfg                                         (solver=rusanov 副本)
  convergence_sod.cfg, convergence_sod_rusanov.cfg      (多分辨率)
  toro_tests.hpp                                         setup_sod/toro2../stationary_contact

scripts/
  verify_toro.py             Python 的 exact Riemann + 1D profile 画图
  verificarlo_run.sh         Docker MCA 采样（--solver, --inst-fma, VPREC）
  verificarlo_analysis.py    sig-digit heatmap
  run_comparison.py          HLLC vs Rusanov 误差范数 + 对比图
  plot_vfc_hllc_vs_rusanov.py  MCA 敏感度对比
```

---

_最后更新: 2026-04-21. 107 / 3403 test cases/assertions 全通过。EulerNVars 重构已完成并验证。_
