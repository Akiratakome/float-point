# Chapter 6 写作计划与审查

本计划细化 `manuscript_outline.md` 中 Chapter 6（Discussion:
Reproducibility Across Implementations）的写作任务。它以当前 Chapter 2--5
正文和 `docs/experiment_logs/report2_evidence_map.md` 为事实边界，只规划综合与
解释，不新增实验、数值结果或证据等级。最终英文仍须由学生重写、核对并统一语气。

## 0. 写前基线与 skill 路由

### 必读顺序

1. `report2/phd-thesis-template-2.4/Chapter2/chapter2.tex`：提取实现选择，尤其是
   HLL/HLLD、GLM、CPU/CUDA 路径、串行 MHD sweep 与 completion gate；
2. `report2/phd-thesis-template-2.4/Chapter3/chapter3.tex`：继承 matched-axis、
   reference hierarchy、metric 和 metadata 定义，不在 C6 重复方法；
3. `report2/phd-thesis-template-2.4/Chapter4/chapter4.tex`：确定哪些 C5 比较具有
   可解释的验证前提，以及这些前提不能支持什么；
4. `report2/phd-thesis-template-2.4/Chapter5/chapter5.tex`：提取 matched、null、
   non-zero、workload-dependent 和 negative observations；
5. `docs/experiment_logs/report2_evidence_map.md`：覆盖较早 planning 或 synthesis
   中已经过时的 status、scope 和 excluded claims；
6. `experiments/week17/report2_synthesis/summary.md`：只作 claim-boundary 导航。
   其中的 ordinal axis ranking 与 `axis_ranking.png` 不进入正文。

### 本轮 skill

| Pass | Skill | 对 C6 的作用 |
|---|---|---|
| 结构规划与后续起草 | `scientific-writing-duke` | 每段固定一个主要 character，用 action verb 连接 C2--C5，按 known-to-new 顺序把新判断放在句末；按研究问题综合，避免逐算例重播。 |
| 独立接受检查 | `avoiding-ai-flavor` | 删除通用学术套话、营销式确定性、连续三联句和无证据形容词；强制每段出现具体方法、结果类型或限制。 |

本轮不加载 `report1-context`，也不使用 conclusion skill 代写讨论。Chapter 6
可以为 Chapter 7 锁定结论边界，但不能提前写 future-work 清单。

## 1. 章节任务与中心论点

Chapter 4 回答“哪些实现组合在限定测试中通过了验证”；Chapter 5 回答“改变某个
受控轴后，保存状态或运行时间如何响应”。Chapter 6 应回答更高一层的问题：这些
结果对“复现一个公开 HRSC/ideal-MHD 算法”意味着什么。

建议用下列中心论点贯穿五节：

> 在本研究覆盖的配置中，确定性重复、跨设备保存状态一致和数值充分性是三个不同
> 问题。算法名称不能单独保证复现；只有把数值方法、有效构建语义、算术精度、执行
> 路径、配置、参考定义和运行元数据共同固定，matched comparison 才能被解释。

该中心论点不是新的结果。它是 C2 的实现事实、C3 的控制协议、C4 的验证边界和 C5
的系统变轴结果的合并解释。

## 2. C2--C5 到 C6 的接口

| 已有章节 | C6 可承接的内容 | C6 禁止重复或升级 |
|---|---|---|
| C2 Project Development | 相同算法家族仍包含 GLM、fallback、branch rule、solver、CPU/CUDA 和 completion semantics 等实现选择。 | 不重述 MHD 方程、HLL/HLLD 教程、CUDA 结构或开发时间线。 |
| C3 Methodology | matched-axis 比较、reference hierarchy、error/discrepancy/timing 区分，以及 config--metadata--summary 的证据链。 | 不重复 metric 公式、matrix 细目或运行命令。 |
| C4 Validation | 验证使后续敏感性比较可解释，但只在 case、solver、precision、device、grid 和 time 的已覆盖组合内成立。 | 不复述 refinement、divB 或 CPU/GPU 表中的完整数字；不把 validation 写成普遍正确性。 |
| C5 Results | covered device/thread/repeat 的 null differences，precision/build/CFL 的非零或条件响应，workload-dependent timing，以及 temporal negative result。 | 不逐算例重报数字；不把不同 metric 归一成统一 effect size；不生成 axis leaderboard。 |

### 三层“复现”含义

C6 可用三层概念组织讨论，但正文不必机械编号：

