# Week 15 汇报（给导师）
> **Historical snapshot:** This dated meeting document preserves what was known
> at the time. It is not the current Report 2 status. See
> [report2_evidence_map.md](../experiment_logs/report2_evidence_map.md) for
> current evidence, supersession, and claim boundaries.

> 生成于 2026-07-09。图在 `docs/week15/figures/` 下（学术论文风），数字都核对自各自的 `summary.json`。
> 本周把精度研究从**smoke 规模**升级到**report-grade**：从 Week-14 只做 Brio–Wu 1D / 8 变体 / MCA n=8，
> 扩到 **1D（Brio–Wu）+ 2D（Orszag–Tang）两个算例、HLL + HLLD 两个求解器、完整 24 变体 + MCA N=30**，纯 CPU。

---

## 一句话总结

这周把系统精度研究的**四条主轴里的三条**（精度 / 编译器优化+fastmath / 求解器不等号）在 **1D 和 2D、两个求解器**上收成了 report-grade 证据（6 张论文风图），
每个证据包都过了硬门禁（G0 锚点）；过程中**并行化了 Verificarlo 采样（16 容器并发，之前只用 1 核）并修好了一个 p24 采样偶发失败的鲁棒性问题**。
唯一还没覆盖的主轴是**硬件（CPU vs GPU）**——GPU MHD 的 spec + 计划已经写好，CUDA 正在装。

---

## 这周具体做了什么

1. **确定性精度矩阵升到全 24 变体**：每个算例跑满 `{float,double} × {O2,O3,Ofast} × {ieee,fastmath} × {leq,strict}`（Week-14 只有 8 个），逐点比和双精度基线的差别。
2. **MCA 随机舍入采样升到 N=30**：从 Week-14 的 n=8 smoke 升到统计稳定的 N=30，量化"实际还剩几位有效数字"。
3. **1D 和 2D、两个求解器都做**：Brio–Wu 1D 和 Orszag–Tang 2D，各自 HLL 和 HLLD，共 4 个 report-grade 证据包，全部 G0 过。
4. **工程改进（这周发现/做的）**：把 MCA 采样**并行化**（`--jobs 16`，之前串行只用 1 核）；诊断并修掉 **p24 偶发 stall**（低精度下 CFL 时间步偶尔被舍入逼到 ~0，重试次数从 3 提到 6）。
5. **GPU MHD 计划**：写好 HLL 优先的 spec + 10 任务实施计划，开始装 CUDA（补硬件轴）。

---

## 六张图：怎么看，说明什么

下面每张图先说**一句话结论**，再说**怎么看**。

### 图 A — 精度/编译器/求解器分支，哪个影响大？`figures/fig1_precision_axis.png`

- **一句话**：**精度（float vs double）压倒性主导**——1D 和 2D 都是一个大台阶，float 比 double 大约 8–9 个数量级。
- **怎么看**：两个子图 (a) Brio–Wu 1D、(b) Orszag–Tang 2D，纵轴是"和双精度基线的 $L_\infty(\rho)$ 误差"（对数刻度），横轴是 24 个变体（左 12 个 double 蓝、右 12 个 float 红）。
  double 簇贴在 ~1e-14～1e-17（机器精度极限，虚线是 1e-15 参考），float 簇一下跳到 ~1e-6（1D）/ ~1e-5（2D）。
- **注意边界**：这里比的是"和我们自己的双精度基线"的差，是**工程一致性**，不是对精确解的逐点验证。

### 图 B — 还剩几位有效数字？（本周头图）`figures/fig2_mca_noise_floor.png`

- **一句话**：**fp64 交付约 15 位有效数字，fp32 只有约 6–7 位**——两者噪声底差约 9 个数量级，四个证据包一致。
- **怎么看**：横轴四组（Brio–Wu HLL/HLLD、Orszag–Tang HLL/HLLD），每组两根柱：p53（双精度替身，蓝）和 p24（float 替身，红），纵轴是 N=30 次 MCA 采样的密度散布（对数）。
  p53 全部压在 ~1e-15（机器精度），p24 全部在 ~1e-6，稳定分离。
- **说明什么**：MCA 独立于任何参考解，直接测"这个模拟本身能交付几位可信数字"。这是 Report 2 最有辨识度的证据，现在在 N=30 下统计稳定，跨两个求解器、两个维度都一致。
- **互相印证**：p24 的 ~1e-6 和图 A 里确定性 float 的 ~1e-6 高度吻合——两种独立方法给出同一结论。

### 图 C — 编译器优化 / fastmath 影响多大？`figures/fig3_compiler_axis.png`

- **一句话**：**是真实但次要的轴**（比精度小两个数量级）；而且 fastmath 呈**非单调**——有时误差反而比严格 IEEE 更小。
- **怎么看**：两个子图 (a) Brio–Wu HLLD、(b) Orszag–Tang HLLD，只画 float 变体，蓝=严格 ieee、红=fastmath。
  Brio–Wu 面板能看到 ~1.5–1.9e-6 的抖动，红柱有的比蓝柱**低**（非单调）；OT 面板近乎平——2D 时编译器轴相对 fp32 误差底噪可忽略。
