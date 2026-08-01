# Chapter 5 写作计划与审查

本计划细化 `manuscript_outline.md` 中 Chapter 5（Precision, Hardware, and
Implementation Results）的写作任务，并以已完成技术草稿的 Chapter 4 为直接上文。
它是写作与审查清单，不是可直接提交的论文正文；最终英文须由学生重写、逐项核对并统一语气。

## 0. 写前语言基线与 skill 准备

### 语言与上下文基线

写作前按以下顺序建立语气和边界：

1. `report2/phd-thesis-template-2.4/Chapter4/chapter4.tex`：直接上文。继承其
   metric 名称、British English、过去时/现在时分工和段尾 boundary，但不重复验证数值；
2. `report1/phd-thesis-template-2.4/Chapter5/chapter5.tex`：只学习 results
   段落如何点名图表、给出最小必要数字、解释意义和限制；
3. `report1/phd-thesis-template-2.4/Chapter6/chapter6.tex`：只学习 negative
   result、限制和跨节过渡的语气；
4. `report2/planning/manuscript_outline.md`、
   `docs/experiment_logs/report2_evidence_map.md` 和本计划：唯一的 Report 2
   事实、证据状态和章节责任来源。

正文段落统一按 **question -> named figure/table -> quantitative observation ->
bounded interpretation** 推进。自有运行和观察使用过去时；图、表和本章论证使用现在时。
`accuracy` 只用于精确解或明确数值参考，其余使用 `discrepancy`、`difference`、
`sensitivity` 或 `drift`。

### 必用 skill 路由

后续正文写作分三轮执行，每轮最多加载两个 skill：

| Pass | 必用 skill | 任务 | 本轮禁止事项 |
|---|---|---|---|
| 写前/初稿 | `scientific-writing-duke` + `academic-english-style` | 建立对象主语、given-to-new flow、时态和 evidence-bound claim | 不做逐词润色，不用泛化形容词代替数字 |
| 结构编辑 | `editing-academic-prose` | 检查段落职责、相邻小节去重和图表解释 | 不在结构未定时追求句式变化 |
| 接受检查 | `avoiding-ai-flavor` | 删除 generic academese、模板化三联句、营销式总结和重复破折号 | 不把机器检查结果视为学生最终语言 |

不得加载 `report1-context` 作为 Report 2 约束，也不得用
`writing-introduction`、`writing-literature-review` 或 `writing-conclusion` 代替结果写作。

### 写前完成条件

- [x] 重读 Chapter 4 全文，建立“只交叉引用、不重述”的 C4/C5 清单；
- [x] 从当前 summary/JSON 生成 C5 drafting sheet，逐个数值记录 metric、baseline、
      grid/end time、solver、precision、CFL、status 和 source path；
- [x] 确认发布图的 PDF hash、caption boundary 和章节归属；五张 C5 PDF 已按原始
      hash 放入 `report2/phd-thesis-template-2.4/Figs/report2/`；
- [x] Chapter 3 已定义 mean norm、mean-relative norm、ULP、timing、MCA spread 和
      temporal-fit protocol，C5 不再重新定义方法；
- [x] 当前正文按 `1,850--1,950` 的章节预算执行，图注和表格文本计入预算。

## 1. 章节任务与 C4--C5 交接

Chapter 4 回答“实现是否在限定测试中通过验证”；Chapter 5 回答“在已验证范围内改变
precision、build semantics、solver、device、resolution、time、thread count 和 CFL 后，
输出差异或运行时间如何变化”。Chapter 5 不再次证明求解器正确，也不把方法变化写成
reproducibility drift。

| Chapter 4 已拥有的内容 | Chapter 5 的承接方式 | 禁止重复或升级 |
|---|---|---|
| Brio--Wu 数值参考、GLM 和二维不变性 | 仅作为系统敏感性结果的验证前提 | 不重报 refinement/GLM 数值 |
| Table 4.1 的四个 CPU/GPU 0-ULP 比较 | 5.6 用一句交叉引用后进入五次重复 timing | 不再创建第二张正确性表，不推出普遍硬件无关性 |
| Figure 4.2 的八组三网格自一致性 | 5.7 只讨论同网格 fp32--fp64 separation 的分辨率依赖 | 不重复 Figure 4.2，不把 observed $p$ 写成精度充分性 |
| OT/KH physical-state、mass 和 divB diagnostics | 作为后续比较的 completion/validity gate | 不用 morphology 或 divB 单独证明 accuracy |
| C4.7 validation limits | 作为 C5 每节解释强度的上限 | 不把局部 workstation/case 结果外推 |

本章的主线按研究问题而非实验时间排列：范围基线 -> deterministic axes -> solver/device
performance -> resolution/time -> stochastic/robustness -> bounded close。内部 week、P0/P1、
gate nickname 和运行目录名只留在计划与附录定位中。

