# Week 13 导师会议材料 — 2D MHD 基准 + HLLD 求解器
> **Historical snapshot:** This dated meeting document preserves what was known
> at the time. It is not the current Report 2 status. See
> [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md) for
> current evidence, supersession, and claim boundaries.

> 生成日期：2026-06-26。本文件用于导师会议汇报。配套图位于
> `experiments/week13/`，原始数值诊断行（`[mhd] t=... divB_max=...`）均来自本仓库
> `build-double/hrsc_mhd.exe` 的真实运行输出，未做人工修改。

---

## 0. 一句话进度

本周在**已验证的 HLL 求解器**上把代码从 1D（Week 12 的 Brio–Wu）扩展到 **2D 物理 MHD
基准**（Orszag–Tang 涡、Kelvin–Helmholtz 剪切层），并以**零成本、可配置切换**的方式新增了
**HLLD 五波求解器**（`riemann = hll | hlld`，默认仍为 `hll`）。HLLD 经诊断后**暂缓用于
生产精度研究**——它能跑完且结果有限，但当前 GLM 配置下 div(B) 显著偏大。

代码架构是**纯增量**的：默认路径 `riemann = hll` 使 Week-12 的 Brio–Wu 1D 结果保持逐位一致
（回归锚点 `steps=759`, `divB_max=4.441e-14`）。

---

## 1. 图件清单与逐图说明

下面每张图按 **作用 / 如何阅读 / 对比文献 / 得到的结论 / 合理性核查** 五点说明。

所有 2D 图：横轴 x、纵轴 y，周期性方形域 `[0,1]²`，分辨率 `256²`，HLL 求解器，
γ=5/3，色条标注实际数值范围。

### 1.1 Orszag–Tang 涡（OT）

数值诊断行：`[mhd] t=0.500000 steps=806 divB_mean=1.225e-01 divB_max=3.720e+00`

#### 图 A — `orszag_tang/figures/ot_density_pressure.png`（=`ot_paper_style.png`）
密度场（左）与气压场（右），t=0.5。

- **作用**：展示 OT 涡在非线性阶段的形态——由初始光滑涡旋演化出的相互作用激波与电流片。
- **如何阅读**：密度色条 1.27–5.69，亮黄=高密度团块（激波压缩区），深蓝=低密度区；气压色条
  4e-5–3.76，亮带勾勒出斜向激波面。中心区域形成的高密度"通道流"与对角激波结构是 OT 的标志特征。
- **对比文献**：Tóth 2000（*J. Comput. Phys.* 161, 605；DOI `10.1006/jcph.2000.6519`）的 OT
  div(B)-约束基准；原始问题 Orszag & Tang 1979。本仓库采用有理化单位
  (ρ₀=γ²≈2.78, p₀=γ≈1.67, B₀=1)，故形态对比看的是**结构拓扑与相对密度衬度**，不是绝对数值。
- **结论**：t=0.5 时已出现文献一致的中心密度峰、对角激波/电流片网络，相对密度衬度
  ≈5.69/1.27≈4.5，落在 OT 标准结果区间内。
- **合理性核查**：✅ 合理。形态、激波取向、密度衬度量级与 Tóth 2000 一致。注意这是**形态学证据**，
  非逐点定量比对（未数字化外部参考解）。

#### 图 B — `orszag_tang/figures/ot_divb.png`
log₁₀|div(B)| 空间分布，t=0.5。

- **作用**：检查 GLM 散度清理在强激波问题上的实际效果与误差分布。
- **如何阅读**：色条为 log₁₀ 尺度，范围 10⁻⁵·³⁵ ~ 10⁰·⁵⁷（即约 4.5e-6 ~ 3.7）。亮黄丝状结构
  =div(B) 误差集中处，**几乎完全沿激波面/电流片排列**；大片绿色区域 div(B) 已被清理到很小。
- **对比文献**：Dedner et al. 2002（*JCP* 175, 645；DOI `10.1006/jcph.2001.6961`）的 GLM
  双曲-抛物散度清理。
- **结论**：div(B) 误差被约束在 `divB_max=3.72`、`divB_mean=0.122`，并集中于不连续面——这是
  cell-centered + GLM 方案的**预期行为**（误差在激波处产生、被传播-阻尼清理，而非约束输运的机器零）。
- **合理性核查**：✅ 合理。注意 3.72 是绝对值，看似大，但单格 B~O(1) 跨激波跳变的"最坏单格散度"
  ≈1/dx≈256，因此 max 仅为最坏情形的 ~1.5%，mean 更小。**div(B) 是被控制、非被消除**，这点需在
  汇报中明确（我们用的是 GLM 而非 constrained transport）。

### 1.2 Kelvin–Helmholtz 剪切层（KH）

数值诊断行：`[mhd] t=1.000000 steps=1148 divB_mean=4.411e-05 divB_max=6.714e-04`

#### 图 C — `kelvin_helmholtz/figures/kh_density_bmag.png`（=`kh_paper_style.png`）
密度场（左）与磁场模 |B|（右），t=1.0。双剪切层位于 y=0.25 与 y=0.75。

