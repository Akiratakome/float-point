# Report 2 严格审阅逐项修订计划（subagent 版）

## 1. 目标与不可突破的边界

本计划把 2026-08-03 严格审阅中的每项意见拆成可独立委派的最小
section-level 任务。执行时，每个任务只交给一个 subagent；同一 subagent
不得顺手修改相邻章节。总控 agent 只负责派发、冲突检查、编译和最终验收。

- 正式目标是 Report 2 **不超过 7,500 words**；7,875 只是 5% 无扣分容差，
  不是写作目标。
- authoritative local baseline 是 `texcount -inc -sum = 6,994`；本轮所有
  正文、表格、图注和 appendix 的累计**净增不得超过 250 words**，优先净减。
  最终以独立 Overleaf project count 为准。
- 不新增或伪造实验。没有现成 logged evidence 的建议只能写入
  `Limitations` 或 `Prioritised future work`，不能写成已完成结果。
- 不改变 solver numerics、既有 cfg defaults、输出格式、原始/聚合数据，
  不提交 build directories 或 transient grids。
- 工作树很脏。每个 agent 开始前记录目标文件的 diff，只修改表中列出的
  section/asset，不回滚、不格式化、不整理其他人的改动。
- 每个数值句必须给出 case、baseline、metric 和 scope；`accuracy` 仅用于
  有合法 reference 的 error，其他比较使用 `discrepancy`、`sensitivity` 或
  `drift`。
- AI 草稿仍需学生本人重写和逐句核实后才可提交。

## 2. 执行协议

每个 subagent 必须依次完成：

1. 阅读 `docs/INDEX.md`、`docs/HARNESS.md`、
   `report2/planning/reportagents.md`，再阅读本任务列出的证据源。
2. 用 section label/明确锚点定位写入范围；不要依赖会漂移的行号。
3. 开始前运行 `git diff -- <target>`，保留已有用户改动。
4. 仅提交局部 patch，并在回报中列出：改动文件、净字数、引用/数值来源、
   未解决缺口。证据不足时停止写结论，回报 `evidence-blocked`。
5. 运行与改动成比例的局部检查；不得自行扩大为新实验。

任务可以并行的前提是目标文件不重叠。即使锚点不同，同一 `.tex` 文件的任务
也应顺序执行，以降低共享工作树冲突。

## 3. 小节级任务矩阵

下表的净字数预算是 hard ceiling，不是必须增加的字数。负数表示应通过替换和
去重缩短。`R0` 为引用前置 gate；`I1--I3` 为最终集成 gate。