### 推荐的最终排版层级

`editing-academic-prose` 的结构检查发现，1,880 词内使用 11 个同级 `\section`
会产生多个只有一段的短节，使 Figure 5.1 在 5.2--5.4 之间被反复解释。最终 LaTeX
建议保留以下六个主结果块；本计划的 5.1--5.11 编号继续作为 drafting/evidence ID：

| 最终结果块 | 吸收的计划任务 | 连贯问题 |
|---|---|---|
| Result matrix overview | 5.1 | 本章改变哪些轴，比较边界是什么？ |
| Deterministic output sensitivity | 5.2--5.4 | precision 和 effective build semantics 如何改变保存状态？ |
| Solver and device performance | 5.5--5.6 | method/device 改变如何影响 timing，正确性门槛是否保持？ |
| Scale, time, and stochastic sensitivity | 5.7--5.9 | discrepancy 如何随 resolution/time/virtual precision 改变？ |
| Robustness checks | 5.10 | thread count 与 CFL 是否改变已观察结果？ |
| Bounded result summary | 5.11 | 哪些 matched 结论可直接比较，哪些留给 C6？ |

若必须保留 outline 的全部标题，则将 5.2--5.4、5.5--5.6 和 5.7--5.9 设为
subsections，而不是 11 个同级短节。该调整只改变阅读层级，不改变证据责任。

## 2. 证据状态与硬边界

### 可进入正文的主要证据

- **report-grade**：Euler--MHD cross-system、三网格 MHD ladder、五次重复 CPU/GPU timing、
  OpenMP/CFL supplemental、KH solver/precision timing，
  以及通过同配置统一门控的 Brio--Wu HLL/HLLD deterministic-plus-MCA rows；
- **negative-result**：固定窗口 temporal discrepancy；门控与来源完整，但 OT 的低
  $R^2$ 限制 slope 解释，因此只报告未观察到预设对比；
- **validation**：CSC 上 $64^2$, $t=0.05$, $N=4$ 的 KH native-Verificarlo packet，
  只支持管线可用和 reduced-case stochastic scale；
- **provisional**：两个 OT deterministic-plus-MCA rows，以及 KH 的完整
  deterministic/reduced-MCA packets。OT 的 deterministic 为 $256^2$, $t=0.5$，MCA 为
  $64^2$, $t=0.05$；不同 scope 只能分开陈述；
- **invalid/superseded**：旧的 N=8 HLL MCA 和开发 smoke。数值、图和排序全部排除。

### 当前数据完整性锁

1. `resolution_ladder/summary.json` 的 24/24 runs、8/8 self-refinement groups 和
   **12/12** 个同网格 fp32--fp64 density-pair cells 均完整。OT/HLLD/$512^2$ 的 corrected
   completion packet 记录两精度 binary/grid hashes、相同 final time/steps 和 source-semantics
   检查。5.7 可写完整 matrix，但仍不得把 cross-precision separation 称为 accuracy 或
   discretisation error。
2. Week-15 二维历史 L1/L2 受旧 cell-measure 定义影响。新正文只使用 Week-18 的
   corrected mean/mean-relative metrics 或不受该问题影响的 $L_\infty$。
3. build directory label 不是 compiler semantics 的证据。Week-18
   `O2-default` 对 `Ofast-fast` 是同时改变多个 recorded semantics 的 composite pair；
   Week-20 Brio--Wu packet 用八个 clean MSVC builds 和 16/16 runs 分别直接比较
   `/O2`--`/Ox`、compiler-default--`/fp:fast` 和 `<`--`<=`，每对只改变一个 recorded axis。
   三组结果均为 report-grade density sensitivity，但不支持 compiler-wide、performance、
   accuracy 或 portability 结论。
4. 发布图 manifest 已把 `hardware_reproducibility` 统一归入 Chapter 5。C4 继续用
   Table 4.1 承担正确性，C5.6 独占 repeated performance figure，不能在两章重复放图。
5. `experiments/week18/precision_mca_gate/summary.json` 已完成 4/4 source-integrity audit，
   同配置 promotion 为 2/4：Brio--Wu HLL/HLLD 升为 report-grade，OT HLL/HLLD 因
   $256^2$, $t=0.5$ 对 $64^2$, $t=0.05$ 的 scope mismatch 保持 provisional。
6. 当前没有统一、可比较的 cross-axis aggregation。5.11 不生成 ordinal ranking，
   `experiments/week17/report2_synthesis/figures/axis_ranking.png` 永不进入论文。

## 3. 字数与版面预算

