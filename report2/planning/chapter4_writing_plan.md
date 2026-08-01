# Chapter 4 写作计划与审查

本计划细化 `manuscript_outline.md` 中 Chapter 4（MHD Validation Results）的
写作任务。它是写作与审查清单，不是可直接提交的论文正文；最终英文须由学生
重写、核对并统一语气。

## 0. 写前语言基线与 skill 准备

### Report 1 语言学习范围

C4 不从通用“学术英语”想象语气，而以已完成的 Report 1 正文作为本项目内部
语言基线。写作前必须按以下顺序阅读：

1. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`：主要语料。学习其
   validation/results 段落如何先点名算例和图表，再给数字、解释含义并立即限定范围；
2. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`：只学习 limitation、
   negative result 和跨章节过渡的语气；
3. `report1/phd-thesis-template-2.4/Chapter4/chapter4.tex`：只核对术语、实验轴和
   reference strategy 的表达连续性，不照搬其 implementation 内容。

这里的“学习”是提取句法、语气和论证节奏，不是复制句子。Report 1 的 Euler 数值、
case 范围、章节编号和结论均不得作为 Report 2 的事实来源；C4 的事实 authority 仍是
本计划第 5 节、`report2/planning/manuscript_outline.md` 和
`docs/experiment_logs/report2_evidence_map.md`。

从 Report 1 锁定以下语言特征：

- 用被测对象作主语，例如 “The HLL runs ...” 或 “Figure 4.2 shows ...”，少用
  “an investigation was performed” 一类名词化开头；
- 自有运行与观测用过去时，图、表、公式及本章论证用现在时；
- 沿用 Report 1 的英式拼写（例如 `behaviour`、`discretisation`、`artefact`），
  不在同一章混用美式拼写；首次介绍基准或论文结论时优先使用作者式引用，支撑句末
  解释时使用括号式引用；
- 每段只承担一个主要判断，按 **对象/目的 → named figure or table → 2--4 个关键数字
  → evidence meaning → explicit boundary** 推进；
- 数值通常保留 3--4 个有效数字，精确零明确写为 zero/0 ULP，不用 vague adjective
  代替量化；
- 以 “within the tested ...”, “does not establish ...”, “not an exact-solution
  claim” 等范围句控制强度，但每个 clause 最多一个 hedge；
- 对仍有证据支持的负结果使用短而直接的句子，不得用流畅的总结句冲淡其边界；
- 图表必须被点名、指出读者应看什么，并说明该观察支持什么和不支持什么。
- 只继承 Report 1 的声音，不继承其个别长段的数字密度；超过 4 个关键数时移入表格或
  图注，正文保留支撑本段判断所需的最小集合。

### 必用 skill 路由

不新建重复 skill；复用 `report1/skills/` 下已经在 Report 1 定稿中使用过的本地
写作 skill。每一轮最多加载两个，顺序固定如下：

| Pass | 必用 skill | 任务 | 本轮禁止事项 |
|---|---|---|---|
| 写前/初稿 | `scientific-writing-duke` + `academic-english-style` | 建立 topic/stress position、时态、主动主语、hedging 与 evidence-bound claim | 不做逐词润色，不追求“漂亮”同义改写 |
| 结构编辑 | `editing-academic-prose` | 先检查段落职责和 given-to-new flow，再处理句子和词 | 不在结构未定时修饰单句 |
| 接受检查 | `avoiding-ai-flavor` | 检查 generic academese、三联节奏、营销式形容词、重复破折号和无证据总结 | 不把检查结果自动视为学生最终语言 |

`report1-context` 不得用于 C4：它包含 Report 1 的字数、范围和交付约束。C4 上下文由
Report 2 outline、evidence map、reference map 和本计划提供。`writing-introduction`、
`writing-literature-review`、`writing-conclusion` 也不适用于本章结果写作。

### 写前完成条件

开始写 4.2 正文前，执行者必须准备一页内部 drafting sheet（可留在工作笔记中，不放入
论文），逐节记录：named evidence、允许报告的 2--4 个数、baseline、scope、negative
result 和禁止外推。随后用 Report 1 Chapter 5 的一个段落做结构对照，确认只借用结构，
没有复用其句子或 Euler 事实。未完成该 preflight 时，C4 仍保持 `structure-only`。

## 1. 章节任务与结论边界