| ID | 审阅意见与局部目标 | 唯一写入目标 | 允许改动 | 禁止事项 | 必读证据源 | 净字数预算 | 验收标准 | 依赖 |
|---|---|---|---|---|---|---:|---|---|
| R0 | 核验新增文献候选，避免“真实但不支持该句” | `References/references.bib`；`report2/references/reference.md` 中新增记录 | 核验并按实际用途加入 Torrilhon (2003)、Celik et al. (2008)、Mignone et al. (2010)、Ahrens et al. (2020)；Parker (1997) 仅在找到一手可核元数据且正文确需时加入 | 不改正文；不凭二手网页猜 DOI/页码；不为增加数量而加文献 | 出版商/DOI 一手页；现有 `reference.md` 的逐条审计格式 | 0（bibliography 不计；审计文档不进论文） | 每个新增 key 有可核元数据、允许支撑的命题和明确禁止的外推；未验证候选不进入 bib | 无，必须最先完成 |
| D1 | 让 Report 1 如何决定 Report 2 可被直接评分；说明 representative-range 选择和开发受阻后的取舍 | Chapter 2，`Development priorities after Report 1` | 将现有两段压成一个 4-row 左右的紧凑 decision map，字段为 finding/limitation → Report 2 decision → evidence outcome；纳入 runtime、comparability、MCA timeout、GPU HLLD/KH/MPI deferred 的决策理由 | 不复述 Report 1 结果章；不写周记；不把 deferred 写成失败的科学结论 | Report 1 conclusion；`docs/experiment_logs/report1_evidence_map.md`；`report2_evidence_map.md`；project brief | +25 | 每一条 Report 1 内容都导向一个 Report 2 决策；“representative”由 physics/risk/comparability/runtime/evidence value 定义；表与正文不重复 | R0 |
| D2 | 补足自洽的 MHD/GLM 基础概念 | Chapter 2，`Ideal-MHD and GLM additions` | 用替换而非扩写补清 GLM augmented coupling、`c_h`/`c_r` 的作用和 `c_r=0` 行为、primitive/conservative reconstruction 事实、Lie split 的时间阶边界；引用 cell-centred GLM 文献（若 R0 验证通过） | 不重做 Report 1 的 finite-volume/MUSCL 推导；不改变公式或实现事实；不宣称 CT/GLM 优劣 | `src/mhd/` 对应实现；Dedner 2002；R0 核验的 Mignone et al. 2010 | +35 | 读者无需 Report 1 也能理解新增 MHD/GLM 状态、清理和 split；每个实现细节与源码相符 | R0 → D1 |
| D3 | 澄清 HLL/HLLD 的波结构、退化分支与 fallback attribution 限制 | Chapter 2，`HLL and HLLD solver paths` | 精简补充 signal-speed/中间波差异；明确 fallback 条件；加一句“当前报告未记录 fallback/branch-hit counts，因此不能把差异唯一归因于某分支” | 不创造 counts；不将 HLLD 称为更准确；不改默认 solver | `src/mhd/` HLL/HLLD/fallback 实现；Miyoshi & Kusano 2005；build-semantics summary | +15 | HLL/HLLD 描述准确；结果机制与未经记录的 branch/fallback attribution 清楚分开 | D2 |
| D4 | 把 1/2/4/8 threads 正确降格为 unused-setting null control | Chapter 2，`CPU, OpenMP build control, and CUDA implementation` | 删除可能让人误认已做 parallelisation study 的表述；保留 serial sweep、no work sharing、no scaling/ordering claim | 不删除 OpenMP metadata 事实；不暗示 MPI/GPU HLLD/KH coverage | `experiments/week18/supplemental/`；`src/mhd/`；`docs/HARNESS.md` | -10 | 单独阅读本节不会把 thread experiment 理解成 parallel speed-up/reproducibility study | D3 |
| M1 | 规范 reference hierarchy，并解释为何三网格不能自动成为 GCI/正式收敛证据 | Chapter 3，`Reference hierarchy and validation gates` | 加入 Brio--Wu pseudo-convergence 风险和 shock-containing three-grid/GCI 适用边界；仅在 R0 验证后引用 Torrilhon/Celik | 不计算未经验证的 GCI；不把同代码 N=8000 称 exact；不把 morphology 称 validation | Brio--Wu packet；resolution-ladder summary；R0 文献审计 | +25 | exact/numerical/self-refinement/morphology/implementation checks 四级区分清楚；说明未报告 GCI 的科学理由 | R0 → D4 |
| M2 | 避免“3% refinement scale”被读成 fp32 accuracy/adequacy | Chapter 3，`Metrics and statistical treatment` 中 `S_N` 定义段 | 将 `S_N` 明确命名为 diagnostic ratio；说明分母不是误差/uncertainty，不允许跨 case/solver 排名 | 不改数值和公式；不引入新 threshold；不称其 error ratio | `experiments/week18/resolution_ladder/summary.md`；Chapter 5 source figure manifest | -5 | 公式、caption 和 Chapter 5 用词可以一致映射；无 adequacy 暗示 | M1 |
| M3 | 完善 timing protocol 和硬件/软件环境可复核性 | Chapter 3，`Metrics and statistical treatment` 的 elapsed-time 段；若已有环境表则只更新该表 | 明确 KH warm-up 与 CPU/GPU 无独立 warm-up的差异；加入已有 metadata 能证明的 OS/CPU/GPU/compiler/CUDA/driver 字段，优先用紧凑表或脚注替换散文 | 不查询当前机器来冒充历史 run 环境；缺字段标“未记录”；不重跑 timing | hardware repeats metadata/summary；KH solver timing summary；build-semantics metadata | +30 | timer boundary、n、median/IQR、warm-up、单机范围和已记录环境齐全；历史未知项不猜测 | M2 |
| M4 | 改善 temporal 模型解释，并登记 KH time-history 缺口 | Chapter 3，`Metrics and statistical treatment` 的 temporal-fit 段 | 保留预声明窗口；把 shock-position/shift-aligned metric、transport metric、KH temporal series 写为未完成的诊断/未来需求，至多一句 | 不事后改 window；不把 slope 称 Lyapunov exponent；不生成新时间序列 | temporal-divergence summary；Chapter 5 figure/source manifest | 0 | 预设模型、fit-quality、serial correlation 与替代诊断的状态清楚；不把建议写成已做 | M3 |
| V1 | 加固 Brio--Wu internal comparator 的可信度边界 | Chapter 4，`Brio--Wu numerical-reference assessment` | 用 Torrilhon（R0 通过后）说明 MHD Riemann pseudo-convergence/非唯一性风险；保留已有单调 self-reference 观察 | 不否定现有数据；不称 N=8000 exact/converged；不新增 solver comparison | Brio--Wu summary；Torrilhon 一手文献；Chapter 3 reference hierarchy | +15 | “approached defined internal comparator”与“physical/exact accuracy”严格分离 | R0 → M1 |
| V2 | 明确 CPU/GPU bit identity 只能验证 correspondence | Chapter 4，`Matched CPU/GPU implementation verification` | 压缩并突出“两个实现可一致但共同错误”；保留覆盖的四个组合和未保存 intermediate 的边界 | 不重复性能结果；不扩大到 HLLD/KH/其他设备 | CPU/GPU hardware-axis summary；Chapter 4 table | -10 | 结果只支持 bounded saved-state consistency，不出现独立 accuracy/correctness 外推 | V1 |
| V3 | 对二维 OT/KH validation 缺口作单点汇总 | Chapter 4，`Validation limits` | 明列缺失：independent fieldwise reference、smooth linear MHD/Alfvén convergence、dimensionless divB、全变量 conservation；把 Athena/Athena++/PLUTO matched comparison 定位为 future validation | 不在 OT/KH 结果段重复长免责声明；不写未做结果；不新增数值 | OT/KH summaries；Athena/Athena++/PLUTO 已核文献；evidence map | +25 | 审稿人能一处看清 2D evidence 能/不能证明什么；不削弱已有 property-check 结果 | V2 |
| S1 | 防止 density-only 结果被误写成完整 MHD accuracy | Chapter 5，`Deterministic fp32--fp64 sensitivity` | 明确 systematic comparison 的 reported field 是 density；指出未系统报告 `B,p,E,divB` 和 conservation 的局限，交叉引用 V3 | 不制造其他 field 数值；不说 density 代表全状态 | deterministic precision summaries；Chapter 3 metric contract | 0 | 所有 adequacy/whole-state 暗示消失；已报告和未报告 variables 清楚 | V3 |
| S2 | 修正 build-semantics 因果归因与 log-zero 表现 | Chapter 5，`Effective build-semantics sensitivity` 及 `ch5_build_semantics` 对应 plot/caption | 文本说明 `/fp:fast` 可能包含 reassociation/FMA 等但当前未隔离；branch结果因无 hit count 仅为响应；把 log 轴零值改成独立 bit-identical marker/row，并从原 summary 重新 scripted plot | 不改 summary/data；不声称某机制已被识别；不手工涂改图片 | week20 summary/json；figure source script/manifest；MSVC `/fp` 官方文档 | -5 | 零值视觉上不伪装为小非零；文本不超出单 MSVC/单 case/密度 scope；图哈希/provenance 更新 | S1 |
| P1 | 强化性能实验的稳定性边界和 outlier 处理 | Chapter 5，`Matched CPU/GPU agreement and performance` 及其 caption | 以 raw-point/IQR 事实描述 2.695 s observation；说明无 device warm-up、end-to-end 混合 launch/transfer/I/O/compute；统一称 observed workstation ratio | 不删除 outlier；不做无预注册的 outlier exclusion；不泛化 GPU speed-up | hardware repeats summary/json/metadata；Chapter 3 timing protocol | -10 | 6.174/5.925 等只作为本机观测；样本量、timer、warm-up/outlier 均可见 | M3 → S2 |
| T1 | 让 temporal negative result 比 slope 数字更科学 | Chapter 5，`Growth of discrepancies with time` | 压缩 OT slope 展示，突出 `R^2≈0` 即模型不适用；保留 Brio shock drift 解释；把 shift/transport metric 与 KH series 仅列作缺失诊断 | 不改 fit/window；不把 Brio 墵称 chaos；不比较未归一化 case slopes | temporal-divergence summary/json；Chapter 3 temporal protocol | -15 | negative result 是主结论；低 `R^2` 的 slope 不再承担解释作用；KH omission 明示而不伪补 | M4 → P1 |
| C1 | 给出限定范围内的 case × axis 综合判断，而不是回避所有比较 | Chapter 6，`Relative importance of the tested axes` | 将散文重组为紧凑 `case × axis × observed response × boundary` 表或等价短段；允许同 metric/同 scope 内比较，禁止 arbitrary cross-metric leaderboard | 不创造统一 score；不跨 unmatched CFL/grid/device；不新增结果 | Chapters 4--5；week17 synthesis summary（禁用 arbitrary-scale ranking figure） | +20 | 至少明确 OT/HLLD 512 local `L_inf`、Brio HLLD branch response、Brio/OT GPU timing contrast、OT temporal negative result，各自附边界 | T1 |
| C2 | 增加数值机制解释而不冒充因果证明 | Chapter 6，`Accuracy, discrepancy, and performance trade-offs` | 用限定语解释：HLLD 分支/中间波可能提高敏感性；shock displacement 放大 `L_inf`；GPU overhead 主导小 workload；fast-math 允许的变换可能改变路径；GLM 参数影响 cleaning | 不用“caused/proved”描述未隔离机制；不重复 Chapter 5 数字；不发明 fallback counts | HLLD/GLM/FP 文献；Chapter 5 matched observations；R0 reference audit | +25 | 每个机制都标为 plausible interpretation，并紧邻能排除的因果边界 | C1 |
| C3 | 把全部关键证据缺口集中为可审查 limitation | Chapter 6，`Limitations` | 加入 density-only、fallback/branch-hit counts 未记录、CPU/GPU warm-up和单机环境、KH temporal缺口；合并已有重复限制 | 不复制 V3 全段；不新增 future-work 清单；不写成辩解 | V3、S1、S2、P1、T1 的最终文本 | -20 | 重要缺口一个不少，且本节净减或不增；不与 Chapter 7 逐句重复 | C2 |
| F1 | 修复图文一致性和可读性 | 仅 Chapter 4 的四张结果图及各自 caption/float 参数；必要时对应已有 plot script | 放大 Brio--Wu panels；OT 保持共同色标并在可由现有数据生成时增加 difference map/切片；KH 增加 color bar 或明确数值 range/levels；修正过小字体和拥挤 legend；全部 scripted、logged、更新 hash/manifest | 不改数据；不生成“好看但不可追溯”图；不让 morphology 支撑 quantitative accuracy | `Figs/README.md`；publication `figure_manifest.json`；各图已记录 source packet | -15（caption 合计） | caption 与每个 panel、色标、变量、grid/time 完全一致；A4 实际尺寸可读；source/hash 可追溯 | V3；不得与正文 agent 并行改同一 Chapter 4 文件 |
| Q1 | 让结论直接回答 brief，又不把 3% diagnostic 写成 adequacy | Chapter 7，`Answers to the research questions` 的 conclusion matrix | 按 C1 的 bounded synthesis 更新四行；RQ3 明称 diagnostic ratio；RQ2 区分 saved-state、timing、unused-thread null control | 不新增证据；不建立跨 metric 总排名；不声称 2D accuracy | C1 最终表述；Chapters 4--6 | -10 | 每个 RQ 有结论+principal boundary；可追溯到正文；“3%”不能独立读成 fp32 足够准确 | C3 → C1/C2 |
| Q2 | 使 future work 与最高价值证据缺口一一对应 | Chapter 7，`Prioritised future work` | 排序为：smooth/external 2D MHD validation；全变量/branch/fallback diagnostics；matched OT/KH MCA；第二机器和明确 warm-up；真实 OpenMP/MPI/reproducible reductions；引用 Ahrens（若 R0 通过） | 不列泛泛愿望；不把 deferred 写成完成；不承诺无法执行的日期 | Chapter 6 limitations；project brief；R0 文献审计 | +10 | 每项含对象、matched controls、metric 和它能关闭的 claim gap；优先级有理由 | Q1 |
| E1 | 删除重复免责声明、模糊论述和 AI 式重复句法 | Abstract、Chapters 1--7、Appendix，按章逐个文件串行 | 仅做等义压缩；合并反复出现的 `bounded/scope/does not establish`，但每个关键 claim boundary 至少保留一次；修复 `sam-ples` 等断词 | 不改数值、公式、表意、引用 key；不跨章节搬 ownership；不消除必要限制 | 完成后的 D--Q 文本；`reportagents.md` | **-120** | 全文无模糊代词指向；结果段遵循 question→evidence→observation→boundary；必要边界仍可独立定位；累计净字数回收 ≥120 | 所有正文任务后 |
| I1 | 交叉一致性与引用 gate | 只修复被检查发现的具体交叉引用、caption、bib/key 错误 | 检查所有数值在正文/表/图注一致；检查 100% cited keys 存在且新增文献实际引用；检查 figure source/hash | 不进行风格性二次重写；不改实验 artefact | `references.bib`、`reference.md`、figure manifests、source summaries | 0 | 无 undefined/unused 新引用；无图文数值冲突；新增引用只支撑审计允许的句子 | E1 |
| I2 | 构建与逐页视觉 gate | 仅修复 LaTeX build、float placement、overfull/underfull、断字和不可读字号问题 | 使用仓库 build script；逐页检查 PDF；最小排版 patch | 不更换数据/内容；不隐藏警告导致的信息；不更新 combined submission 前先冻结 standalone | `scripts/build_report2.ps1`；standalone thesis tree | 0 | clean build；无缺图/undefined ref；Brio、OT、KH、log-zero、temporal 图在实际 PDF 可读；表不越界 | I1 |
| I3 | 字数与 release gate | `planning/drafting_status.md` 和既有 submission checklist 中对应状态行；正文只在超预算时按 E1 规则压缩 | 记录 local count、Overleaf count、最终 PDF hash；确认 standalone 后再替换 combined PDF；提醒签署 declaration | 不伪造 Overleaf 数字/签名；不以 7,875 为目标；不提交 build/transient grids | manuscript outline word lock；submission requirements；最终 PDFs | 0；若超限则继续净减 | local count ≤7,244（6994+250），**Overleaf count ≤7,500**；正式签署材料由学生提供；combined 使用冻结后的 standalone | I2 |

