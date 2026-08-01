# Chapter 3 写作计划与审查

本计划细化 `manuscript_outline.md` 中 Chapter 3（Experimental Design and
Reproducibility Methodology）的写作任务，并以已完成的 Chapter 4 和 Chapter 5
技术稿为下游接口。它是写作与审查清单，不是可直接提交的论文正文；最终英文须由学生
重写、核对并统一语气。

## 0. Skill 使用与写前基线

本轮使用 `scientific-writing-duke`，不叠加第二个 skill。该 skill 在本章的作用是把
已有技术材料重组为读者可跟随的方法链：已知研究问题放在段首，实验对象作为主语，
控制动作使用明确动词，新定义或解释边界放在句末。C3 不应写成配置项、公式和工具名的
平铺清单。

正文起草与后续检查分开执行：

| Pass | Skill | 本章任务 | 禁止事项 |
|---|---|---|---|
| 方法稿重写 | `scientific-writing-duke` | 建立 question -> controlled comparison -> metric -> claim boundary 的 known-to-new 顺序 | 不先做同义词润色，不用抽象名词代替实验对象 |
| 结构编辑 | `editing-academic-prose` | 删除 C4/C5 已承担的结果和重复定义，压缩到字数上限 | 不在结构未稳定时逐句美化 |
| 接受检查 | `avoiding-ai-flavor` | 检查模板化连接、generic academese、过度对称列表和无证据总结 | 不把机器检查视为学生最终语言 |

本轮只实际应用第一项。后两项应在 C3 英文稿完成后分别执行，不能在同一 pass 中把三个
skill 混用。`report1-context` 不适用于 Report 2；Report 1 只可作为术语连续性来源，
不能为 C3 提供新的结果或范围。

写作前事实来源按以下顺序锁定：

1. `report2/phd-thesis-template-2.4/Chapter4/chapter4.tex` 与
   `Chapter5/chapter5.tex`：确定 C3 必须定义、而结果章已经直接调用的方法接口；
2. `report2/planning/manuscript_outline.md` 与本计划：确定章节责任、字数和结构；
3. `docs/experiment_logs/report2_evidence_map.md`：确定证据状态和不可提升的范围；
4. 当前 machine-readable summaries、生成配置和 metadata：确定实际 grid、end time、
   solver、device、CFL、sample count 和 timing protocol；
5. `report2/references/reference.md`：确定 benchmark 与工具引用可以支持的句子。

## 1. 章节任务与 C4/C5 反向接口

Chapter 3 只回答一个方法问题：**实验如何控制变量、定义比较和记录 provenance，从而使
Chapters 4--5 的验证与敏感性结论在明确范围内可复核？**

它是 test/build/run matrix、reference hierarchy、metrics、statistical treatment、
metadata 和 exclusions 的唯一拥有者。它不报告结果数值，不评价哪个 solver、precision
或 device 更好，也不把已观察到的结果提前解释为结论。

| C4/C5 已调用的接口 | C3 必须一次定义 | C3 不得重述 |
|---|---|---|
| C4 的 reference hierarchy、completion、physical-state 和 divergence checks | 数值参考、自加密、性质门槛、形态检查和完成门槛的层级及用途 | Brio--Wu、GLM、OT、KH 的观测值 |
| C4 的 mean norms、relative mass drift 和 CPU/GPU ULP | 范数口径、质量守恒口径、ULP 适用类型和保存状态范围 | Figure 4.1/4.2 与 Table 4.1 的数值 |
| C5 的 matched groups 和 within-row baseline | 每个变轴比较固定什么、改变什么、以哪一行作 baseline | fp32--fp64、build、solver 或 hardware 的响应大小 |
| C5 的 repeated timing | subprocess wall time、median/IQR，以及两套不同 warm-up policy | Figure 5.2/5.3 的 timing ratios |
| C5 的 refinement context、MCA 和 temporal fits | $D_N/E^{64}_{256,512}$、virtual p24/p53、sample spread、固定窗口与 fit quality | 3% 范围、MCA ratio、slope 或 $R^2$ 结果 |