Chapter 4 只回答一个问题：**在进入精度、编译器、硬件性能和实现敏感性分析
之前，现有 MHD 实现在哪些明确范围内通过了验证？**

论证顺序固定为：

1. 局部性质：二维退化为一维时的横向不变性，以及 GLM 对人为散度扰动的控制；
2. 数值参考：Brio--Wu 的一维网格加密结果；
3. 实现一致性：相同精度下 CPU 与 GPU HLL 路径的输出一致性；
4. 复杂二维算例：Orszag--Tang（OT）与 Kelvin--Helmholtz（KH）的完成性、
   物理状态、散度诊断和三网格自加密趋势；
5. 限制：数值参考不等于精确解，三网格趋势不等于渐近收敛，形态相似不等于
   定量精度，未覆盖组合不得外推。

Chapter 4 不负责比较 fp32 与 fp64 的敏感性、GPU 加速比、HLL 与 HLLD 的性能或
精度排名、编译器/分支规则、MCA 或时间增长率。这些属于 Chapter 5。允许在 C4
末尾用一句话指向 C5，但不得提前解释 C5 的结果。

## 2. 字数与版面预算

全章目标保持在大纲规定的 1,150--1,220 词内，并把表格文字和图注计入总数。

| 部分 | 主文目标 | 写作功能 |
|---|---:|---|
| 4.1 Validation hierarchy overview | 约 85 词 | 给出证据顺序，不复述实验矩阵 |
| 4.2 One-dimensional Brio--Wu validation | 约 165 词 | 建立一维数值参考验证 |
| 4.3 Two-dimensional invariance and divergence control | 约 145 词 | 建立局部二维性质验证 |
| 4.4 Matched CPU/GPU implementation validation | 约 135 词 | 建立受限 GPU 路径正确性 |
| 4.5 Orszag--Tang validation | 约 190 词 | 报告复杂二维 OT 验证及完整三网格结果 |
| 4.6 Kelvin--Helmholtz validation | 约 210 词 | 报告 KH 自加密、诊断范围及独立文献初值复现 |
| 4.7 Validation limits | 约 120 词 | 集中声明不可推出的结论 |
| 图注、表头和表注 | 约 130--160 词 | 完整定义比较、指标、基线和范围 |

主文约 1,050 词；加图表文字后总计约 1,180--1,210 词。若超限，先删除重复的
配置说明和结果复述，不删除成功完成证明、基线或结论边界。

## 3. 主文图表锁

### Figure 4.1：一维加密与 GLM 诊断

- 文件：`experiments/week18/report2_publication_figures/fig_validation_refinement_glm.pdf`
- 4.2 解释 panel (a)，4.3 解释 panel (b)。图只出现一次。
- 图注必须说明 Brio--Wu 使用对齐并块平均的 (N=8000) fp64 数值参考；GLM panel
  报告周期二维散度扰动的 `divB_max`，并把 `c_r=0` 标为无阻尼对照。
- 允许结论：加密时数值参考差异单调下降；非零 GLM 阻尼在所测时间末端降低了
  最大散度诊断。
- 禁止结论：精确解精度、fp32 充分性、GLM 参数全局最优性或复杂二维流已验证。

### Table 4.1：相同精度 CPU/GPU 正确性

建议列：case、precision、grid、CPU/GPU steps、maximum ULP、absolute
$L_\infty$、validation scope。四行覆盖 Brio--Wu/OT × fp64/fp32。

- 数据源：`experiments/week16/cpu_gpu_hardware_axis/summary.json`。
- 四行均报告 `ulp_max=0`、绝对 $L_\infty=0$，且 CPU/GPU 步数一致。
- 不把 speed-up 放入该表；重复计时与工作负载差异由 C5 的硬件图负责。
- 表注锁定 HLL、Brio--Wu/OT 和本机 CUDA 路径，不扩展到 HLLD、KH 或 MCA。

### Figure 4.2：OT/KH 三网格诊断

- 文件：`experiments/week18/report2_publication_figures/fig_resolution_precision.pdf`
- C4 只显示八个完整组的自加密诊断。OT/HLLD/fp64/$512^2$ 运行已经完成；跨精度
  panel 则等待用同一修复路径重新生成对应的 fp32/$512^2$ 保存网格和配对度量后进入
  C5。这不影响 fp64/$512^2$ 完成性或八组三网格成功结论，也不以缺失点代替结果。