- **说明什么**：标题里的"N 个 fastmath ordering flags"（Brio–Wu：HLL 4/HLLD 6；OT：HLL 0/HLLD 4）是我们**自动标记**的非单调点。这是浮点重结合的正常现象，我们把它**标出来而不是悄悄当噪声**——是可写进报告的发现。HLLD 的 5 波扇比 HLL 更敏感。
- **注意边界**：这是软标记（非阻塞门），报告里作为"次要轴 + 非单调观察"呈现，不下强因果结论。

### 图 D — fp32 换来多少加速？`figures/fig4_walltime.png`

- **一句话**：**CPU 上 fp32 只比 fp64 快 1.06–1.34×**——对照约 9 个数量级的精度损失，CPU 上 fp32 的性价比不划算。
- **怎么看**：横轴四个证据包，纵轴是"加速比 = fp64 墙钟 / fp32 墙钟"，虚线 1.0 = 无加速；柱内标了绝对时间（1D ~0.15s，2D ~27s）。
- **说明什么**：这是"该不该用 float 换速度"的量化答案：CPU 上换不到多少速度却损失大量精度。真正的 fp32 吞吐优势在 GPU 上（架构性的），所以下一步转向 GPU。

### 图 E — 2D 算例长什么样？`figures/fig5_ot_hll_reference_fields.png`

- **一句话**：Orszag–Tang 2D 的密度/压强场，重现了文献里的经典涡结构。
- **怎么看**：双精度参考解在 256²、t=0.5 的密度和压强场（伪彩），能看到 OT 标志性的湍流状电流片和涡旋。
- **注意边界**：OT 没有闭式解，这里是**对文献形态的重现**（morphology），不宣称逐点吻合。

### 图 F — 2D 混沌把 fp32 漂移放大了多少？`figures/fig6_ot_hll_fp32_drift.png`

- **一句话**：**2D 混沌流把 fp32 漂移放大到 ~3e-3**（OT-HLLD），远大于 1D 的 ~1e-6——是"时间发散"的入口。
- **怎么看**：float 相对 fp64 参考的 |密度漂移| 和 |By 漂移| 的对数热图，漂移集中在欠分辨的电流片区域。
- **说明什么**：混沌 2D 流会**指数放大**精度差异，在电流片处最明显。这直接引出 Week 16 的**时间发散 / Lyapunov 指数**分析（拟合 `log(误差)=λt+c`）。

---

## 能对导师说的（和暂时不说的）

**能说**：

- 1D（Brio–Wu）和 2D（Orszag–Tang）、HLL 和 HLLD 四个证据包都过了 G0 锚点门（1D 759 步；OT HLL 806 步/divB 3.72、HLLD 812 步/divB 24.45），有限、可复现。
- 精度是主导轴（≈9 个数量级）；MCA 测出 fp64≈15 位、fp32≈6–7 位有效数字，N=30 稳定、跨维度跨求解器一致。
- 编译器/fastmath 是次要轴，且带非单调 ordering flags（已标记）；CPU 上 fp32 只换来 1.06–1.34× 加速。
- 2D 混沌算例把 fp32 漂移放大到 ~3e-3，指向 Week 16 的时间发散分析。
- 工程上：把 MCA 采样并行化（16 容器并发）、修好了 p24 偶发 stall（重试 3→6）。

**暂时不说**（避免过度宣称）：

- 不宣称和精确解逐点吻合（Brio–Wu / OT 都只对文献形态）；不宣称 HLLD 更优或已达生产水平（HLL 仍是生产默认）。
- **还没有 GPU/硬件轴数据**（在做）；还没做 Lyapunov/时间发散拟合（Week 16）；不下 KH 或 512² 的结论。

---

## 下一步

1. **GPU MHD（补硬件轴）**：HLL 先上 GPU，加 CPU-vs-GPU 同精度 ULP 回归门，再把 Brio–Wu 1D + OT 2D 指向 GPU 补齐第四条主轴；HLLD-on-GPU 作后续。spec + 计划已写好，CUDA 正在装。
2. **Kelvin–Helmholtz 2D**：第二个 2D MHD 算例（目前只有形态验证），升到同样的 24 变体 + N=30。
3. **时间发散 / Lyapunov 指数**（Week 16）：在 OT / KH 混沌流上拟合 `log(误差)=λt+c`，图 F 的 ~3e-3 漂移就是入口。

---

## 参考文献

- Brio & Wu (1988), *JCP* 75, 400, DOI `10.1016/0021-9991(88)90120-9` — 一维理想 MHD 激波管基准。
- Orszag & Tang (1979), *JFM* 90, 129 — 二维 MHD 湍流涡基准。
- Dedner et al. (2002), *JCP* 175, 645, DOI `10.1006/jcph.2001.6961` — GLM 散度清理。
- Miyoshi & Kusano (2005), *JCP* 208, 315 — HLLD 五波求解器（GPU 作后续）。
- Denis, Castro & Petit (2016), Verificarlo — 蒙特卡洛算术（MCA）随机舍入分析工具。