章节结束时读者应能从任何 C4/C5 数值反向回答四个问题：比较了什么、baseline 是什么、
metric 如何定义、该比较的 scope 在哪里终止。

## 2. 当前 C3 技术稿审计

现有 `Chapter3/chapter3.tex` 已包含七节和主要公式，因此不应继续标为“空骨架”。但它仍是
待重写的技术稿，不能直接视为完成稿。

### 已有且应保留

- 四个 bounded research questions，以及 primary、robustness 和 deferred axes 的区分；
- fp32/fp64、effective build semantics 与 virtual p24/p53 的术语区分；
- Brio--Wu 数值参考、二维 block averaging 和非渐近边界；
- mean/mean-relative norms、$p_{\mathrm{obs}}$、ULP、divergence、MCA spread、
  timing 和 fixed-window temporal fit 的核心定义；
- `config -> build -> run -> measure -> aggregate -> plot` 与 metadata/retention 概述；
- MPI、扩展 GPU、full KH MCA 和 cross-machine timing 的排除范围。

### 必须关闭的内容缺口

1. **Master experiment matrix 缺失**：3.2 只概述了算例，没有集中列出 dimension、
   core grid/end time、boundary、solver/device coverage、变化轴和用途。
2. **Evidence hierarchy table 缺失**：3.4 用 prose 描述层级，但大纲承诺的 compact table
   尚未出现，C4 的 validation hierarchy 因而不能快速反查。
3. **Relative mass drift 未定义**：C4 对 OT/KH 使用该 gate；C3 需要给出统一口径。
4. **Timing protocol 过度统一**：KH CPU timing 是一次排除的 warm-up 加五次 measured
   runs；CPU/GPU repeated timing 保留五次 repetitions，未排除 device warm-up。两者不能
   被一句 blanket policy 合并。
5. **Test-case scope 不够具体**：必须显式区分 OT 的 $128^2/256^2/512^2$, $t=0.5$
   deterministic scope 与 $64^2$, $t=0.05$ MCA scope；Brio--Wu 的同配置 MCA 则可对齐。
6. **字数超限风险**：当前文本的本地粗略 token-to-word 清理计数约 1,130 词，明显高于
   900 词 hard upper；正式判断仍以独立 Overleaf 项目的计数为准。
7. **未被结果章使用的定义需删减**：例如 numerical SNR 若不进入 C5 或 Appendix，
   不应占用 C3 主文；定义应由实际结果反向决定，而不是展示所有可计算指标。

这些缺口都是写作与集成任务，不需要修改 solver、cfg defaults、输出格式或重跑实验。

## 3. 最终结构与字数预算

保留 canonical outline 的七节，不增加第八节，也不把 methods 拆成更多短 subsection。
目标为 840--880 词，hard upper 900 词；表格、表注、caption 和小标题均计入内部预算。

| 小节 | 主文目标 | 表格/公式职责 |
|---|---:|---|
| 3.1 Research questions and controlled axes | 约 75 词 | 定义 RQ1--RQ4；引出 Table 3.1 |
| 3.2 Test-case matrix | 约 70 词 | Table 3.1 承担 case、scope、coverage 和 purpose |
| 3.3 Build and run matrix | 约 80 词 | 只写 baseline、one-axis/composite pair 和 semantics |
| 3.4 Reference hierarchy and validation gates | 约 75 词 | Table 3.2 承担 reference/gate/allowed claim |
| 3.5 Metrics and statistical treatment | 约 235--250 词 | 保留直接被 C4/C5 调用的公式和 protocol |
| 3.6 Harness, metadata, and retention | 约 55 词 | 一段 pipeline/provenance/retention |
| 3.7 Deliberate exclusions | 约 50 词 | 一段 omission -> claim limit |
| Table 3.1、Table 3.2、表注和标题 | 约 170--190 词 | 两表合计，不新增主文 figure |
| **合计** | **约 840--880 词** | 以 Overleaf 最终计数为准 |