目标约 1,880 词，给 Overleaf 计数误差和学生改写保留 70 词余量。下表包含正文目标；
图注、表格文字和小标题另锁定约 250 词。

| 小节 | 正文目标 | 段落/项目 |
|---|---:|---|
| 5.1 Result matrix overview | 80 | 1 段 |
| 5.2 Euler--MHD cross-system sensitivity | 180 | 2 段 + Figure 5.1 |
| 5.3 Deterministic fp32--fp64 sensitivity | 150 | 1--2 段 |
| 5.4 Compiler and branch-rule sensitivity | 120 | 1 段 |
| 5.5 HLL and HLLD comparison | 140 | 1--2 段 + Figure 5.2 |
| 5.6 Matched CPU/GPU correctness and performance | 190 | 2 段 + Figure 5.3 |
| 5.7 Resolution dependence of discrepancies | 150 | 1--2 段 + Figure 5.4；与 Figure 4.2 分工 |
| 5.8 Growth of discrepancies with time | 200 | 2 段 + Figure 5.5 |
| 5.9 Monte Carlo arithmetic | 170 | 2 段 + Table 5.1 |
| 5.10 Thread-count and CFL sensitivity | 150 | 2 段 |
| 5.11 Cross-axis summary | 100 | 1 段 |
| 图注、Table 5.1 和小标题 | 250 | 五图一表 |
| **合计** | **1,880** | 工作目标；正式计数以 Overleaf 为准 |

如果超字数，依次删除 provisional packet 的数字、重复的 method 说明和 C4 已给出的验证
数字；不得先删除 negative result、scope boundary 或图表解释。

## 4. 主文图表锁

### Figure 5.1：Euler--MHD cross-system sensitivity

- **来源**：`fig_cross_system_sensitivity.pdf`；16/16 completion-attested runs；
- **职责**：在四个命名算例内并列展示 fp32--fp64 与 `Ofast-fast`--`O2-default`
  density discrepancy；
- **caption 必含**：图中实际绘制的 mean-relative $L_1$、每行 baseline、Euler/HLLC 与
  MHD/HLL 的 solver 差异；$L_\infty$ 只在正文作为 retained supporting range；
- **禁止**：cross-system accuracy、Euler/MHD 难度排序、solver ranking。

### Figure 5.2：KH solver and precision timing

- **来源**：`fig_kh_timing.pdf`；每组一次 warm-up 后五次 measured runs；
- **职责**：量化固定 workstation、$256^2$、$t=1.0$、CFL 0.4、单 OpenMP thread 下的
  FP32 speed-up 与 HLLD/HLL cost；
- **caption 必含**：median、IQR、warm-up policy、20 个组内重复输出均 0 ULP；
- **禁止**：accuracy--cost Pareto、通用 solver 排名、跨机器 portability。

### Figure 5.3：Repeated CPU/GPU timing

- **来源**：`fig_hardware_reproducibility.pdf`；五次重复的 Brio--Wu/OT、fp64/fp32、
  HLL CPU/GPU evidence；
- **职责**：在交叉引用 Table 4.1 的正确性后，展示 workload-dependent speed-up；
- **caption 必含**：median/IQR、相同精度、0 ULP、tested workstation 和 case/grid；
- **禁止**：HLLD/KH/GPU-MCA、通用 GPU 性能、硬件独立性。

### Figure 5.4：Precision discrepancy relative to refinement scale

- **来源**：`fig_precision_refinement_context.pdf`；12/12 same-grid precision cells；
- **职责**：展示 OT/KH、HLL/HLLD、128/256/512 下的 corrected density mean-$L_1$
  separation，并以 matched fp64 $256^2$--$512^2$ difference 提供尺度背景；
- **caption 必含**：12 cells、每个 case/solver 的 denominator、OT/KH final time 与
  solver-specific CFL；
- **禁止**：exact error、fp32 adequacy、asymptotic convergence 或 solver ranking。

### Figure 5.5：Temporal discrepancy

- **来源**：`fig_temporal_discrepancy.pdf`；固定样本和预定 fit windows；
- **职责**：展示 fp32--fp64 discrepancy 随时间的曲线以及 OT $>$ Brio--Wu 假设未出现；
- **caption 必含**：15/25 paired samples、两个 fit windows、engineering-fit boundary；
- **禁止**：formal maximal Lyapunov exponent、physical instability rate、事后换窗。

### Table 5.1：Matched Brio--Wu deterministic and MCA scales

- **行**：同 scope 的 Brio--Wu HLL/HLLD N=30 report-grade rows；
- **列**：deterministic $L_\infty$、p53/p24 maximum cellwise spread、descriptive ratio 和 scope；
- **附录分工**：OT reduced-scope、KH local/CSC validation 和 unavailable full KH rows 只进入
  Appendix 的 evidence-status table；
