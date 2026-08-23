# Chapter 1 写作计划与 C2--C6 接口审查

本计划细化 `manuscript_outline.md` 中 Chapter 1（Introduction and Project
Transition）的写作任务。它以已经成形的 Chapters 2--6、Report 1 结论和当前
evidence map 为边界，负责锁定引言的逻辑、研究问题和章节接口；它不是可直接提交
的论文正文。最终英文仍须由学生重写、核对并统一个人语气。

## 0. Skill 使用与写作顺序

本轮使用 `writing-introduction` 与 `academic-english-style`：

- `writing-introduction` 要求采用 narrowing funnel，并把 gap 放在 aim 之前；
- `academic-english-style` 用于选择准确动词、校准限定语，并避免把有限矩阵写成
  普遍结论。

1.2 只承担 Report 1 -> Report 2 的短过渡，不是文献综述，因此本轮不叠加
`writing-literature-review`。正文初稿完成后，应另行使用 `avoiding-ai-flavor`
检查通用套话、营销式确定性、连续三联句和均匀句式；该检查不能替代学生改写。

建议执行三轮：

| Pass | Skill/责任 | 输出 | 禁止事项 |
|---|---|---|---|
| 结构与初稿 | `writing-introduction` + `academic-english-style` | context -> gap -> aim -> scope -> contribution 的 430--480 词初稿 | 不在此轮逐词追求“漂亮”句式 |
| 独立接受检查 | `avoiding-ai-flavor` | 删除可移植到任意论文的句子，检查证据强度与句式节奏 | 不增加新论点、数字或引用 |
| 作者签核 | 学生本人 | 重写后的个人学术英语与事实核验记录 | 不把 AI 初稿直接视为提交文本 |

## 1. 章节责任与中心漏斗

Chapter 1 只回答四个读者问题：

1. 为什么一个已发表或已命名的 HRSC 算法仍有计算复现问题？
2. Report 1 的哪些结论实际改变了 Report 2 的设计？
3. Report 2 在完成范围内提出哪些可回答的问题，又明确排除什么？
4. Chapters 2--6 已经支持哪些贡献表述，后文怎样展开？

推荐中心句在 1.1 段尾或 1.3 开头首次明确出现：

> This report investigates how arithmetic precision, effective build
> semantics, solver choice and matched CPU/GPU execution affect validated
> ideal-MHD HRSC calculations within a controlled, metadata-bearing
> experiment harness.

该句是 aim，不是结果。最终英文可由学生改写，但必须保留四个限制：研究对象是
ideal-MHD HRSC；比较轴是受控且匹配的；解释以验证为前提；结论绑定配置和 metadata。

全文漏斗顺序固定为：

```text
computational reproducibility
        -> an algorithm name leaves implementation choices open
        -> the Report 1 Euler baseline determines the MHD design
        -> four bounded Report 2 questions
        -> completed contribution and chapter route
```

不从 Euler/MHD 方程、激波重要性、GPU 性能或浮点格式教程开始。删除任何不改变漏斗
焦点的背景句。

## 2. 字数、段落与版面预算

大纲工作范围为 **430--480 words**。建议初稿目标约 **460 words**，给学生重写和
Overleaf 计数差异保留余量。Chapter 1 不新增图、表或公式。

| Section | 目标词数 | 段落 | 唯一任务 |
|---|---:|---:|---|
| 1.1 Reproducibility question | 100--110 | 1 | 从计算复现语境收束到 exact Report 2 question |
| 1.2 How Report 1 informed Report 2 | 60--70 | 1 | 只保留能解释设计决定的 Report 1 输入 |
| 1.3 Research questions and scope | 145--155 | 1 个引导句 + 4 个紧凑 RQ + 1 个 scope 句 | 定义后文章节真正回答的问题和排除项 |
| 1.4 Contributions and report structure | 130--140 | 2 | 三项有下游证据的贡献；随后给 C2--C7 路线 |
| **合计** | **435--475** | **5--6** | 正式计数以 Overleaf 为准 |

若超字数，依次压缩 roadmap、Report 1 signpost 和 RQ 的重复限定语。不得先删除 aim、
scope exclusions、reference boundary 或 reproducibility qualification。

## 3. Chapters 2--6 到 C1 的接口锁