若超限，依次删除工具实现细节、未在结果章使用的 metric、重复的“不支持 ranking”句和
配置 prose；不得删除 baseline、scope mismatch、warm-up distinction、metric qualifier 或
deferred-axis limitation。

## 4. 主文表格锁

### Table 3.1：Master experiment and test-case matrix

建议列：case/system、dimension、core scope、boundary、solver/device、controlled role。
表格只列读者理解 C4/C5 所需的科学配置，不列目录名、week、packet、P/G gate nickname 或
每个 build label。

| Case | System/dimension | Core scope | Boundary | Solver/device coverage | Role and varied axes |
|---|---|---|---|---|---|
| Sod | Euler 1D | $N=200$, $t=0.25$ | outflow | HLLC/CPU | compact Report 1 continuity; precision and composite build pair |
| Liska--Wendroff Configuration 3 | Euler 2D | $200^2$, $t=0.3$ | outflow | HLLC/CPU | two-dimensional Euler continuity; precision and composite build pair |
| Brio--Wu | ideal MHD 1D | headline $N=800$, $t=0.1$; validation $N=200,400,800$ against $N=8000$ | outflow | HLL/HLLD CPU; HLL GPU | validation, precision, build/branch, hardware, time and same-scope MCA |
| Orszag--Tang | ideal MHD 2D | $128^2/256^2/512^2$, $t=0.5$; reduced MCA $64^2$, $t=0.05$ | periodic | HLL/HLLD CPU; HLL GPU | resolution, precision, hardware, time and explicitly unmatched MCA |
| Kelvin--Helmholtz | ideal MHD 2D | $128^2/256^2/512^2$, $t=1.0$ | periodic | HLL/HLLD CPU | resolution, precision, solver timing, thread/CFL robustness; full MCA deferred |

集成到 LaTeX 时应进一步压缩单元格文字，并在 table note 统一声明：grid/end time 是各主矩阵
的 report-facing scope；特殊 validation、timing 或 MCA 子矩阵只在表内明确标出的范围内
使用。该表不构造五个 case 的 difficulty 或 accuracy ranking。

### Table 3.2：Reference and gate hierarchy

建议列：evidence class、comparison object、allowed use、prohibited inference。

| Evidence class | Comparison object | Allowed use | Prohibited inference |
|---|---|---|---|
| Aligned high-resolution numerical reference | Brio--Wu candidate against block-averaged fp64 $N=8000$ | bounded numerical-reference difference | exact-solution error |
| Three-grid self-reference | block-averaged $128/256/512$ OT/KH pairs | direction and scale of an engineering trend | asymptotic convergence or solver ranking |
| Property/correctness gates | completion, finite/positive state, invariance, mass drift, divB, saved-state ULP | named implementation or physical-state property | full solution accuracy |
| Literature morphology | expected OT/KH structures | qualitative support only | field-wise validation |

若版面过紧，completion 可与 property gates 合并，不能删除 numerical-reference 与
self-reference 的区别。Table 3.2 只定义证据能力；C4 才报告 gate outcome。

## 5. 分节段落蓝图

### 3.1 Research questions and controlled axes

用一个短段完成四件事：

1. RQ1：precision 与 effective build semantics 是否改变保存状态；
2. RQ2：matched solver/device 变化如何影响保存状态与 wall time；
3. RQ3：fp32--fp64 discrepancy 如何随 resolution/time 变化，并与同 scope 的
   virtual-precision stochastic spread 形成何种 bounded context；
4. RQ4：thread count 与 CFL 是否改变 covered observations。

段尾把 precision、build semantics、solver、device、resolution 和 time 称为 primary axes；
thread count/CFL 称为 supplemental robustness axes；MPI、未实现 GPU 组合、第二机器和
formal Lyapunov analysis 称为 deferred axes。不要提前写 RQ 的答案。