- **禁止**：把 p24 称为 fp32、把 ratio 当作相同统计量的比较、合并不同 scope 或形成
  solver ranking。

Figure 4.2 只交叉引用，不在 C5 复制。当前没有 cross-axis ranking 图或统一 effect-size 表。

## 5. 分节段落蓝图

### 5.1 Result matrix overview

- **目的**：从 C4 的 validation boundary 转入系统变轴结果，并点回 Chapter 3 matrix；
- **段落顺序**：验证前提 -> 本章研究问题 -> 小节顺序 -> 每个结论只在 matched scope 内成立；
- **不写**：结果数字、实验时间线、所有 gates 均通过的总括句；
- **过渡**：先用最紧凑的 Euler--MHD range 建立全章尺度。

### 5.2 Euler--MHD cross-system sensitivity

- **Named item**：Figure 5.1；
- **关键观察**：四个 fp32--fp64/O2-default mean-relative density differences 约为
  $1.38\times10^{-7}$--$3.76\times10^{-7}$；fp64 的 build-pair mean-relative
  differences 约为 $4.24\times10^{-17}$--$4.21\times10^{-16}$，而 fp32 的
  build response 从 zero 到 $5.12\times10^{-7}$；
- **解释**：precision 和 effective build pair 的响应依 case/configuration 而变；
- **边界**：不同 physical systems 和 HLLC/HLL 路径不允许 universal ranking，也不是
  Report 1 Euler validation 的重述；
- **过渡**：从四算例范围缩到 MHD 的 matched precision comparison。

### 5.3 Deterministic fp32--fp64 sensitivity

- **证据优先级**：先用 cross-system 的 Brio--Wu/OT report-grade matched rows，再用
  corrected resolution/CFL summaries 补充 KH；Week-15 Brio--Wu unified-gate rows 可作
  bounded 正文支持，OT 和 Week-16 reduced-scope provisional packets 只放状态表/附录；
- **段落顺序**：同 solver/config baseline -> density metric -> 与该 case 的 validation
  scale 分开解释 -> provisional boundary；
- **数字规则**：每个段落最多保留两个 case 的 2--4 个数字，并同时写 grid/end time；
  不把不同 packet 的 OT 数值并列为同一配置；
- **边界**：cross-precision difference 不是 discretisation error，也不证明 fp32 accuracy
  或 adequacy。

### 5.4 Compiler and branch-rule sensitivity

- **第一段**：解释 Figure 5.1 的 `O2-default`--`Ofast-fast` composite pair；它同时改变
  recorded semantics，因此不作单一原因归因；
- **第二段**：使用 Week-20 direct packet 报告 `/Ox`--`/O2` 四组 density zero、
  `/fp:fast` 四组 non-zero，以及 branch rule 在 HLL 为 zero、HLLD 为 non-zero；
- **允许的零结果**：zero response 是有效结果，不用“negligible”代替数字；
- **边界**：只适用于 MSVC 19.51 和命名 Brio--Wu 配置；不报告 performance、accuracy、
  portability 或 compiler-wide ordering。

### 5.5 HLL and HLLD comparison

- **Named item**：Figure 5.2；
- **关键观察**：KH matched timing 中 FP32 speed-up 为 HLL 1.181x、HLLD 1.154x；
  HLLD/HLL median cost 为 fp64 1.147x、fp32 1.173x；
- **段落顺序**：说明 solver change 是 method variation -> 报 timing protocol/数字 ->
  说明组内 repeat 0 ULP -> 限定到 workstation/config；
- **边界**：C4 resolution runs 的 HLL/HLLD CFL 不同，不能从其 discrepancy 或 observed
  $p$ 推出 solver superiority；timing 也不支持 accuracy--cost claim。

### 5.6 Matched CPU/GPU correctness and performance

- **Named item**：Chapter 4 Table 4.1 + Figure 5.3；
- **第一段**：用一句交叉引用说明 covered saved states 为 0 ULP，再立即区分 correctness
  与 performance；
- **第二段关键观察**：Brio--Wu CPU/GPU median ratio 为 fp64 0.510、fp32 0.488；
  OT 为 fp64 6.174、fp32 5.925；由于 timer 未拆分 transfer、launch、I/O 和 compute，
  不解释 workload contrast 的原因；
- **边界**：只覆盖 HLL Brio--Wu/OT、本机和测试 grid；不覆盖 HLLD、KH、GPU MCA、
  kernel-only throughput 或其他 GPU。

### 5.7 Resolution dependence of discrepancies

- **Named item**：Figure 5.4 展示 cross-precision separation；Figure 4.2 只承担
  self-refinement validation，两图不重复；