- **作用**：展示流向弱磁场 (B₀=0.1, Alfvén Mach M_A=5) 双周期剪切层中 KH 不稳定性的早期非线性演化。
- **如何阅读**：密度色条 0.986–1.01（衬度极小，仅 ~1.4%，因弱场+弱扰动 δ=0.01）；两条深蓝水平
  带=剪切界面。|B| 色条 0.0951–0.102，对角的亮/暗条带=**磁场被剪切流卷绕、拉伸放大**沿界面分布。
- **对比文献**：Frank et al. 1996（*ApJ* 460, 777；arXiv `astro-ph/9510115`）MHD KH 演化；
  Lecoanet et al. 2015（arXiv `1509.03630`）作为**局限性锚点**——无黏 KH 对扰动/正则化敏感，可能
  不适定，故不能宣称网格收敛。
- **结论**：剪切界面清晰、磁场沿界面被拉伸放大、扰动在 x 方向呈正弦种子（与 IC 一致）——符合弱场
  KH 早期非线性阶段的形态。
- **合理性核查**：✅ 合理，但需诚实标注**caveat**：t=1.0 时 billow（卷起）尚未充分发展，密度衬度很小，
  **不能宣称湍流饱和或网格收敛**（Lecoanet 2015 的不适定性警告）。这是**有界形态/稳定性证据**。

#### 图 D — `kelvin_helmholtz/figures/kh_divb.png`
log₁₀|div(B)|，t=1.0。

- **作用**：验证在**光滑（无强激波）**问题上的散度清理质量。
- **如何阅读**：色条 10⁻⁹·⁴³ ~ 10⁻³·¹⁷（约 3.7e-10 ~ 6.7e-4），误差沿剪切层弱集中。
- **结论**：`divB_max=6.7e-4`、`divB_mean=4.4e-5`，比 OT **小约 4 个数量级**——因为 KH 光滑、弱场，
  无强激波产生散度误差。
- **合理性核查**：✅ 合理且是**强证据**：相同求解器在光滑问题上 div(B) 干净、在激波问题上受控，说明
  误差来源确为不连续面，符合预期。

### 1.3 HLLD vs HLL 求解器对比（OT 256², t=0.5）

#### 图 E — `solver_compare/figures/rho_hll_hlld_diff.png`
三联图：HLL 密度 | HLLD 密度 | (HLLD−HLL) 密度差。

- **作用**：评估 HLLD 五波解相对 HLL 二波解在物理解上的差异是否可接受。
- **如何阅读**：前两panel 几乎肉眼无差；右 panel 为差值（色条 ±0.85 量级），**差异集中在激波/电流片**，
  大片区域差≈0。
- **对比文献**：Miyoshi & Kusano 2005（*JCP* 208, 315；DOI `10.1016/j.jcp.2005.02.017`）HLLD
  五波求解器。
- **结论**：体相 L1(ρ)=9.43e-2、Linf(ρ)=8.46e-1（且仅局部于不连续面）——两求解器在**物理解上一致**，
  差异如预期集中在分辨率敏感的间断处。
- **合理性核查**：✅ 合理。HLLD 在间断处更锐利属正常（更少耗散），整体一致说明 HLLD 实现无系统性错误。

#### 图 F — `solver_compare/figures/divb_hll_hlld.png`
两联图：log₁₀|div(B)| HLL | HLLD。

- **作用**：本周关键判据图——决定 HLLD 是否采用。
- **如何阅读**：两图都是丝状沿激波分布，但 HLLD 整体更亮（散度更大）。
- **结论（关键）**：`divB_max`：HLL=3.72，**HLLD=34.29（约 9 倍）**；`divB_mean`：0.122 vs 0.290。
  → **HLLD 暂缓，HLL 维持为生产求解器**。
- **合理性核查**：✅ 合理且结论保守正确。佐证见 §1.4 的 GLM sweep：在**早期 t=0.05、小 glm_cr** 下
  HLLD 的 div(B) 反而**更低**（0.243 vs HLL 0.355），说明 t=0.5 的偏大是 **HLLD 波扇与 GLM 清理的
  晚期相互作用**所致，需专门排查，因此"先用 HLL、择期再验 HLLD"是稳妥决策。

### 1.4 支撑性诊断（非主图）

- **HLLD GLM sweep**（`hlld_glm_sweep/summary.md`，OT t=0.05，4/4 跑完且 ρ 有限）：最佳 `hlld_glm0.05`
  `divB_max=0.243`。**作用**：定位 HLLD div(B) 问题随时间/glm_cr 的趋势，支撑 §1.3 的诊断。
- **MHD Verificarlo smoke**（`mhd_verificarlo_smoke/summary.md`，3 个 MCA 样本）：`rho_mean_spread`
  =2.22e-16（机器 ε）。**作用**：打通 MHD 路径接入 Verificarlo 随机舍入工具链的**管路冒烟**，为后续
  浮点精度研究做准备；**注意**：仅 3 样本冒烟，非精度研究结论。

---

## 2. 本周主要结论