### 3.2 Test-case matrix

本节 prose 只解释 case selection logic，细节交给 Table 3.1：Euler 的 Sod/LW3 只保持
Report 1 到 Report 2 的 compact cross-system continuity；Brio--Wu 提供一维 discontinuous
MHD，OT 提供二维 interacting-wave/current-sheet flow，KH 提供二维 shear instability。

引用边界：Brio--Wu 用 `brioWu1988`；OT 用 `toth2000divb` 并保留 unit-square/time
rescaling；KH 明确写成 project-defined adapted setup，以 `tricco2019kh`、
`frankEtAl1996kh` 和 `lecoanetEtAl2016kh` 分别支持 functional form、weak-field context
和 morphology limitation。不得称 KH 为任何一篇论文的 exact reproduction。

### 3.3 Build and run matrix

建议两个短段：

- 第一段定义 fp64/fp32 deterministic matrix。所有 precision comparisons 使用同 case、
  solver、grid、final time 和 build semantics 的 fp64 行作 numerical baseline。Solver、
  device、thread 或 CFL 比较各自只改变声明的轴，并保留该 packet 所需的固定条件。
- 第二段区分 composite 与 isolated build comparisons。Cross-system 的
  O2-default--Ofast-fast pair 同时改变 recorded semantics，只用于 composite response；
  MSVC 19.51 Brio--Wu clean-build matrix 才分别隔离 `/O2`--`/Ox`、default--`/fp:fast`
  和 $\leq$--$<$。目录标签不是 compiler semantics 证据。

最后一句将 virtual p53/p24 MCA 定义为独立 stochastic matrix；p24 不是 IEEE fp32。

### 3.4 Reference hierarchy and validation gates

先用一句话引入 Table 3.2，再说明每个 claim 使用可用的最强 reference，但较弱 gate 不会
自动升级为 solution accuracy。正文仅需补充三项表格难以表达的操作规则：二维 fine state
在 adjacent-grid comparison 前 conservatively block-average；completion 同时需要 declared
final time、structured success 和 required output；finite/positive、invariance、mass、divB 和
ULP 是相互独立的 gates。

段尾保留两条硬边界：three-grid trend 不等于 asymptotic convergence；morphology 不等于
field-wise accuracy。

### 3.5 Metrics and statistical treatment

本节按“field discrepancy -> physical/correctness diagnostics -> timing -> stochastic/time”
排列，不按脚本或实验目录排列。

#### A. Field discrepancy and refinement context

- 保留一个 combined equation 定义 same-grid $L_{1,\mathrm{mean}}$、
  $L_{2,\mathrm{mean}}$ 和 $L_\infty$；明确 $N=N_xN_y$。
- 用一行区分 physical-domain norms：二维积分范数使用 $\Delta x\Delta y$，而本报告的
  Figure 4.2 和主要 same-grid 2D comparisons 使用明确命名的 mean norms。禁止使用未限定的
  “L1/L2”。
- 保留 cross-system density mean-relative $L_1$ 定义，并说明 fp64 baseline 不是 exact
  state，normalisation 不支持 cross-system ranking。
- 保留 $p_{\mathrm{obs}}=\log_2(E_{128,256}/E_{256,512})$ 和
  $S_N=D_N/E^{64}_{256,512}$。前者是 three-grid engineering diagnostic；后者把
  same-grid precision discrepancy 放到 matched fp64 refinement scale 中，不是 exact-error
  ratio 或 fp32 adequacy criterion。

#### B. Physical-state and implementation diagnostics

- 增加 relative mass drift：
  $|M(t)-M(0)|/|M(0)|$，其中 uniform-grid $M(t)=\sum_{ij}\rho_{ij}\Delta x\Delta y$；
  它是守恒 gate，不是 solution-reference error。