- **职责**：只报告同一 case/solver/CFL 下 fp32--fp64 density separation 随 grid 的变化；
- **可用例子**：OT/HLL $L_\infty$ 从 $3.565\times10^{-6}$（$128^2$）增至
  $1.676\times10^{-4}$（$512^2$）；KH/HLL 从 $7.066\times10^{-7}$ 增至
  $4.400\times10^{-6}$；KH/HLLD 从 $3.630\times10^{-6}$ 增至
  $1.461\times10^{-5}$；
- **完整性**：8/8 self-refinement groups 与 12/12 same-grid precision-pair cells 均完整；
  OT/HLLD/$512^2$ 的 mean-$L_1$/mean-$L_2$/$L_\infty$ separation 分别为
  $5.554\times10^{-5}$、$4.833\times10^{-4}$ 和 $5.031\times10^{-2}$；
- **边界**：不把 separation 称为 discretisation error，不重复 C4 observed $p$，不做
  cross-solver ranking。

### 5.8 Growth of discrepancies with time

- **Named item**：Figure 5.4；
- **第一段**：陈述预先固定的 hypothesis、15/25 paired samples、Brio--Wu
  $[0.01,0.1]$ 与 OT $[0.1,0.5]$ fit windows；
- **第二段关键观察**：mean-$L_1$ engineering rates 为 30.6153 与 0.0293431；OT
  $L_\infty$ fit 为 -0.0422334；计划中的 OT $>$ Brio--Wu contrast 未出现；
- **fit-quality 分析**：在不改变 fit windows 的前提下，正式 summary 已从
  `records[].fit_*` 数据计算 log-linear $R^2$ 和 residual diagnostics，得到
  Brio--Wu $R^2=0.963$（mean-$L_1$）和 0.852（$L_\infty$），而 OT 分别约为
  0.0073 和 0.0006。后两项表明 OT slope 的解释力很弱；分析脚本、测试、summary、
  evidence map 和发布图已同步；
- **边界**：fit quality 已量化但 gate 不要求最小 $R^2$；不是 formal maximal Lyapunov
  exponent 或 physical instability rate；negative result 不做 post-hoc repair。

### 5.9 Monte Carlo arithmetic

- **Named item**：Table 5.1；
- **第一段**：用 Chapter 3 定义后的术语解释 p53 noise floor 与 p24 virtual precision，
  并只对同 scope 的 Brio--Wu N=30 rows 给出 deterministic/p24 descriptive ratio；
- **第二段**：OT N=30 的 MCA 与 deterministic scope 不同，因此不合并；KH local、CSC
  reduced validation 和 full unavailable rows 由 Appendix 状态表承接；
- **status 处理**：正文表只保留 report-grade Brio--Wu，Appendix 明确列出 provisional、
  provenance、validation 和 unavailable rows；
- **边界**：p24 不是 IEEE fp32；不同 N、grid、machine 和 solver 不合并排序。

### 5.10 Thread-count and CFL sensitivity

- **第一段（thread count）**：OT/KH 在 1/2/4/8 OpenMP threads 下 covered outputs
  最大 ULP 和 absolute drift 均为 zero；这说明该本机/配置的 thread reproducibility，
  不说明 OpenMP scaling 或 MPI ordering；
- **第二段（CFL）**：KH CFL 0.2/0.4/0.6/0.8 均完成且 finite/positive；fp32--fp64
  $L_\infty(\rho)$ 对 CFL 为 non-monotonic，例如 HLL 为
  $4.678\times10^{-6}$、$1.786\times10^{-6}$、$2.133\times10^{-6}$、
  $8.910\times10^{-7}$；
- **边界**：CFL sweep 是 sensitivity study，不是 formal temporal convergence；
  HLL/HLLD 数值不形成 general solver ranking。

### 5.11 Cross-axis summary

- **目的**：用一个短段回答“哪些结论是直接 matched、哪些不可比较”，并把 interpretation
  交给 Chapter 6；
- **可写**：device correctness、workload-dependent timing、CPU KH precision/solver timing、
  fixed-window negative result 分别在各自 metric/scope 内成立；
- **不写**：新的数字、任意归一化、axis leaderboard、provisional row promotion；
- **项目决策**：使用 `chapter5_result_scope_matrix.md` 区分 coverage/scope，但不生成
  cross-axis quantitative comparison table；若该矩阵进正文，MCA status table 移到 Appendix。

## 6. 证据定位表