| 已完成章节 | C1 可以承接 | C1 禁止提前写出 |
|---|---|---|
| C2 Project Development | ideal-MHD/GLM 扩展、CPU HLL/HLLD、有界 CUDA HLL 路径，以及这些选择来自 Report 1 基线 | 状态方程、通量、fallback、测试门或开发细节 |
| C3 Methodology | controlled axes、reference hierarchy、matched comparison、metadata-bearing harness 和 deliberate exclusions | matrix 参数、metric 公式、timing/MCA protocol 或命令 |
| C4 Validation | 新 MHD 路径先经数值参考、property/self-refinement 与匹配设备检查，再解释 sensitivity | 任何验证数值、图表观察或“普遍正确”表述 |
| C5 Results | systematic variation 覆盖 precision、build semantics、solver、device、resolution、time、MCA、thread request 与 CFL | 结果值、轴排名、fp32 adequacy、GPU 性能方向或 temporal answer |
| C6 Discussion | reproducibility 需要 experiment、implementation、execution 和 evidence specification；结论绑定配置 | null/non-zero/negative 结果回放或普遍 reproducibility 结论 |

C1 与 C7 的分工同样固定：C1 提问题、定义范围并陈述已完成贡献；C7 才回答问题、
选择 load-bearing findings 并安排 future work。引言不得写成结论摘要。

## 4. 1.1 Reproducibility question

### 单段动作

1. **Anchored context：** 用计算研究中的复现需求开篇。`plesser2018reproducibility`
   只支持“不同领域对 reproducibility/replicability 的术语使用不一致”，不能支持本项目
   的数值或 metadata 充分性。
2. **Operational focus：** 用 `sandveEtAl2013reproducible` 支持保留程序版本、参数和
   人工步骤的实践要求；项目自己的 schema、hash 和 gate 仍是项目设计。
3. **Narrowing gap：** 点明 HLL/HLLD、MUSCL--Hancock 或 ideal-MHD 等算法标签本身
   并不固定算术精度、有效编译语义、分支规则、设备路径和运行配置。这里写成需要被
   控制的 implementation freedom，不宣称文献从未研究过。
4. **Exact question：** 收束到本报告：当这些轴在经过验证的 ideal-MHD 计算中逐一或
   成组改变时，保存状态、运行时间和可复现结论如何受到影响？

段内不得出现结果数值、算例清单或“GPU 更快/结果一致”等答案。`Kritsuk et al.` 的
shared-benchmark citation 已在 C6 承担跨代码比较语境；除非初稿确实需要该功能，C1
不重复加入第三篇背景引用。

## 5. 1.2 How Report 1 informed Report 2

该节只写一个短 signpost，并用 Section~`\ref{sec:ch2-priorities}` 承接完整 decision
map。每个 Report 1 输入都必须导出一个 Report 2 决定：

| Report 1 输入 | C1 中允许的压缩后果 | 完整说明所有者 |
|---|---|---|
| 严格配置下的匹配 CPU/GPU 保存状态在覆盖范围内未观察到差异 | Report 2 保留 matched device paths，而不假设 hardware independence | C2.1、C4、C5 |
| fast-math 和 solver/method 变化可产生不同响应 | 显式控制 build semantics 与 solver axis | C2.1、C3、C5 |
| fp32--fp64 discrepancy 必须与数值参考/离散化尺度区分 | 先建立 MHD validation hierarchy，再解释 variation | C3、C4 |
| final-state-only 分析不能回答时间演化 | 使用预设终止时间的独立运行形成 time-resolved comparison | C2.1、C3、C5 |

正文不逐项复述此表。建议压成两句：第一句定义 Euler baseline，第二句说明它如何导出
MHD 的 matched paths、validation-first interpretation 和 time-resolved design。不要把
ideal MHD 写成 Report 1 “发现后才决定”的方向；它原本就是 Report 2 的既定扩展。

## 6. 1.3 Research questions and scope

研究问题应在初稿前锁定，避免 C1、C3 和 C6 使用不同问题。推荐四问如下；学生可
调整句法，但不能改变 ownership 或扩大范围。

### RQ1 -- MHD validation