- 保留 centred-interior $\nabla\!\cdot\!\mathbf B$ 的 mean/max 定义，但可压缩为一个
  equation block。说明 raw values 是 grid-scale diagnostics，不是 dimensionless divergence
  errors，mean/max 分开解释。
- ULP 用 prose 定义：只比较相同 IEEE type 的 matched arrays；zero ULP 表示保存的
  conservative state bitwise equal，不代表未保存 intermediate stages 相同。禁止跨
  fp32/fp64 使用 ULP。

#### C. Timing, MCA and temporal fits

- subprocess wall time 从 solver launch 计到 required output 完成，不等于 kernel time。
  所有 repeated groups 报 median/IQR，但 protocol 分开写：KH CPU solver/precision timing
  排除一次 warm-up 后保留五次；hardware packet 保留五次 recorded repetitions，未排除
  device warm-up。Speed-up/ratio 的 numerator 和 denominator 必须在 C5 caption 中点名。
- MCA 保留 sample standard deviation 与 spatial maximum spread；每个值伴随 virtual
  precision、sample count、solver、grid 和 final time。只对 same-scope Brio--Wu 作
  descriptive context；OT reduced scope 不与 deterministic headline ratio。若 numerical
  SNR 不进入结果或 appendix，从 C3 删除其定义。
- Temporal protocol 保留 aligned fp32/fp64 states、fixed case-specific windows、
  $\log e(t)=a+\lambda t$、$R^2$ 和 residual diagnostics。窗口不因结果改变；$\lambda$ 是
  engineering diagnostic，不是 formal maximal Lyapunov exponent 或 physical instability rate。

### 3.6 Harness, metadata, and retention

只写一个段落。实验使用 `config -> build -> run -> measure -> aggregate -> plot`；generated
config、binary/config hash、effective build semantics、return/completion status、diagnostics、
elapsed time 和 summary 形成可审计记录。Aggregators 在出图前检查 completeness 与 scoped
gates。保留 configs/logs/metadata/summaries；大网格除完成明确配对或重新验证所需外删除。

不要列命令、build directory 或脚本目录；Appendix 负责 reproduction routing。

### 3.7 Deliberate exclusions

将遗漏轴与 claim limit 成对写在一个短段中：没有 matched MPI path，因此不讨论 reduction
ordering；没有 HLLD/KH GPU 或 GPU MCA，因此 HLL device result 不能外推；没有第二机器，
因此 timing 不支持 portability；full-scale KH MCA 未完成，因此只能进入 limitation/future
work；fixed-window fit 不构成 formal Lyapunov analysis。Isolation 不能证明 omitted axes
没有影响。

## 6. 证据与配置定位表

路径仅供计划和事实核对；论文 prose 不出现 week、packet 或 run directory。

| 小节 | 主要 authority | 提取内容 | 排除项 |
|---|---|---|---|
| 3.1 | 完成的 C4/C5；`manuscript_outline.md` | 四个 RQ、primary/robustness/deferred axes | 结果答案和 axis ranking |
| 3.2 | `euler_mhd_cross_system/summary.json`；`resolution_ladder/summary.json`；对应 generated configs；`references/reference.md` | case、dimension、grid、end time、boundary、solver/device、引用范围 | Report 1 Euler validation 重述；KH exact-reproduction claim |
| 3.3 | `docs/HARNESS.md`；`euler_mhd_cross_system/summary.json`；`brio_wu_build_semantics/summary.json`；`precision_mca_gate/summary.json` | baseline、effective semantics、isolated/composite comparisons、MCA scope | directory-label semantics；OT scope merge |
| 3.4 | C4 authorities；`brio_wu_1d/summary.json`；`resolution_ladder/summary.json`；CPU/GPU and supplemental summaries | numerical reference、self-reference、completion、physical/property gates | exact MHD solution、asymptotic convergence、morphology accuracy |
| 3.5 | corrected Week-18 summaries；`kh_solver_timing/summary.json`；hardware repeats；temporal summary；MCA summaries | 实际 metric definitions、sample/repeat counts、fit windows 与 quality | historical area-bug 2D L1/L2；blanket warm-up rule；formal Lyapunov claim |
| 3.6 | `docs/HARNESS.md`；experiment manifests；run metadata | pipeline、hash、completion、retention | operational command catalogue |
| 3.7 | `report2_evidence_map.md`；C4/C5 limitations | deferred/uncovered scope | 把 deferred 写成 negative result 或 completed evidence |