- 图注必须声明 HLL 使用 CFL=0.4、HLLD 使用 CFL=0.2；图中的 observed $p$
  仅为同一 case/solver/precision/CFL 内的三网格工程诊断。
- OT/HLLD/fp64/$512^2$ 使用修复后二进制的完成记录和保存网格，不得再引用旧失败记录。
- 允许结论：24 个计划运行全部完成，八组均具备完整三网格诊断，且八组的平均密度
  $L_1$ 差异均给出正的 observed $p$。
- 禁止结论：完整矩阵通过、渐近收敛阶、跨 solver 优劣，或把跨精度分离称为
  离散化误差。

### 形态图决策

OT/KH 形态图现为 morphology-only/P2，而且不在已审计的六张 publication
figures 中。默认不占主文版面：C4 只用一至两句说明已观察到预期的基准结构，
并明确这是定性支持。仅当最终版面允许且图源、引用、图注和视觉质量全部复核后，
才把合并形态图放入附录；不得让它承担定量验证结论。

## 4. 分节段落蓝图

每节使用统一结果段结构：**目的 → 点名图/表 → 定量观察 → 验证含义 → 边界**。

### 4.1 Validation hierarchy overview

写一个段落，完成三件事：

1. 回指 Chapter 3 已定义的参考层级和指标，不再说明为何选择这些算例；
2. 声明验证从局部性质、数值参考和 CPU/GPU 一致性推进到复杂二维算例；
3. 说明同一证据的地位不会自动继承到其他 solver、precision、device、grid 或
   end time。

不要在本节出现具体结果值或“all validations passed”一类总括句。

### 4.2 One-dimensional Brio--Wu validation

建议一个主段落：

- 目的：验证一维理想 MHD 波结构求解在加密时趋近一个明确的高分辨率数值参考；
- 图：引入 Figure 4.1(a)；
- 数值：$N=200,400,800$ 相对 $N=8000$ 参考的密度 $L_1$ 从
  $1.481\times10^{-2}$ 降至 $5.642\times10^{-3}$，$L_2$ 从
  $3.642\times10^{-2}$ 降至 $1.923\times10^{-2}$；两者均单调下降；
- 含义：实现随网格加密更接近对齐的数值参考，并在各运行中保持有限状态和受控
  `divB`；
- 边界：参考是块平均后的 (N=8000) fp64 数值解，不是 Brio--Wu 精确解，也不
  支持精度 headline。

如需报告图中 observed rates（$L_1=0.70$、$L_2=0.46$），称为“over the
three tested grids 的 observed rates”，不要写成形式收敛阶。

### 4.3 Two-dimensional invariance and divergence control

建议一个段落，先不变性、后 GLM：

- 在 $800\times4$ 的二维 Brio--Wu 嵌入中，横向最大偏差为 0；相对一维运行的
  密度平均/最大绝对差分别为 $3.550\times10^{-4}$ 和
  $7.034\times10^{-3}$，均通过预设门槛；
- Figure 4.1(b) 显示在 (t=0.5) 时，无阻尼对照的 `divB_max` 为 3.030，
  `c_r=0.18` 和 0.36 分别为 0.2678 和 0.8429；
- 解释为二维方向处理保持了测试所要求的横向不变性，而且两个非零阻尼设置在
  末时刻均低于无阻尼对照；
- 只说 `c_r=0.18` 在所测设置中给出较小末时刻值，不称其为全局最优参数，也不
  据此宣称 OT/KH 的精度充分。

### 4.4 Matched CPU/GPU implementation validation

建议一个主段落围绕 Table 4.1：

- 目的：先验证设备实现一致性，再在 C5 讨论计时；
- 数值：Brio--Wu $800\times1$ 和 OT $256^2$ 的 HLL 路径在 fp32/fp64 中均
  有相同步数、0 maximum ULP 和 0 absolute $L_\infty$；重复硬件包也保持该
  0-ULP 结果；
- 含义：对四个明确组合，GPU 路径重现了相同精度 CPU 路径的存储输出；
- 边界：这是受限的实现一致性证据，不是普遍的硬件无关性。不得扩展到
  HLLD-on-GPU、KH-on-GPU、GPU MCA 或其他架构。

本节不报告任何加速比；可用一句末句指向 C5 的重复计时分析。

### 4.5 Orszag--Tang validation

建议两个短段落：