| 小节 | 当前 authority | 状态 | 正文用途 | 排除项 |
|---|---|---|---|---|
| 5.2/5.4 | `experiments/week18/euler_mhd_cross_system/summary.{md,json}` + `experiments/week20/brio_wu_build_semantics/summary.{md,json,csv}` | report-grade | composite cross-system range + direct one-axis build sensitivity | accuracy、performance、compiler-wide/system/solver ranking |
| 5.3 | 上项 + `experiments/week18/resolution_ladder/summary.json` + supplemental CFL | report-grade/局部完整 | bounded deterministic precision | 历史 2D L1/L2、fp32 adequacy |
| 5.4 | `experiments/week20/brio_wu_build_semantics/summary.{md,json,csv}` | report-grade direct density sensitivity | `/O2`--`/Ox`、math mode、branch rule 的 matched Brio--Wu comparisons | performance、accuracy、portability、compiler-wide conclusion |
| 5.5 | `experiments/week18/kh_solver_timing/summary.{md,json}` | report-grade | repeated KH solver/precision timing | accuracy--cost、portability |
| 5.6 | `experiments/week18/supplemental/hardware_repeats/summary.{md,json}` | report-grade | repeated CPU/GPU timing and 0 ULP | generic GPU matrix |
| 5.7 | `experiments/week18/resolution_ladder/summary.json` + `resolution_ladder_pair_completion/summary.json` | report-grade；12/12 precision cells | resolution-dependent separation | asymptotic order、accuracy、discretisation error |
| 5.8 | `experiments/week15/mhd_temporal_divergence/summary.{md,json}` | negative-result | fixed-window engineering fits | formal Lyapunov/physical rate |
| 5.9 | `experiments/week18/precision_mca_gate/summary.json`；Week-15 N=30 packets；`experiments/week18/csc_findings_synthesis/summary.json` | report-grade + provisional + validation | status-aware MCA observations | cross-scope OT merge、full KH MCA、solver ranking |
| 5.10 | `experiments/week18/supplemental/{thread_repro,kh_cfl}/summary.{md,json}` | report-grade | thread reproducibility/CFL sensitivity | MPI、scaling、time convergence |
| 5.11 | 上述 matched rows only | 无统一 aggregation | bounded close | arbitrary axis ranking |

## 7. 写作执行顺序

1. **建立 drafting sheet**：已从 JSON/CSV 生成
   `experiments/week18/chapter5_drafting_sheet/summary.{md,json}`、`facts.csv` 和
   `mca_status_table.{md,csv}`，逐项保留 status 和完整 scope；
2. **锁定图表**：核对五个 PDF hash，修正/确认 hardware figure 的 C5 ownership，生成
   MCA status table；
3. **写 5.1--5.4**：完成 cross-system、deterministic precision 和 direct build semantics，
   将 composite pair 与 one-axis comparisons 分开；
4. **写 5.5--5.7**：solver timing -> hardware timing -> resolution-dependent separation，
   每处显式区分 correctness、performance 和 discrepancy；
5. **写 5.8--5.10**：先保留 temporal negative result，再写 status-aware MCA 和两项
   robustness；
6. **写 5.11**：只在前十节稳定后写 bounded close，不创建新 aggregation；
7. **结构编辑**：删掉 C4 重复、方法复述和跨小节重复数字；
8. **接受检查**：逐项查 metric/baseline/scope、引用、图注、AI flavour 和 British English；
9. **学生重写**：人工核对所有数字、claim boundary 和 Overleaf 词数。

## 8. Review 结论与门槛

### Review 发现并已在计划中关闭的风险

- C4/C5 重叠通过“C4 验证、C5 变轴敏感性/性能”的责任表关闭；
- Figure 4.2 不在 C5 重复，5.7 只承接 cross-precision separation；
- 单次 CPU/GPU timing 被五次重复证据取代，正确性仍由 C4 Table 4.1 所有；
- 历史二维 L1/L2 被 corrected Week-18 mean/mean-relative metrics 取代；
- unified audit 只提升同配置 Brio--Wu 两行；OT/KH reduced-scope precision/MCA packets
  不承担 headline；
- MCA 通过 status table 区分 N=30 report-grade/provisional、N=4 validation、invalid 和 blocked；
- temporal negative result 保留固定窗口和未观察到的对比，不做事后修复；
- cross-axis arbitrary ranking 被明确排除，5.11 不越权进入 Chapter 6 discussion。

### 已关闭的正文集成硬门槛

1. audited `hardware_reproducibility` figure 已唯一归入 C5.6；
2. OT/HLLD/$512^2$ paired fp32--fp64 metric 已由定向 corrected run 补齐；集成时只使用
   completion packet 的 12/12 summary，不再引用旧的缺失状态。
3. fixed-window fit-quality 已加入正式 summary；正文必须报告低 OT $R^2$，不能用 slope
   的符号或大小承担物理解读。

以上三项均已关闭，不再阻止正文起草；集成时仍须只引用这里列出的最新 summary。

### Draft 完成门槛

