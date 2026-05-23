# Findings: C1-C5 Strict Review (2026-05-23)

## 机械验证结果

| 检查项 | 结果 |
|---|---|
| 禁用词 TODO/week#/D1/D2/HLLC-fill/config12/P1/USE_GPU/Lyapunov | C1-C5 全部 0 命中 ✓ |
| "vertical interface" / "well resolved in binary64" / "rows" 误用 | C1-C5 全部 0 命中 ✓ |
| 未编号 `\[ \]` displayed equations | C1-C5 全部 0 命中 ✓ |
| 所有 `p32` 实例 | C2、C4 各处都明确写 "not IEEE binary32/fp32" ✓ |
| Cite keys 存在性 (18 关键键) | 17/18 OK; `davis_1988` 缺失（已按 prompt 通过 Toro fallback 处理）✓ |
| 章节边界 `% <<SECTION_n_BEGIN/END>>` | 全部存在 |
| Liska-Wendroff 命名 | "configuration 3 (LW3)" / "configuration 12 (LW12)" 一致 ✓ |
| Chapter 6 状态 | 仅占位 + TODO，未撰写正文 ⚠ |
| Chapter 7 状态 | 已起草、覆盖结论要素 ✓ |

## 字数估算（LaTeX 原始 `wc -w`，含表格/公式）

| Ch | LaTeX 词数 | 目标 (Overleaf) | 评估 |
|----|----|----|----|
| C1 | 609 | 500-600 | 略紧；正文 ~470，处于上限附近 ✓ |
| C2 | 1045 | 850-950 | 含 4 个公式块；正文估 ~780 ✓ |
| C3 | 2204 | 1200-1350 | 含 25+ 公式 + 2 表 + 1 TikZ；正文估 ~1300-1400，可能略超上限 |
| C4 | 1628 | 950-1100 | 含 3 表 + 1 algorithm box；algorithm 计入 Overleaf 计数；正文估 ~900-1000 ✓ |
| C5 | 2924 | 1800-1950 | 含 5 表 + 8 figures；正文估 ~1700-1850 ✓ |

C3、C5 需在 Overleaf 实测 `texcount` 验证；初步看处于上限边缘。

## 覆盖率审计：原始要求 (Project Brief Report 1)

### Literature review & background [20%]
| 子项 | 覆盖位置 | 状态 |
|---|---|---|
| Euler 概览 | C2 §2.1 (完整公式块 + ideal-gas closure + γ 定义) | ✓ |
| Ideal-MHD 概览 | C2 §2.2 (含 ∇·B=0 解释), C3 §3.6 (含波速、Dedner、Evans-Hawley) | ✓ |
| 有限体积法基本推导 | C2 §2.3 文献层 + C3 §3.1 完整守恒推导 | ✓ |
| 浮点 + 硬件/编译器/并行影响 | C2 §2.4 完整 (含 exponent range, unit roundoff, non-associativity 例子, -O3 vs -Ofast, FMA, reduction) | ✓ |

### Mathematical theory [20%]
| 子项 | 覆盖 | 状态 |
|---|---|---|
| Explicit Riemann-solver-based 方法 (MUSCL-Hancock 或 WAF) | C3 §3.1-3.4 完整描述 MUSCL-Hancock + HLLC | ✓ |
| MHD 特定 numerical variations (不同 Riemann solver, divergence cleaning) | C3 §3.6 (Dedner 全公式 + Evans-Hawley CT 提及) | ⚠ 未具体命名 MHD 专用 Riemann solver (Roe-MHD/HLLD) — 浅 |
| 可变 algorithm 点 (`<` vs `<=` 等) | C3 §3.5 三组明确分类 (measured/concept-only/Report 2) | ✓ |
| Brief 要求的 "near zero" 警告 | C3 line 378-379 ✓ |

### Code description [20%]
| 子项 | 覆盖 | 状态 |
|---|---|---|
| AMReX 或 stand-alone 选择 + 多核 CPU/GPU 实现 | C4 §4.1 stand-alone, 表 mapping `FLOAT_PRECISION→HRSC_REAL`, `ENABLE_CUDA` | ✓ |
| Ease-of-implementation / optimization 特征 | C4 §4.2 mentions OpenMP static, 16×16 thread blocks, Kahan summation, deterministic CFL | ⚠ outline §4.1 列出的 4 项 (fp templating, CMake CUDA, regression harness, matched-binary switch) 未明确编号呈现，但内容大体到位 |
| Testing framework + 可重复 reproducibility | C4 §4.2 提到 "configuration, build, run, measurement, aggregation, plotting" 序列 + 元数据保存 | ✓ (但简略) |
| 编译器/浮点 tolerance 范围的探索方式 | C4 §4.3 表 tab:ch4-strict-flags 列 CPU/CUDA 各 flag | ✓ |
| 参考解的获得方法 | C4 §4.5 (exact Riemann + 高分辨率 fp64 numerical reference + cell averaging downsample) | ✓ |