1. **完成性与诊断。** 说明 OT 是形态支持加上定量工程诊断，而不是精确解比较。
   HLL 运行保持有限、正的物理状态和质量守恒诊断；`divB_mean` 随
   $128^2\rightarrow512^2$ 从 0.1364 降至 0.1036，而局部 `divB_max`
   可随更薄的电流片增大。因此不得只用最大值判断全局散度控制。HLLD follow-up
   只用于说明较大局部峰值已排除 stale binary，并与当前片层局部化一致。
2. **网格诊断与完成结果。** 引入 Figure 4.2：HLL fp64/fp32 的平均密度
   $L_1$ observed $p\approx0.639$，HLLD fp32/fp64 均约为 0.846；HLLD fp64
   $512^2$ 在 3277 步完成到 $t=0.5$，保存网格保持有限和正压。明确结论是
   “全部组合完成并呈正的三网格自加密趋势，但三个网格不证明渐近收敛”。

不要把 HLL 与 HLLD 的数值作优劣排名，因为 solver 和 CFL 不同；不要引用旧的
二维 `dx`-only L1/L2 汇总值。上述三网格数值只从 Week-18 corrected summary
读取。

### 4.6 Kelvin--Helmholtz validation

建议两个短段落：

1. **物理状态与散度诊断。** 说明 KH (128^2,256^2,512^2) 的 HLL 与 HLLD、
   fp32 与 fp64 组合全部完成并保持有限、正的状态。HLL 的 `divB_mean` 从
   $6.877\times10^{-5}$ 降至 $2.305\times10^{-5}$；HLLD fp64 从
   $2.747\times10^{-4}$ 降至 $3.479\times10^{-5}$。最大值与平均值分开
   报告，不把一个标量当作无散度证明。
2. **网格诊断。** Figure 4.2 中 HLL 的平均密度 $L_1$ observed
   $p\approx0.919$，HLLD 为 1.436--1.442；把它们表述为各自固定 solver/
   precision/CFL 内的正向自加密趋势。不同 CFL 下不得据此宣称 HLLD 比 HLL
   “更准确”或“收敛更快”。正文同时报告相邻网格差异，避免仅用 observed $p$
   隐藏误差尺度。

独立 Lecoanet 增长率检查在通过预先声明的定量吻合门槛前不进入论文。不得把仅有
正增长或高 $R^2$ 写成文献增长率复现，也不在正文中写失败结论。

形态描述最多一至两句。准确措辞是“项目定义的平滑周期 MHD 双剪切算例”：
Tricco/Lecoanet 支持平滑双剪切函数族和收敛限制，Frank et al. 支持弱平行磁场
MHD 情景，而代码/cfg 是本项目参数的唯一精确权威。不得写成逐项复现上述任一论文，
也不得将验证扩展为 full-scale KH MCA、GPU coverage 或一般化的非线性不稳定性结论。

### 4.7 Validation limits

用一个紧凑段落依次收束：

- Brio--Wu 使用高分辨率数值参考；OT/KH 主要使用自参考、形态和诊断量，没有
  MHD 精确解误差；
- 三网格在含间断/复杂结构的解上只给工程趋势，不证明渐近区间；
- 形态一致是定性证据；`divB_max` 对局部片层和分辨率敏感，不能单独证明全局
  散度误差消失；
- GPU 证据仅覆盖 HLL Brio--Wu/OT；HLLD/KH GPU 路径仍未验证；
- 历史二维 `dx`-only L1/L2 不进入新比较，C4/C5 使用审计后的 Week-18
  mean/area metrics 或不受面积权重影响的 $L_\infty$。

最后一句说明这些边界定义了 C5 系统敏感性结果的可解释范围，不列 future-work
清单。

## 5. 证据定位表

