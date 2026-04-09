# Week 2 Report: 1D Euler Solver

**日期:** 2026-04-09  
**分支:** main (`f8ce4d0..0feabad`)

---

## 1. 本周完成工作

### 1.1 实现模块

| 模块 | 文件 | 功能 |
|------|------|------|
| PrimVar 枚举 | `src/core/eos.hpp` | 原始变量语义索引 `{PRHO, VX, VY, PRES}` |
| 物理通量 | `src/euler/euler_flux.hpp` | `euler_flux_x(cons, gamma)` — x 方向 Euler 通量 |
| MUSCL 重构 | `src/euler/muscl.hpp` | `minmod` 限制器 + `muscl_reconstruct_x` 分段线性重构 |
| Hancock 预测 | `src/euler/hancock.hpp` | `muscl_hancock_x` — 半步时间演化预测器 |
| HLLC 求解器 | `src/euler/hllc.hpp` | `hllc_flux(qL, qR, gamma)` — HLLC 近似 Riemann 求解器 |
| 求解器类 | `src/euler/euler_solver.hpp` | `EulerSolver<Real>` — CFL 时间步、主循环 |
| 测试工况 | `tests/cases/toro_1d/` | Toro Tests 1-5 初始条件 + 配置文件 |
| 主程序 | `src/main.cpp` | 读配置 → 初始化 → 求解 → 输出原始变量 |
| 验证脚本 | `scripts/verify_toro.py` | 精确 Riemann 解 + 误差计算 + 可视化 |

### 1.2 算法流程

```
每个时间步:
  1. apply_outflow_bc()        — 填充 ghost cells
  2. compute_dt()              — CFL 条件: dt = CFL * dx / max(|u|+a)
  3. 对每个界面 k:
     a. muscl_hancock_x(左单元) → 获得 qL_right（右面值）
     b. muscl_hancock_x(右单元) → 获得 qR_left （左面值）
     c. hllc_flux(qL_right, qR_left) → 界面通量
  4. 守恒更新: U_i -= (dt/dx) * (F_{i+1/2} - F_{i-1/2})
```

### 1.3 测试覆盖

- **单元测试:** 70 test cases, 1254 assertions, 全部通过
- **涵盖:** EOS、minmod、MUSCL 重构（均匀/线性/间断场）、Hancock（均匀/线性）、HLLC（恒等/Sod/对称）、求解器集成（密度范围/质量守恒/激波位置）

---

## 2. 验证结果：Toro 1D 测试集

### 2.1 误差汇总（200 网格，L1 范数）

| 测试 | 描述 | rho L1 | u L1 | p L1 |
|------|------|--------|------|------|
| Test 1 | Sod 激波管 | 3.75e-3 | 5.04e-3 | 2.57e-3 |
| Test 2 | 123 问题（对称稀疏波） | 8.25e-3 | 1.69e-2 | 2.67e-3 |
| Test 3 | Woodward-Colella 爆炸波 | 9.44e-2 | 2.37e-1 | 4.63e+0 |
| Test 4 | Lax 问题 | 9.89e-3 | 1.10e-2 | 1.18e-2 |
| Test 5 | 慢速接触间断 | 2.78e-1 | 7.57e-2 | 6.36e+0 |

### 2.2 结果分析

**Test 1 (Sod):** 稀疏波、接触间断、激波三种结构均被清晰捕捉。密度/压力/速度与精确解吻合到 3 位有效数字。L1 误差 O(10⁻³)，符合二阶格式在 200 网格上的理论预期。

**Test 2 (123):** 对称两侧稀疏波产生近真空中心区域。数值解正确捕捉了低密度区域，未出现负密度或负压。

**Test 3 (Blast wave):** 压力比 10⁵:1 的极端工况。误差较大是因为强激波和接触间断在 200 网格上的分辨率不足，但解的结构定性正确，未出现非物理振荡。

**Test 4 (Lax):** 非对称状态，包含左行稀疏波和右行激波。误差与 Test 1 同量级，表现良好。

**Test 5 (Slow contact):** 高速相向碰撞产生极强激波。L1 误差较大但定性结构完全正确。这是对数值格式最严苛的测试之一。

### 2.3 可视化

![Toro Summary](toro_summary.png)

各测试详细 4 面板图（密度、速度、压力、比内能）：
- [Test 1: Sod](sod_verification.png)
- [Test 2: 123](toro2_verification.png)
- [Test 3: Blast](toro3_verification.png)
- [Test 4: Lax](toro4_verification.png)
- [Test 5: Slow Contact](toro5_verification.png)

---

## 3. 问题与思考

### 3.1 RIEMANN_STRICT_INEQUALITY 的影响

实现过程中发现：HLLC 的 flux 选择逻辑中，S* = 0 时使用严格不等式 (`<`) 和非严格不等式 (`<=`) 会产生不同行为。对于完全对称的 Riemann 问题（u_L = -u_R），S* 恰好为零，严格不等式导致两个 star region 都不被选中，回退到 F_R。这不影响实际求解（Sod 等非对称问题不受影响），但说明了 Riemann 求解器在退化情况下的脆弱性。

**结论：** 默认使用非严格不等式 (`<=`)，保持对称性。通过 CMake 选项保留切换能力。

### 3.2 GridView 的模板参数推导

`muscl_reconstruct_x` 的签名最初设计为 `ConstGridView<Real, 4>`，但从 mutable `GridView`（`Real*`）到 `ConstGridView`（`const Real*`）的隐式转换在模板推导中失败。解决方案是将函数模板化为 `GridViewBase<Real, 4, Ptr>`，同时接受 const 和 non-const 视图。这个模式贯穿了 MUSCL → Hancock 整条链路。

**Week 3 注意:** 如果添加 y 方向重构，应延续相同的 `GridViewBase` 模板模式。

### 3.3 Hancock 预测器的效果

对于 Test 2（近真空问题），Hancock 半步预测器至关重要。如果去掉半步演化（退化为纯 MUSCL + HLLC），在低密度区域容易产生负压。Hancock 的 flux-difference 修正有效地稳定了面值预测。

### 3.4 接下来的工作方向

- **网格收敛测试:** 在 50/100/200/400/800 网格上运行 Sod，验证 L1 误差的收敛阶（期望 ~1.5-2.0 阶，受限制器和间断影响）
- **Week 3 计划:** 精确 Riemann 求解器、y 方向扩展、2D 结构

---

## 4. 构建与运行

```bash
# 构建
cmake -B build -S . -G Ninja && cmake --build build

# 单元测试
PATH="/c/Strawberry/c/bin:$PATH" ./build/unit_tests

# 运行 Sod 测试
PATH="/c/Strawberry/c/bin:$PATH" ./build/hrsc tests/cases/toro_1d/sod.cfg > output/sod_result.txt

# 运行全部 Toro 测试并生成验证图
python scripts/verify_toro.py
```