## 4. 依赖波次与并发安排

为避免多个 agent 同时写同一文件，按以下波次执行；括号内可并行，但同一文件
仍需串行：

1. **Wave 0：** `R0`。
2. **Wave 1（开发/方法）：** `D1 → D2 → D3 → D4`；完成后
   `M1 → M2 → M3 → M4`。
3. **Wave 2（验证/结果）：** `V1 → V2 → V3`；再执行
   `S1 → S2 → P1 → T1`。`F1` 在 `V3` 后执行，并与任何 Chapter 4
   正文任务错开。
4. **Wave 3（综合）：** `C1 → C2 → C3 → Q1 → Q2`。
5. **Wave 4（集成）：** `E1 → I1 → I2 → I3`。

跨文件并发最多使用剩余 slots，例如 D 系列完成后可让 Chapter 3、Chapter 4
和 reference/figure provenance 各有一个 agent；绝不并发修改同一 `.tex`。

## 5. 总字数账本

任务 hard ceilings 的理论合计为 **+5 words**（正文/表/图注口径），低于
允许的 +250；`E1` 另要求至少回收 120 words。执行时总控 agent 在每个任务
后更新以下账本，不接受仅凭感觉报告“很短”：

| Gate | 允许累计净增 | 目标 |
|---|---:|---|
| Wave 1 完成 | +115 | 方法补全，但用替换控制增长 |
| Wave 2 完成 | +100 | 结果边界和图注整体不再膨胀 |
| Wave 3 完成 | +125 | synthesis 以表/替换为主 |
| E1 完成 | **≤ +5** | 优先达到净减 |
| 最终 local hard gate | **≤ +250** | local count ≤7,244 |
| 最终正式 gate | — | Overleaf count ≤7,500 |

若任何 wave 超账，先删除重复的 Report 1 背景、结果数字复述和重复
claim-boundary 句；不得先删证据解释、关键 limitation 或 figure-reading prose。

## 6. 完成定义

只有在以下条件全部满足时，本轮审阅修订才算完成：

- 每条审阅意见在矩阵中有 completed 或 evidence-blocked 记录；blocked 项已进入
  limitation/future-work，而没有被包装成结果。
- Project development、Computational results、Conclusions/future work、
  Quality of write-up 四个评分维度均有可定位改动。
- 2D independent validation、全变量 MHD diagnostics、fallback/branch counts、
  GPU warm-up/跨机 timing、KH full MCA/temporal series 等缺口没有被掩盖。
- 所有图、caption、数值、引用和 evidence packet 可追溯且相互一致。
- standalone PDF clean build、逐页可读，并通过最终 Overleaf 7,500-word gate。