| 用途 | 当前权威文件 | C4 使用方式 |
|---|---|---|
| 一维 Brio--Wu 数值参考 | `experiments/week12/brio_wu_1d/summary.json` | 4.2 数值与 Figure 4.1(a) |
| 二维横向不变性 | `experiments/week12/mhd_2d/brio_wu_2d/summary.json` | 4.3 小型定量结果 |
| GLM 扰动衰减 | `experiments/week12/mhd_2d/divb_clean/summary.json` | 4.3 与 Figure 4.1(b) |
| HLLD 散度 follow-up | `experiments/week13/hlld_divb_followup/summary.md` | 4.5 解释局部峰值；不重述开发史 |
| CPU/GPU 正确性 | `experiments/week16/cpu_gpu_hardware_axis/summary.json` | 4.4 Table 4.1 |
| 重复硬件正确性 | `experiments/week18/supplemental/hardware_repeats/summary.json` | 4.4 复核 0-ULP；计时归 C5 |
| OT/KH 完整三网格 | `experiments/week18/resolution_ladder/summary.json` | 4.5、4.6、Figure 4.2，二维 norm 的首选权威 |
| Lecoanet KH 初值/早期增长检查 | `experiments/week19/lecoanet_kh_linear_reproduction/summary.json` | 当前不进入论文；仅在定量吻合门槛通过后重新评估 |
| 发布图审计 | `experiments/week18/report2_publication_figures/figure_manifest.json` | 图源、hash、claim boundary 与视觉质量锁 |
| 证据状态 | `docs/experiment_logs/report2_evidence_map.md` | 所有 status 与外推边界的最终权威 |

旧的 `experiments/week13/orszag_tang/summary.md`、
`experiments/week16/kelvin_helmholtz_precision/validation/summary.md` 和
`experiments/week16/ot_kh_512_consolidation/summary.md` 可用于完成性、质量、
`divB`、$L_\infty$ 与历史 provenance，但其历史二维 L1/L2 不得作为新比较的
数值来源。

## 6. 写作执行顺序

1. 完成第 0 节 language/skill preflight：读 Report 1 Chapters 5、6 和 Chapter 4 的
   指定用途，完整读取本轮要求的 skill，并制作逐节 drafting sheet。
2. 先锁定 Chapter 3 中 norm、reference、completion、physical-state 与 `divB`
   的术语和符号，避免 C4 重复方法定义。
3. 将两个已审计 PDF 复制/链接到 LaTeX figure 路径，记录 manifest 中的源 hash；
   不重新绘制或手工改数字。
4. 从机器可读 JSON 生成 Table 4.1，保留 source path 和生成命令到 appendix map；
   不手抄 speed-up 列。
5. 使用 `scientific-writing-duke` + `academic-english-style`，按
   4.2 → 4.3 → 4.4 → 4.5 → 4.6 的证据顺序写结果段，再写 4.1 和 4.7。
6. 完成一次“数值三元组”检查：每个数字都同时具备 metric、baseline 和 scope。
7. 完成一次章节责任检查：删除 C5 的性能/精度敏感性解释和 C2/C3 的实现或方法
   细节。
8. 单独使用 `editing-academic-prose` 做结构到句子的编辑，再单独使用
   `avoiding-ai-flavor` 做接受检查；不得把两个 pass 合并成泛化改写。
9. 将 C4 与 Report 1 Chapter 5/6 做语气对照：检查证据密度、时态、主语选择、
   hedge 强度和段尾边界，不要求逐句相似。
10. 学生用自己的英文连接各段，再做术语、引用、图注、交叉引用和总字数检查。

## 7. Review 结论与待办

### 已关闭的 review 阻塞项

1. **基准文献已锁定。** `report2/references/reference.md` 记录了 Brio--Wu、OT、
   KH 和 GLM 的逐项实现核对、citation keys、允许句子和禁止外推；已核验条目写入
   `References/references.bib`。其中 KH 被正确标为 project-defined adaptation，
   不再假称存在一个与全部参数完全相同的论文算例。未达到定量吻合门槛的独立
   Lecoanet 增长率检查不进入论文。
2. **Chapter 3 指标措辞已锁定。** `manuscript_outline.md` 3.5 和 Chapter 3
   结构注释已明确 mean norm 与 physical-domain norm 的公式。Figure 4.2 使用
   block-averaged adjacent grids 的 mean absolute density $L_1$ difference，
   不是 relative norm，也不是旧 `dx`-only physical-domain L1。

### 已解决的计划风险

- 原计划只规定了结果段结构，未规定 Report 1 语言语料和 skill 使用顺序；第 0 节现已
  锁定 Chapters 5/6 为主要语言基线、Chapter 4 为术语辅助，并排除 `report1-context`
  的旧范围污染。
- C4/C5 重叠已通过“C4 验证、C5 敏感性/性能”分工解决；C4 不报告 speed-up 或
  fp32--fp64 adequacy。