## 7. 写作执行顺序

1. 从 machine-readable summaries 和 generated configs 生成 Table 3.1 drafting sheet，
   逐格核对 case、grid、end time、boundary、solver/device 和 special sub-scope；
2. 先写 3.1--3.3，使研究问题、test matrix 和 controlled comparison 在任何 metric 前成立；
3. 写 Table 3.2 和 3.4，建立 C4 所需的 validation hierarchy；
4. 按 C4/C5 实际调用重写 3.5，补 relative mass drift，拆分 timing protocols，删除未使用
   numerical SNR，并保留 metric qualifier；
5. 压缩 3.6--3.7，避免把 Appendix reproduction guide 或 Future Work 写入方法章；
6. 逐条反查 C4/C5：每个被调用的 baseline、metric、gate 和 sample/repeat policy 在 C3
   恰好定义一次；每个 C3 定义在 C4/C5 或 Appendix 有实际消费者；
7. 编译 standalone Report 2，检查表宽、cross-reference、citation、equation numbering 和
   PDF page break；使用 Overleaf 正式计数确认全章不超过 900 词；
8. 另行执行结构编辑与 AI-flavour acceptance pass，最后由学生重写并人工核对所有 scope。

## 8. Draft 完成门槛

- [ ] Table 3.1 包含五个 case 的科学配置、coverage 和 role，且没有内部运行标签；
- [ ] Table 3.2 明确 numerical reference、self-reference、property gate 和 morphology 的
      不同证据能力；
- [ ] RQ1--RQ4 与 C5 的结果块一一对应，但不提前写答案；
- [ ] 每个 comparison 都能识别 changed axis、fixed controls 和 baseline；
- [ ] `O2-default`/`Ofast-fast` 被写成 recorded composite semantics，MSVC direct packet
      被写成 one-axis comparisons；
- [ ] fp32/fp64 与 virtual p24/p53 始终分开，OT unmatched MCA scope 未被合并；
- [ ] mean、mean-relative、physical-domain 和 maximum norms 均有明确限定；
- [ ] relative mass drift、divB、ULP、completion/physical-state gates 已定义且不冒充 accuracy；
- [ ] KH timing 与 hardware timing 的 warm-up/repeat policy 明确分开；
- [ ] temporal windows、$R^2$/residual 和 engineering-rate boundary 完整；
- [ ] 未使用历史 area-bug 2D L1/L2，未把 three-grid diagnostic 称为 asymptotic convergence；
- [ ] harness 段落保留 pipeline/metadata/retention，但没有命令目录；
- [ ] exclusions 限制 claims，而没有把未测试轴写成无影响；
- [ ] C3 没有 C4/C5 结果数字、内部 week/gate label 或 cross-axis leaderboard；
- [ ] standalone LaTeX/BibTeX 编译通过，表格不越界，Overleaf 全章计数不超过 900；
- [ ] 学生完成个人语气、事实和最终 word-count 审读。

## 9. Review 结论

完成的 C4/C5 已提供足够的反向接口来冻结 C3 内容；当前不需要增加实验或改动 solver。
C3 的主要风险不是证据不足，而是方法定义过密且仍缺两个承诺表格。最佳路径是用两张紧凑
表格承接 matrix/hierarchy，用结果章实际消费者筛选公式，并把约 1,130 词的技术稿压缩到
840--880 词。正文集成前必须关闭 relative mass drift 与双 timing protocol 两个接口缺口；
其余工作是结构重写、交叉引用、正式 word count 和学生签署式人工审读。