> Within the stated numerical-reference and property-based hierarchy, which
> parts of the new CPU and bounded HLL CUDA ideal-MHD implementation are
> sufficiently validated for controlled sensitivity comparisons?

- **回答所有者：** C2 说明实现，C3 定义 gates，C4 给验证证据；
- **边界：** 不问 universal correctness，不暗示 HLLD/KH GPU coverage。

### RQ2 -- systematic implementation variation

> For matched one- and two-dimensional configurations, how do stored-state
> discrepancy and elapsed time respond to arithmetic precision, effective
> build semantics, solver choice, device, requested thread count and CFL?

- **回答所有者：** C3 定义匹配关系，C5 报告结果，C6 解释不同 metric；
- **边界：** solver choice 是 method variation，不自动称为 reproducibility drift；
  Euler rows只提供 compact continuity，不重新承担 Euler validation。

### RQ3 -- scale, time, and stochastic context

> How does the fp32--fp64 discrepancy vary with resolution and observation
> time, and how does its deterministic scale relate to separately scoped
> virtual-precision Monte Carlo arithmetic?

- **回答所有者：** C3 定义 mean norm、fixed window 与 MCA；C5 给 bounded result；
- **边界：** virtual p24/p53 不等于 IEEE fp32/fp64；不同 grid/time 的 packet 不合并；
  temporal fit 不称 formal Lyapunov exponent。

### RQ4 -- reproducibility claim

> What experiment, implementation, execution and evidence information is
> required to reproduce the bounded claims made for the tested ideal-MHD HRSC
> configurations?

- **回答所有者：** C3 的 harness/metadata 与 C6 的 synthesis；
- **边界：** 问的是本项目证据支持的 operational specification，不提出 universal
  reproducibility taxonomy。

### Scope sentence

四问之后用一句话集中声明完成范围之外的工作：MPI、HLLD-on-GPU、KH-on-GPU、
通用 GPU matrix、cross-machine/architecture timing、full-scale KH MCA 和 formal
Lyapunov analysis。不得把“未实现/未完成”改写成这些轴无影响。

## 7. 1.4 Contributions and report structure

### 贡献段

只写 Chapters 2--6 已经展示的 contribution，不使用 “first”、`novel`、
`comprehensive`、`robust` 或其他未经 literature check 的 novelty/marketing 用语。
推荐组织为三个句子，但应改变句长，避免连续模板化三联结构：

1. **Development contribution：** existing Euler harness 被扩展为带 GLM divergence
   control、CPU HLL/HLLD 和 bounded CUDA HLL path 的 ideal-MHD implementation；
2. **Methodological contribution：** controlled, metadata-bearing
   `config -> build -> run -> measure -> aggregate -> plot` workflow 将 reference error、
   cross-variant discrepancy、stochastic spread 和 runtime 分开；
3. **Empirical contribution：** bounded 1D/2D Euler--MHD evidence set 使 precision、
   build semantics、solver/device、resolution/time 和 supplemental axes 能在声明的
   case、metric 与 baseline 内解释。

第三项只描述 evidence capability，不在引言中陈述最小差异、零 ULP、性能方向、
temporal negative result 或 cross-axis importance。

### Roadmap 段

用约 55--65 词覆盖 Chapters 2--7：

- Chapter 2：ideal-MHD development and implementation choices；
- Chapter 3：controlled design, metrics and reproducibility records；
- Chapter 4：validation evidence and limits；
- Chapter 5：precision/hardware/build/solver/time results；
- Chapter 6：reproducibility interpretation and limitations；
- Chapter 7：bounded answers and prioritised future work。

roadmap 使用现在时，不写“Chapter 5 proves/shows”，也不预告具体结果。

## 8. 引用、措辞与时态锁

### 引用锁

| Key/source | C1 允许支持 | C1 不允许支持 |
|---|---|---|
| `plesser2018reproducibility` | 术语在不同领域存在冲突，因此本报告采用 operational usage | 本项目 taxonomy、metadata 或数值结果正确 |
| `sandveEtAl2013reproducible` | 保留 programs、parameters 和 manual procedures 的实践建议 | 当前 harness 足以保证独立复现 |
| Report 1 Chapter 7 + evidence map | 能导出 Report 2 设计决定的受控 Euler 结论 | 重新讲述 Report 1 结果章或复制数值 |
| Report 2 C2--C6 + evidence map | 当前 scope、contribution 和后文章节 ownership | 从 provisional/deferred/invalid evidence 提升 headline claim |