- [x] 每节至少包含 purpose、named item/source、quantitative observation、meaning 和 boundary；
- [x] 所有数字可追溯到第 6 节 authority，且 drafting sheet 记录 metric/baseline/scope；
- [x] C4 只被交叉引用，不重报 validation table/figure 的数值；
- [x] Figure 5.1--5.5 和 Table 5.1 均在正文中被点名、解释并限定；
- [x] 5.4 只使用 Week-20 clean-build direct packet 作拆轴结论，并保留 compiler-wide、
      performance、accuracy 和 portability 边界；
- [x] 5.7 明确 8/8 self-refinement groups 与 12/12 precision-pair cells 是两类不同证据；
- [x] 5.8 明确 engineering fit、固定窗口、negative contrast 和 fit-quality limitation；
- [x] 5.9 始终区分 virtual p24/p53 与 IEEE fp32/fp64；
- [x] 5.10 将 thread reproducibility、performance scaling、CFL sensitivity 和 time
      convergence 四个问题分开；
- [x] 未出现 week、P0/P1、gate nickname、run directory 或 arbitrary axis ranking；
- [x] 本地静态章节计数 1,950，图注和表格已计入；
- [x] 已完成结构、段落职责、British English、generic academese 和重复总结的独立人工 pass；
- [x] 数字已与 machine-readable summaries 绑定，引用与完整 LaTeX/BibTeX 编译通过；
- [ ] 学生完成最终个人语气确认和提交前签署式人工审读。

### 总体 review 判断

该计划与 `manuscript_outline.md` 的 5.1--5.11 证据任务、当前六个主块 LaTeX 层级、
C4 已完成内容、Chapter 5 责任锁和当前
evidence map 一致。计划状态现为 `completed-pending-student-signoff`。正文只按机器审计提升了同
scope 的 Brio--Wu rows，保留 OT/KH provisional/validation 边界，也没有用不可比较
指标构造跨轴排名。五图一表已集成，OT/HLLD/$512^2$ paired precision 缺口已关闭，
正文保留了 fit-quality、non-asymptotic 和 cross-precision-not-accuracy 边界。

## 9. Skill-based 第二轮 review：可增加内容与实验

本节使用 `scientific-writing-duke` 检查 question--evidence--interpretation 链，并使用
`editing-academic-prose` 按“结构 -> 段落 -> 句子 -> 词”顺序复核。结论是：C5 当前覆盖
brief 所需的 precision、hardware、compiler/build、implementation、time、1D/2D MHD
和 Euler continuity，不需要再增加新物理算例。最有价值的增量是关闭现有证据链的三个
缺口，而不是扩大 case 数量。

### 建议增加的论文内容（无需新 solver runs）

| 优先级 | 内容 | 论文价值 | 放置位置 | 接受条件 |
|---|---|---|---|---|
| P0--完成 | **量化 temporal fit quality**：增加 fixed-window $R^2$ 和 residual diagnostic | 防止把 OT 的近零、低解释力 slope 写成增长率证据；使 negative result 更可信 | 5.8；发布图标注 slope 与 $R^2$ | fit windows 未变；脚本/测试/summary/evidence map/manifest 已同步；正文称 engineering fit |
| P1--完成 | **建立 machine-readable unified deterministic-plus-MCA gate** | 4/4 source-integrity audit 通过；scope-derived promotion 为 2/4 | Brio--Wu HLL/HLLD 同配置 rows 升为 report-grade；OT 因 $256^2/t=0.5$ 对 $64^2/t=0.05$ mismatch 保持 provisional | aggregate summary、source hashes、metadata-derived scope、脚本和测试已生成；未静默 promotion |
| P1--完成 | **增加 non-ranking result-scope matrix** | 已按十个变化轴区分“输出是否改变”“是否有 repeated timing”“status/scope” | `report2/planning/chapter5_result_scope_matrix.md`；可用于 5.1/5.11 或 Appendix；若进正文则把 MCA status table 移到 Appendix | 未把不同 metric 归一化或排序；不重复具体结果数值 |
| P1--完成 | **显式回答 Chapter 3 research questions** | 各结果块均以 scope boundary 收束，5.11 汇总 matched answers，避免章节成为数字清单 | 5.2--5.10 各块段尾 + 5.11 | 只回答本节 RQ，不引入 discussion 或新证据 |
| P2--完成 | **增加“确定性重复基线 vs 变轴响应”叙述** | 组内 repeat、device 和 thread 的 0 ULP/zero difference 与 precision/build/CFL 的 non-zero response 分开陈述 | 5.6、5.10、5.11 | 只作 covered rows 的 zero/non-zero 区分，不声称统一 noise threshold 或 signal-to-noise ratio |