- **deterministic repeatability**：同一 binary/configuration 的重复运行是否保存同一状态；
- **matched implementation reproducibility**：声明改变 device 或实现路径后，受控保存状态是否仍一致；
- **scientific reproducibility**：另一实现是否能在明确参考、metric 和 scope 下支持相同的有界结论。

这三层不能互相替代。零 ULP 的 matched saved state 不证明 exact accuracy；一个通过
self-refinement gate 的解也不证明另一硬件或编译器下 bitwise equality。

## 3. 允许结论与禁止泛化

| 允许的综合结论 | C2--C5 基础 | 必须同时写出的边界 |
|---|---|---|
| 验证是解释 sensitivity 的前提，而不是普遍正确性证明。 | C3 reference hierarchy；C4 numerical-reference、property 和 self-reference gates。 | Brio--Wu 使用数值参考；二维证据不是 exact solution comparison，也不证明 asymptotic convergence。 |
| 测试轴的影响取决于 workload、metric 和 matched scope，当前证据不支持统一排名。 | C5 null/non-zero、workload-dependent、non-monotonic 和 negative observations。 | 不比较不同物理系统、不同 solver 或不匹配 MCA scope 的 effect magnitude。 |
| 相同算法标签不足以定义一个可复现实验。 | C2 solver/device/fallback choices；C3 build semantics 和 metadata。 | 该判断针对本项目暴露出的实现自由度，不声称列举了所有可能来源。 |
| 性能结论必须服从 validation 和 output-comparison gate。 | C4 matched correctness；C5 repeated CPU/GPU 与 KH timing。 | 更快不等于更准确或科学上足够；timing 只适用于当前 workstation、workload 和 subprocess protocol。 |
| null result 和 negative result 都是证据。 | covered zero saved-state differences；未观察到预设 temporal contrast。 | null 只属于已测试组合；negative temporal result 不等于不存在一般时间增长。 |

以下表述在 C6 中禁止：

- “precision is the most important axis”或任何跨 metric 的 ordinal ranking；
- “GPU is reproducible/independent of hardware”这类超出 HLL Brio--Wu/OT 的泛化；
- “fp32 is accurate enough”，除非另有 exact 或明确 numerical reference 和接受阈值；
- 把 HLL/HLLD method difference 称为 reproduction error；
- 把 thread-count invariance 写成 parallel-schedule 或 MPI reproducibility；
- 把三网格趋势称为 asymptotic convergence；
- 把 virtual p24 称为 IEEE fp32，或合并不同 grid/time 的 deterministic/MCA rows；
- 把 temporal slope 称为 formal maximal Lyapunov exponent 或物理不稳定增长率。

## 4. 字数与版面预算

Chapter 6 工作范围为 680--730 words，硬上限 750。建议正文目标 705 words，给学生
重写和 Overleaf 计数差异保留约 25 words。

| 小节 | 目标词数 | 段落 | 主要任务 |
|---|---:|---:|---|
| 6.1 Meaning of the validation evidence | 125 | 1 | 说明 validation 如何允许并限制 C5 interpretation。 |
| 6.2 Relative importance of the tested axes | 165 | 2 | 综合 null/non-zero/negative evidence，并解释为何不能统一排名。 |
| 6.3 Accuracy, discrepancy, and performance trade-offs | 125 | 1 | 分开 reference error、cross-variant discrepancy 与 runtime。 |
| 6.4 Reproducibility of a published algorithm | 165 | 1--2 | 给出最小可复现实验说明及 metadata 责任。 |
| 6.5 Limitations | 125 | 1 | 把主要限制逐一连接到被限制的结论。 |
| **合计** | **705** | **6--7** | 主文目标；正式计数以 Overleaf 为准。 |

### 图表决策

C6 不新增主文图或表。现有 `axis_ranking.png` 永久排除，C5 的 non-ranking scope
matrix 也不在 C6 重复。讨论通过交叉引用 Chapter 4 的 validation evidence 与 Chapter 5
的现有 figure/table 完成。若版面审查后来要求一个 synthesis item，只能使用不排序的
claim/scope table，并必须删除等量重复 prose；当前不推荐。

## 5. 分节段落蓝图

### 6.1 Meaning of the validation evidence

- **主要 character**：`The validation hierarchy`，不要用抽象的 “the analysis”。
- **Known opening**：Chapter 4 已通过数值参考、property checks、self-reference 和
  matched CPU/GPU gates 建立不同强度的验证。
- **Action**：说明这些 gate 排除明显实现失败，使 Chapter 5 的 matched discrepancy
  可被解释为受控 variation，而不是未诊断的 solver failure。