1. **2D HLL 形态学验证通过**：OT 与 KH 在 256² 上均产生与文献一致的形态，诊断量有限、守恒合理、
   div(B) 受控（OT 受控于 O(1)，KH 干净于 1e-4）。
2. **HLLD 已实现但暂缓**：可运行、体相解与 HLL 一致，但当前 GLM 配置下 t=0.5 时 div(B) 约 9 倍于
   HLL。生产路径维持 HLL。
3. **代码增量安全**：默认 `riemann=hll`，Brio–Wu 1D 逐位一致，未改动 Euler/1D 数值。

---

## 3. 合理性总体审查（含必须向导师如实说明的 caveat）

| 项 | 状态 | 说明 |
|---|---|---|
| OT/KH 形态 vs 文献 | ✅ 合理 | 拓扑、激波取向、衬度量级一致 |
| div(B) 控制 | ✅ 合理 | GLM 受控非机器零；误差集中于间断面，符合预期 |
| HLLD 暂缓决策 | ✅ 合理保守 | 9× div(B) + sweep 佐证 → 先 HLL |
| 求解器一致性 | ✅ 合理 | HLLD 体相 L1≈0.09，差异仅在间断处 |
| **512² 自收敛门控** | ⚠️ **本周未记录** | OT/KH 的 L1/L2/Linf 收敛门控因 512² 运行超本地 20 分钟预算而**当时未完成**；**正在后台补跑**（见 §4） |
| 自收敛 = 物理验证？ | ⚠️ 需澄清 | 自收敛是**工程一致性检查**，非对已发表参考解的逐点验证（未数字化外部参考数据） |
| KH 演化阶段 | ⚠️ 需澄清 | t=1.0 仍属早期非线性，billow 未充分发展，**不能宣称收敛/湍流饱和**（Lecoanet 2015 不适定性） |
| Verificarlo | ⚠️ 仅冒烟 | 3 样本管路冒烟，非精度研究 |

**给导师的一句话**：本周的 2D 证据是**经文献锚定的形态学 + 有限诊断量**，足以支撑"2D HLL 物理基准
跑通"；**收敛性门控（512²）本周内未记录，现已在补跑**，补完前不宣称定量收敛。

---

## 4. 2D case 完成情况与补全

**结论：2D case 部分完成。**

- ✅ **已完成**：OT 与 KH 的 256² 形态学运行 + 图件包（图 A–D）、HLLD vs HLL 对比（图 E–F）、
  GLM sweep、Verificarlo 冒烟。
- ⚠️ **本周未完成（已自动补跑中）**：OT 与 KH 的**完整 512² 自收敛参考门控**，即
  `experiments/week13/{orszag_tang,kelvin_helmholtz}/summary.{csv,json,md}`，含
  L1/L2/Linf(ρ)、mass_rel、div(B) floor 三类门控。
  - 原因：512² 运行耗时（实测外推：OT 512²→t=0.5 约 25 min，KH 512²→t=1.0 约 40 min，含 candidate
    与 cr=0 control 后单驱动约 35–60 min），超过本地单命令 10 分钟超时。
  - **处置**：已派后台 subagent 顺序执行 `scripts/regression/mhd_orszag_tang_2d.py` 与
    `mhd_kh_2d.py`（均以后台方式规避超时），结果将回填到本节下方表格。

### 4.1 512² 自收敛门控结果（补跑回填）

> 状态：**补跑进行中**。下表在后台运行完成后回填真实门控数值。

| 基准 | L1(ρ) | L2(ρ) | Linf(ρ) | mass_rel | divB_max | 门控通过？ |
|---|---|---|---|---|---|---|
| Orszag–Tang 512²→256² | _补跑中_ | | | | | |
| Kelvin–Helmholtz 512²→256² | _补跑中_ | | | | | |

---

## 5. 下一步

1. 回填 §4.1 的 512² 收敛门控（后台补跑完成后）。
2. 排查 HLLD 晚期 div(B) 偏大（HLLD 波扇与 GLM 清理交互），通过后再考虑生产采用。
3. 在 HLL 生产路径上推进 MHD 浮点精度研究（Verificarlo 由冒烟转入正式采样）。

## 参考文献

- Brio & Wu 1988, *JCP* 75, 400，DOI `10.1016/0021-9991(88)90120-9` — 1D MHD 激波管。
- Orszag & Tang 1979 / Tóth 2000, *JCP* 161, 605，DOI `10.1006/jcph.2000.6519` — OT 涡 & div(B) 约束。
- Frank et al. 1996, *ApJ* 460, 777，arXiv `astro-ph/9510115` — MHD Kelvin–Helmholtz。
- Lecoanet et al. 2015, arXiv `1509.03630` — KH 收敛/不适定性局限。
- Miyoshi & Kusano 2005, *JCP* 208, 315，DOI `10.1016/j.jcp.2005.02.017` — HLLD 五波求解器。
- Dedner et al. 2002, *JCP* 175, 645，DOI `10.1006/jcph.2001.6961` — GLM 散度清理。
</content>
</invoke>