Temporal $R^2$ 已从 retained summary 完成正式聚合，无需重跑 80 个 solver jobs；其值现为
evidence authority 的一部分，可在 5.8 按固定窗口和 engineering-fit boundary 使用。

### 建议新增或补齐的实验

| 优先级 | 实验/分析任务 | 预计成本与风险 | 可新增的论述 | 决策 |
|---|---|---|---|---|
| P0--完成 | **补跑 corrected OT/HLLD/fp32/$512^2$ 并与已保留的 corrected fp64 grid 配对** | measured wall time 420.874 s；两精度 binary/grid hashes、final time、3277 steps 和 source semantics 均已核对 | resolution-dependent cross-precision cells 已从 11/12 闭合到 12/12 | 已执行；这是证据完整性修复，不扩大 scope |
| P1--完成 | **统一审计四个 Brio--Wu/OT HLL/HLLD deterministic+MCA packets** | 无 solver rerun；核对 24-row matrix、N=30 blocks、source hashes、finite metrics 和配置 scope | 闭合 Brio--Wu 两行；明确证明 OT 两行不能跨 scope 合并，强化 5.3/5.9 的边界论述 | 输出 `experiments/week18/precision_mca_gate/summary.{md,json,csv}`；不对 OT 数值作 ratio |
| P1--完成 | **Brio--Wu direct build-semantics matrix**：`/O2`--`/Ox`、default--`/fp:fast`、`<`--`<=` | 八个 clean MSVC builds、16/16 HLL/HLLD x fp64/fp32 runs；保留 flags、binary hashes、configs、logs 和 metadata | 把 Week-18 composite pair 与 one-axis density response 分开；optimisation 四组为 zero，fast-math 四组 non-zero，branch 仅 HLLD non-zero | 输出 `experiments/week20/brio_wu_build_semantics/summary.{md,json,csv}`；不加入 performance 或 compiler-wide claim |
| P2 | **OT GPU resolution/timing ladder：128/256/512，fp64/fp32，至少 3 次 measured repeats** | CPU 512 rows 最耗时，整体仍可能在一小时级；需新 matrix、metadata、median/IQR summary 和图 | 把“Brio 小任务慢、OT 大任务快”升级为同一 case 内的 workload-size trend | 可选；仅在正文初稿和 P0 缺口已关闭后执行 |
| P2 | **selected build-pair repeated timing**：O2-default vs Ofast-fast | 需要限定 1D/2D 代表 case 并做 warm-up + repeats；容易挤占写作时间 | 可讨论 build semantics 的 performance/output trade-off，而不只 output discrepancy | 可选；不应用历史单次 wall time 代替 repeats |
| P3 | **第二机器复现 repeated timing** | 环境、编译器、GPU 和排队不确定，截止前风险高 | 增加 portability 维度 | 不建议作为当前主线；列入 future work |

所有新增实验都必须进入 `config -> build -> run -> measure -> aggregate -> plot`，保留
generated config、binary/config hash、stdout/stderr、completion metadata 和 summary；大网格按
retention rule 删除，除非它是完成缺失配对所需的审计 artefact。

### 当前不建议增加的工作

- **不新增物理 case**：Sod、LW3、Brio--Wu、OT 和 KH 已覆盖 Euler/MHD、1D/2D、
  discontinuity/complex-flow 的 brief 范围；新 case 会稀释每个结果块的解释字数；
- **不在本机重启 full KH MCA**：$256^2$, $t=1.0$, $N=30$ 已有 runtime-blocked 记录，
  截止前成本和失败风险高；只有现成 CSC jobs 在 freeze 前完整通过时才接收；
- **不增加 MPI、HLLD-on-GPU 或 KH-on-GPU**：这些会扩大实现与验证 scope，无法由当前
  CPU/GPU gate 继承；
- **不为获得正结果改变 temporal fit window**：应增加 fit-quality 诊断，而不是修复
  negative contrast；
- **不生成跨 metric axis ranking**：即使增加 result-scope matrix，也只列 matched
  evidence 和 coverage，不给 ordinal leaderboard。

### 截止前推荐顺序

1. Temporal $R^2$/residual 和 OT/HLLD/fp32/$512^2$ 配对已完成；
2. 立即起草 C5 主文；unified deterministic+MCA audit 已完成，按 2/4 promotion 写 Table 5.1；
3. Brio--Wu 可作同配置 bounded result，OT 保留 reduced-scope provisional，不延误正文；
4. non-ranking result-scope matrix 已完成；正文按版面在它与 MCA status table 中二选一留主文；
5. 只有正文、引用、图注和 Overleaf 词数稳定后，才考虑 GPU size ladder 或 build timing；
6. full KH MCA、第二机器、MPI 和新物理 case 进入 Future Work。