- **New/stress ending**：解释力仍受 reference 强度限制；二维 self-reference、
  morphology 和 raw divB diagnostics 不把 discrepancy 转化为 exact-state error。
- **不写**：C4 数字清单、所有 gate “passed”的总括、普遍 solver correctness。

### 6.2 Relative importance of the tested axes

第一段综合“哪些轴在 matched scope 中改变了保存状态或时间”：

- precision 和部分 effective math/branch comparisons 产生了非零 output response；
- covered device、repeat 和 requested-thread comparisons 给出 null saved-state response；
- hardware 与 solver timing 依 workload/configuration 改变，CFL response 非单调；
- fixed-window temporal hypothesis 保留为 negative result。

第二段解释为什么这些观察不能组成排名：metric 包含 ULP、mean norm、maximum norm、
MCA spread 和 wall time；case、solver、grid、time 及证据状态也不完全相同。段尾应落在
一个具体判断：本报告可以比较每个 matched pair 内的响应，但不能把不同问题压缩成
一个“最重要轴”。

- **允许的最小锚点**：可交叉引用 covered zero-ULP comparison、低于 matched
  refinement scale 的 mean-$L_1$ context 和 temporal fit-quality result；不要重报 C5
  的整组数字。
- **避免**：按 precision/compiler/hardware/implementation 顺序写四段 case replay。

### 6.3 Accuracy, discrepancy, and performance trade-offs

- **主要 characters**：`Reference error`, `cross-variant discrepancy`, `wall time`。
- **顺序**：先说明三者回答不同问题，再说明只有在 validation/reference scope 已明确
  后才能讨论性能收益是否值得。
- **核心判断**：Brio--Wu numerical-reference difference 可支持有界 error language；
  fp32--fp64、build、solver 或 device pair 通常只支持 discrepancy/sensitivity；wall time
  不度量 numerical adequacy。
- **段尾边界**：本研究可以报告“在保持 covered output gate 时更快”，不能报告统一的
  accuracy--performance Pareto frontier。

### 6.4 Reproducibility of a published algorithm

- **主要 character**：`A reproducible computational claim`。
- **首句判断**：HLL、HLLD 或 MUSCL--Hancock 等算法名称没有固定本项目实际暴露的全部
  数值与执行语义。
- **最小说明集**：
  - governing setup、case configuration、grid、end time、CFL 与 boundary conditions；
  - arithmetic precision、solver/fallback、GLM 和 branch semantics；
  - compiler/version、effective optimisation/math flags、binary/config hashes；
  - CPU/GPU path、thread request、workstation/device 与 timing protocol；
  - reference construction、metric definition、sample count、completion status 和 retained
    metadata。
- **组织方式**：不要在正文写成十项操作清单；分别组织为 experiment
  specification、implementation specification、execution record 和 evidence contract。
- **结尾判断**：configuration 与 metadata 不是附属 bookkeeping，而是使 algorithmic
  equivalence 可被检验的条件。
- **引用边界**：Plesser (2018)、Sandve et al. (2013) 和 Kritsuk et al. (2011)
  已在 `reference.md` 中限定允许论点并加入 BibTeX；它们分别支持术语边界、计算记录
  和共享基准比较设计，不支持本项目数值结果或通用实现排名。

### 6.5 Limitations

采用“限制 -> 被限制的结论”写法，不写实验时间线或道歉式叙述。优先保留以下四组：

1. numerical reference/self-refinement 的强度限制 -> 不给出 universal accuracy 或
   asymptotic-convergence 结论；
2. HLL GPU 只覆盖 Brio--Wu/OT、HLLD 仅 CPU、无 KH GPU -> 不给出一般 hardware 或
   solver-device 结论；
3. 单 workstation、单 MSVC toolchain、MHD sweep 无 OpenMP work sharing、无 MPI ->
   不给出 portability、parallel scheduling 或 scaling 结论；
4. OT/KH MCA scope、full KH MCA、fixed-window temporal fit 与样本量限制 -> 不合并
   stochastic/deterministic scopes，也不推断 formal chaotic growth。

段尾应把限制收回章节中心论点：当前证据支持配置绑定的 reproducibility 结论，而不是
对 ideal-MHD HRSC 实现的普遍排序。具体下一步实验留给 Chapter 7。

## 6. 证据与交叉引用定位