### Validation [20%]
| 子项 | 覆盖 | 状态 |
|---|---|---|
| ≥4 个 Euler ideal-gas 测试，含超声速波，含 1D+2D | C4 表: Sod, Toro3, Toro5, LW3, LW12; supersonic 标注 4 处 (Toro3/Toro5/LW3/LW12) | ✓ |
| CPU + GPU 评估 | C5 §5.5 全 5 case CPU/GPU matched | ✓ |
| CPU/GPU 差异定量 | C5 表 tab:ch5-cpu-gpu (零差异 + checkpoint counts) | ✓ |
| Single vs double precision 比较 | C5 §5.4 + R_ref 比较 | ✓ |

### Quality of write-up [20%]
| 子项 | 覆盖 | 状态 |
|---|---|---|
| 结构与排版 | 章节结构完整 (除 C6 未完成); 公式编号一致 | ⚠ C6 placeholder 影响整体完成度 |
| 图表可读性 / caption | C5 captions 含 grid/time/solver/reference — ✓; 但 tab:ch5-1d-summary 仍有 6-7 位有效数字 (导师要求 3-4 位) | ⚠ |
| Completeness | C1-C5 内部完整; C6 未写; C7 已写 | ⚠ |
| References 数量/合理性 | C1=3, C2=11, C3=19, C4=10, C5=8 cite 命令；类别多样、均有出处 | ✓ |

## 覆盖率审计：导师反馈逐项 (supervisor_feedback_map.md)

### Chapter 1
- 1.1 应用与精度-速度权衡：✓ "high-speed gas dynamics, aerospace or engineering applications"
- 1.2 CFD 精度文献：✓ Brogi + Wang/Xia/Chen
- 1.3 CUDA/GPU 背景：✓ 定义 + 提到 throughput 差异 (无未验证产品声明，符合 prompt 限制)
- 1.4 Roadmap 避免内部规划语：✓ "Chapter X reviews/defines/reports..."

### Chapter 2
- 2.1 γ + E + p 定义：✓ line 41-47
- 2.2 MHD 方程块 + ∇·B=0 含义：✓ 完整
- 2.3 不超前用 HLLC：✓ "deferred to Chapter 3"
- 2.4 exponent range + unit roundoff + non-assoc 例 + -O3 vs -Ofast + reciprocal/sqrt + Verificarlo + p32≠fp32：✓ 全部到位
- 2.5 gap statement：✓ 简洁分组+前瞻

### Chapter 3
- 3.1 CFL preview：✓ + 全公式编号
- 3.2 slope-limiting 必要性 + TVD 定义：✓
- 3.3 "vertical" 去除 + Davis-via-Toro + HLLC 分支互斥 + author-name：✓
- 3.4 CFL 公式排序 + νx/νy 定义后 + label sec:ch3-stability：✓
- 3.5 "sufficiently accurate" 措辞 + FMA hw/compiler 警告 + 三宏 table + arraystretch + "near zero" 警告 + 三类 axes 分组：✓ 全部
- 3.6 MHD 方程块 + 波族 + Dedner 全公式 + Evans-Hawley + Report 1 boundary：✓
- **缺失**：MHD-specific Riemann solver (Roe/HLLD) 未命名 — brief 子项 (b) 字面是 "different Riemann solvers OR divergence cleaning"，divergence cleaning 已覆盖，但补一句更扎实

### Chapter 4
- AMReX 移除：✓ 完全未出现
- FLOAT_PRECISION 代码示例：✓ 表
- Boost::Multiprecision 边界：✓
- Toolchain split：✓
- CUDA / thread block / OpenMP 定义：✓
- CFL = max/min 不是 summation：✓ 明确说出
- "matched device evidence" 定义：✓ line 107-110
- Flag table (`-ffp-contract=off` 等)：✓
- SSIM 定义：✓ "image-structure similarity; values near 1..."
- R_ref 含义 (小=好, 接近1=可比, =0 退化)：✓
- 初值条件 / Toro & LW：表中给出 wave content；具体数值初值未列（依赖 Toro/Liska-Wendroff 标准引用） — 可接受
- 表行距：✓ `\arraystretch=1.16`
- 参考下采样 (block averaging)：✓ 含具体 4×4/8×8/2×2 映射