不为 C1 新增未经 `report2/references/reference.md` 核验的文献。Project brief 用于定义
任务和范围，不伪装成同行评议的科学证据。

### 英语与术语锁

- 背景和本报告结构用现在时；Report 1 已完成观察用过去时；
- 优先使用 “This report investigates/examines/characterises”，避免不必要的 `we`；
- 除非明确绑定 numerical reference，否则使用 `discrepancy`、`difference`、
  `sensitivity` 或 `drift`，不用 `accuracy`；
- 使用 British English，与 C2--C6 保持 `optimisation`、`characterise` 等拼写；
- 只在需要范围时使用 hedge；不堆叠 “may suggest/could possibly”；
- 正文不出现 week、P0/P1、gate nickname、packet、源码路径或 local run label。

## 9. 起草执行顺序

1. 从 C6.4 反向提取 1.1 所需的 reproducibility problem，但删去 C6 的答案；
2. 从 C2.1 和 Report 1 Chapter 7 提取 1.2，只保留 decision-causing statements；
3. 先把四个 RQ 原样放入 1.3，并逐个检查在 C4--C6 是否真的有回答所有者；
4. 写 scope sentence，使 deferred/excluded axes 一次出现，不在各 RQ 重复；
5. 从 C2 development、C3 harness 和 C4--C6 evidence synthesis 各提取一项 contribution；
6. 最后写 1.1，让每句收窄并在 gap 之后出现 aim；
7. 压缩 roadmap，使 Chapter 1 达到约 460 词且不泄漏结果；
8. 使用 `academic-english-style` 检查 verb、hedging、时态和 `accuracy`；
9. 独立运行 `avoiding-ai-flavor` 检查；
10. 编译、核对引用与交叉引用，再由学生逐段重写和事实签核。

## 10. Draft 进入门槛

- [x] 1.1 首句是 source-anchored context，不是新闻式或戏剧式开场；
- [x] 每句都从 computational reproducibility 收窄到 ideal-MHD implementation question；
- [x] gap 位于 aim 之前，aim 在本章只出现一次且足够明确；
- [x] 1.2 的每个 Report 1 statement 都解释一个 Report 2 decision；
- [x] RQ1--RQ4 分别覆盖 validation、systematic variation、time/scale/MCA 和 reproducibility；
- [x] 每个 RQ 在 C2--C6 有明确回答所有者，没有许诺未完成实验；
- [x] MPI、GPU/HLLD/KH、cross-machine timing、full KH MCA 和 Lyapunov 边界可见；
- [x] contributions 可由 C2--C6 逐项证明，但没有未经核验的 novelty claim；
- [x] 没有结果数值、findings answer、axis ranking 或 universal conclusion；
- [x] `accuracy`、p24/p53、solver change、three-grid 和 temporal terminology 符合锁定用法；
- [x] 只使用 `reference.md` 已验证的引用，且引用功能未越界；
- [x] 无内部 week/task/gate/packet/file-path 标签进入正文；
- [x] 静态正文估算为 450 words，处于 430--480 working range；正式计数仍以 Overleaf 为准；
- [x] `avoiding-ai-flavor` 检查未发现 banned vocabulary、连续三联句、破折号堆叠或通用段落；
- [ ] 完整 LaTeX 编译待本机 MiKTeX 首次安装配置完成，或在 Overleaf 中执行；
- [ ] 学生完成个人语气重写、C2--C6 事实核验和最终签核。

## 11. 当前 planning 判断

Chapters 2--6 已提供 C1 所需的 development、method、validation、results 和 discussion
接口；写引言不需要新增实验。当前正文已经执行 narrowing-funnel、research-question、
scope、contribution 和 roadmap 设计，没有把 C5/C6 的答案提前写入引言，也没有把
Report 1 signpost 扩写成第二次 Euler 结果回顾。Chapter 1 因此进入
`author-rewrite`：AI-assisted LaTeX draft、引用/交叉引用检查、静态词数和独立
`avoiding-ai-flavor` pass 已完成；剩余门槛为学生改写、Overleaf 正式计数和完整编译。