| C6 任务 | 首选正文交叉引用 | 规划/证据核对源 |
|---|---|---|
| Validation enables interpretation | `Chapter~\ref{chap:mhd-validation-results}`，以及 C4 validation-limits section | `experiments/week12/...`、resolution ladder、CPU/GPU validation rows |
| Matched-axis synthesis | Chapter 5 deterministic、performance、scale/time/stochastic 与 robustness sections | C5 正文；`chapter5_result_scope_matrix.md` 只作 non-ranking aid |
| Accuracy/discrepancy/timing distinction | Chapter 3 metrics/reference hierarchy，Chapter 4 Brio--Wu reference，Chapter 5 timing | 当前 LaTeX 定义和 report-grade summaries |
| Reproducibility specification | C2 execution/solver sections，C3 build/run matrix 与 harness/metadata section | `docs/HARNESS.md`、run-record contract、evidence map |
| Limitations | C3 deliberate exclusions，C4 validation limits，C5 scope sentences | evidence map 的 excluded claims 与 current claim boundaries |

起草前应给 Chapter 3、5 的主要 sections 补稳定 `\label{...}`（若尚未存在），再用
`\ref` 交叉引用。不要依赖章节页码或手写 section number。

## 7. 写作执行顺序

1. 从 C4.7 与 C5 bounded summary 提取 8--10 条“允许解释/禁止泛化”句子；
2. 将每条映射到 6.1--6.5，删除重复归属，使每个判断只在一节完整展开；
3. 先写 6.2 和 6.4，它们分别承担 evidence synthesis 与 reproducibility implication；
4. 再写 6.1，建立 validation 前提；
5. 写 6.3，清楚分开 error、discrepancy 和 runtime；
6. 最后写 6.5，只保留会改变结论强度的限制；
7. 用 `scientific-writing-duke` 检查 topic position、action verb、subject--verb proximity
   和 paragraph stress；
8. 用 `avoiding-ai-flavor` 独立检查 generic wording、过强信心和重复节奏；
9. 运行 LaTeX 编译、引用检查和本地静态词数估计，再以 Overleaf 正式词数为准；
10. 学生逐段重写并对照 C2--C5 和 evidence map 完成人工事实核查。

## 8. Draft 完成门槛

- [x] 本地静态估算为 730 words（含标题），处于 680--730 working range 且未超过 750-word hard upper；正式计数仍以 Overleaf 为准；
- [x] 6.1--6.5 每节各自完成 outline 指定任务；
- [x] 每段有一个稳定 technical character，关键综合判断位于段尾；
- [x] C4/C5 只被综合和交叉引用，没有逐算例复述；
- [x] null、non-zero、workload-dependent、non-monotonic 和 negative evidence 均可见；
- [x] 没有 cross-metric ordinal ranking，也未使用 `axis_ranking.png`；
- [x] `accuracy` 只绑定 exact 或明确定义的 numerical reference；
- [x] solver change 被写为 method variation，而不是 reproducibility drift；
- [x] zero ULP 未被升级为普遍 hardware independence；
- [x] thread-count result 未被升级为 OpenMP schedule、scaling 或 MPI 结论；
- [x] three-grid trend 未被称为 asymptotic convergence；
- [x] temporal result 保留 fixed-window、fit-quality 和 non-Lyapunov boundary；
- [x] deterministic fp32/fp64 与 virtual p24/p53 未被等同或跨 scope 合并；
- [x] performance 结论写明 workstation/workload/protocol scope，且不等同 numerical adequacy；
- [x] 6.4 覆盖 numerical definition、execution semantics 和 evidence contract；
- [x] 6.5 的每个 limitation 都明确限制一个结论，future work 留给 C7；
- [x] 正文不出现 week、P0/P1、gate nickname、packet 或 local run label；
- [x] 未引入未经 `reference.md` 验证的新引用；
- [ ] C6 的 cross-reference target 已静态确认存在，但本机 MiKTeX 首次安装配置未完成，完整 LaTeX/bibliography 编译和 Overleaf 正式计数仍待执行；
- [x] 已完成 `avoiding-ai-flavor` 独立检查；
- [ ] 学生完成最终个人语气重写与事实签核。

## 9. 总体 planning 判断

Chapter 2--5 已提供 C6 所需的实现、方法、验证和系统变轴材料；当前没有需要为 C6
补跑的实验。最重要的写作风险不是证据缺失，而是把不相容 metric 排成统一轴排名，
或把限定组合中的 zero difference 外推为普遍 reproducibility。按本计划执行后，C6
已进入 `author-rewrite`：正文以 validation boundary 为起点，以配置和 metadata
共同定义 reproducibility 为落点，并把 load-bearing conclusions 交给 Chapter 7，
没有增加新结果或新分析。剩余门槛是学生重写、Overleaf 正式计数与完整编译。