### Chapter 5
- 5.2 caption 含 N + t + MUSCL-Hancock + HLLC + Exact reference：✓
- 5.2 表 caption 解释 L_1 是 conservative state on fp64-fp32：✓
- 5.3 captions 含 HLLC + grid + time + 参考类型：✓
- **5.3 表 tab:ch5-2d-summary 数字 3-4 位**：✓ (4.95e-3, 0.9817...)
- **⚠ 5.2 表 tab:ch5-1d-summary 仍是 6-7 位有效数字 (8.743340×10⁻⁸)** — 导师明确要求 3-4 位
- 5.4 LW12 上右区域 bounded 解释：✓ 含 "does not prove a specific HLLC branch changed"
- 5.4 stationary-contact ∞ 标为 degenerate：✓
- 5.5 zero-tables 压缩：✓ 单表 + footnote + toolchain split
- 5.6 Table 5.5 替换为 per-case verified：✓ (tab:ch5-variation)
- 5.6 fp32 flag 表 per-case：✓ tab:ch5-fp32-flags
- 5.6 "P1" 改为 "supplementary GPU flag probe"：✓
- 5.6 drift-slope 表删除：✓
- 5.6 Figure 5.9 caption 解释 overlapping curves：✓
- 5.6 Toro2/Toro-123 限位措辞：✓ "Non-completion within the 600 s limit was observed; the mechanism was not diagnosed in Report 1."
- 5.6 limiter 不报告 (作为 limitation)：✓
- **⚠ schlieren 黑白**：caption 未确认 / 实际图未审查 — 可能仍是彩色

## 章节职能独立性 / 跨章一致性

| 维度 | 评估 |
|---|---|
| C1 不出现方法推导/数字/HLLC 细节 | ✓ |
| C2 不重复 C3 (HLLC 推导 deferred) | ✓ |
| C3 不出现 design matrix / 测得数字 | ✓ |
| C4 不出现 measured results | ✓ (只列 reference 策略与 metric 定义) |
| C5 不重复 C4 design rationale | ✓ ("design matrix...is fixed in Table~ch4...; the role of this chapter is to interpret") |
| 符号一致：U, F, G, ρ, u, v, E, p, γ, c, Δt, ν, S_L/S_*/S_R | ✓ 跨章一致 |
| Cross-references: \ref{eq:ch4-rref}, \ref{tab:ch4-design-matrix}, \ref{sec:ch3-stability} | 看起来正确 |
| Verificarlo 角色：C1 introduce → C2 mechanics → C4 实施 → C5 不依赖 p32 | ✓ |

## 待改进点 (按影响排序)

1. **C6 未撰写** — 报告结构不完整 (placeholder + TODO)。C1 §1.4 roadmap 承诺 Chapter 6 "discusses interpretation, uncertainty, and limitations" 但实际为空。这是当前最大单点缺陷，对整体分数（特别是 Quality of write-up [20%]）有直接负面影响。
2. **C5 tab:ch5-1d-summary 仍为 6-7 位有效数字** — 导师明确要求 3-4 位。同样问题在 C5 正文若干 inline 数值 (e.g. "$6.386967\times10^{-5}$", "$1.364064\times10^{-5}$")。
3. **C3 §3.6 未命名 MHD-specific Riemann solver** — brief 字面 "different Riemann solvers" + divergence cleaning 二选一即可，已选后者，但补一句 (HLLD / Roe-MHD) 可让 brief sub-bullet (b) 显著完成。
4. **C4 §4.2 "ease-of-implementation" 4 项未编号呈现** — outline 列出 4 项但 C4 §4.1/§4.2 散落于多段，未明确"我实现了 X、Y、Z、W"列表式呈现。code description [20%] 子项 1 的可识别度略弱。
5. **C5 schlieren 配色未确认黑白** — 导师明确要求 schlieren 黑白便于与文献比较；当前 caption 无说明，文件未审查，潜在风险。
6. **C5 中部分 inline 数值过精** — supervisor "interpretation, not repeated numbers" 反馈 — 多处 6-7 位精度数值出现于正文，应保留 3-4 位 + 一句解释相对尺度。
7. **C3 §3.5 word budget** — `texcount` 估值未实测；如超 1350 需进一步压缩。
8. **C4 §4.2 Algorithm box 长度 + Kahan summation 必要性** — algorithm 在 Overleaf 计数；当前 7 行紧凑，但 Kahan 引用 (`\citep{higham_2002}`) 在 algorithm 内偏冗余。
9. **C5 reference-scaled ratio R_ρ^ref 在两个 2D 表中数字相同但 LW12 一列正文写 "1.30×10⁻⁴" 而表中是 "1.30×10⁻⁴"** — 一致。但 C7 line 27 写 "1.300607×10⁻⁴" — C5 (3 sig fig) 与 C7 (7 sig fig) 不一致；非主审范围但暴露同一倾向。
10. **C1 cite 数量偏少 (3)** — 对长度 500-600 词的 introduction 是合理的；不构成缺陷，但若想达到 95+，可在 §1.2 加 1 处 Higham 或 IEEE 754 引用直接挂到 unit-roundoff 概念。