- 旧二维 L1/L2 污染通过将 Week-18 resolution summary 设为当前首选来源解决。
- OT/HLLD/fp64/$512^2$ 已由守恒正性回退修复并完成；旧失败记录不进入论文结论。
- 形态图未进入已审计发布图集，因此被降为条件性附录材料，不阻塞 C4 主文。
- 图表数量收缩为两图一表，能在 1,220 词上限内保留定量解释和限制。

### Draft 完成门槛

- [x] 已完整阅读 Report 1 Chapters 5/6 和 Chapter 4 的指定用途，并完成逐节
      drafting sheet；未复制其句子、Euler 数值或 Report 1 结论。
- [x] 初稿、结构编辑和 AI-flavor 检查按第 0 节 skill 路由分轮执行，每轮不超过两个
      skill，且未加载 `report1-context` 作为 Report 2 约束。
- [x] 英文语气与 Report 1 一致：对象作主语、past/present 时态分工清楚、每个 clause
      至多一个 hedge，段尾给出 evidence boundary。
- [x] 每节均包含 purpose、named item、quantitative observation、implication、boundary。
- [x] 每个数值均可追溯到表中列出的当前 authority。
- [x] 所有二维 L1/L2 均来自 Week-18 corrected/mean summary，或被明确排除。
- [x] Figure 4.2 显示八个完整三网格组，正文明确 24/24 完成、8/8 完整组。
- [x] CPU/GPU 正确性只覆盖 HLL Brio--Wu/OT × fp32/fp64，且 C4 无性能结论。
- [x] “accuracy”只用于明确数值参考；其他地方使用 discrepancy、difference、
      sensitivity 或 diagnostic。
- [x] 未出现 internal week、P0/P1、gate nickname 或本地运行目录名。
- [x] 未把 morphology、`divB_max`、三网格 observed $p$ 单独提升为充分验证。
- [x] Brio--Wu、OT、KH、GLM 引用已按实现设置核验。
- [x] 未达到定量吻合门槛的 Lecoanet 增长率检查未写入论文；C4 只保留成功完成且
      可定量解释的项目 MHD KH 结果。
- [x] 图表均在正文中被点名和解释，图注写明 metric、baseline、scope 与 exclusion。
- [x] 补充并压缩后的 PDF 渲染页本地替代统计为 1,204 个英文字词，落在 1,150--1,220
      的计划区间内；该统计计入标题、图注和表格文本，但不替代正式 Overleaf 结果。
- [ ] `texcount` 因本机缺 Perl 不可用，须以 Overleaf 控制计数确认不超过 1,220 词。
- [ ] 最终英文是学生自己的连贯表达，并完成一次人工事实核对。

### 执行记录（2026-07-28）

- C4 七节正文、两张审计 PDF、JSON 生成的 Table 4.1 和附录证据映射已写入 LaTeX。
- 定向文档/生成器/发布图测试通过；BibTeX 与两遍 LaTeX 构建通过，无未解析引用或
  交叉引用。C4 PDF 页已视觉检查，无裁切、重叠或异常图表分页。
- 当前状态为 `author-rewrite`：技术草稿和机器事实核对已完成，但学生改写、Overleaf
  正式词数和最终人工事实核对尚未完成。
- 2026-07-30 review 修订删除了未达到定量吻合门槛的 Lecoanet 增长率段；Figure 4.2
  只保留八个完整三网格成功组，并在 OT/KH 正文补入相邻网格误差尺度。发布图生成、
  定向测试和完整 LaTeX/BibTeX 构建再次通过。
- 2026-07-30 补充轮加入 OT/KH 成功包中的质量守恒和局部散度最大值，拆分 KH 三类
  文献的具体支持职责，并明确 OT/HLLD/fp64/$512^2$ 已完成而跨精度配对度量属于 C5
  的后续成功门槛。补充并压缩后 PDF 渲染页词数代理为 1,204；15 项定向测试和完整构建通过。

## 8. 总体 review 判断

该计划与 `manuscript_outline.md` 的七节结构、Chapter 4 责任锁和当前 evidence map
一致。基准引用、二维 norm 定义、Report 1 语言基线和 skill preflight 四项 review
阻塞均已关闭。计划本身可标记为 `reviewed`；只有第 0 节写前条件实际完成后，C4 论文
文件才可从 `structure-only` 进入 `drafting`。论文正文仍须在学生重写、数值核对、
引用编译和字数检查完成后，才能进入 manuscript-level `reviewed`。
