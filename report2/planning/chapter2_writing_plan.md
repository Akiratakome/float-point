# Chapter 2 写作计划与开发证据审计

本计划细化 `manuscript_outline.md` 中 Chapter 2（Project Development:
Ideal-MHD Solver）的写作任务，并以已经成形的 Chapters 3--5 为下游接口。
它是写作与事实核查清单，不是可直接提交的论文正文；最终英文须由学生重写、
核对并统一语气。

## 0. Skill 使用与章节任务

本轮使用 `scientific-writing-duke` 与 `academic-english-style`。前者把开发
材料组织成读者可追踪的因果链：已有问题放在段首，代码组件作为主语，开发
动作使用明确动词，新能力或限制放在句末；后者用于校准证据范围、限定语和
方法学语气。Chapter 2 不应写成提交记录、文件名或功能清单。

本章只回答三个问题：

1. Report 1 的哪些发现或限制改变了 Report 2 的开发方向？
2. 为支持理想 MHD 研究，代码新增了哪些数值组件、执行路径和安全门槛？
3. 为什么这些开发选择在代表性、风险、可比性、运行成本和证据价值之间合理？

| Pass | 任务 | `scientific-writing-duke` 检查 | 禁止事项 |
|---|---|---|---|
| 开发叙事 | 建立 limitation -> decision -> implementation -> gate 顺序 | 每段保持一个主要“角色”；动作由动词承担 | 不写周记、提交史或源码目录清单 |
| 接口检查 | 将实现交给 C3 的设计、C4 的验证和 C5 的结果 | 段末只说明下游用途，不提前报告结果 | 不重复矩阵、指标定义或结果数值 |
| 事实验收 | 逐句对照源码、测试、证据地图和引用 | 已实现用过去时；代码当前行为和图表用现在时 | 不把支持路径写成已验证范围 |

## 1. 章节责任与 900 词结构

建议目标为大纲规定的 **850--920 词**，不得超过 950 词硬上限。表题和图注
计入总字数，因此五节正文宜保持在约 765--815 词。

| Section | 建议正文词数 | 段落数 | 唯一任务 | 下游接口 |
|---|---:|---:|---|---|
| 2.1 Development priorities after Report 1 | 160--170 | 2 | 解释选择逻辑与省略轴 | C1 只作一句引导；C3 列完整矩阵 |
| 2.2 Ideal-MHD and GLM additions | 190--200 | 2 | 说明相对 Euler 路径新增的状态、通量、二维更新与清理 | C4 验证不变性和散度控制 |
| 2.3 HLL and HLLD solver paths | 135--145 | 2 | 解释双路径的开发目的、退化保护和默认值边界 | C5 比较求解器差异与成本 |
| 2.4 CPU, OpenMP, and CUDA implementation | 140--150 | 2 | 描述镜像语义及 GPU 的有界支持范围 | C3 定义设备矩阵；C4/C5 给证据 |
| 2.5 Testing and development gates | 140--150 | 2 | 说明开发何时被视为可进入实验阶段 | C3 定义量化协议；C4 报告通过情况 |
| **正文合计** | **765--815** | **10** | 另留约 65--90 词给过渡、图注和表题 | **章总计约 830--905** |

本章建议只保留一个主视觉：implementation-delta diagram。2.1 的 decision map
若压缩后仍超过约 90 词，移至正文表格；否则写成两段连贯文字，避免两个视觉
项目共同消耗篇幅。

## 2.1 Development priorities after Report 1

### 段落动作

**第 1 段：从 Report 1 基线导出开发方向。** 先用一句话界定已知基线：
Report 1 已在受控 Euler 范围内研究 fp32/fp64、编译语义和匹配 CPU/GPU
输出；理想 MHD 是既定的 Report 2 扩展，而不是由 Report 1 临时决定的方向。
随后只选取能解释后续
决定的发现：严格配置下匹配设备输出未观察到保存状态差异；fast-math 和方法
变化可能改变非平稳状态；fp32/fp64 差异应与离散化或数值参考尺度区分；单一
终态不足以回答差异如何随时间演化。当前 MHD 时间序列由多个预设 `t_end` 的
独立运行组成，不写成原生 checkpoint 输出。

**第 2 段：给出选择准则并解释范围。** 用五个准则组织决策，而不是按开发
日期叙述：代表性物理、数值风险、硬件可比性、可承受运行时间、证据价值。
这些准则导出 Brio--Wu、Orszag--Tang 和 Kelvin--Helmholtz 的 1D/2D MHD
覆盖，HLL/HLLD 双 CPU 路径，以及有界 HLL CUDA 路径。MPI、HLLD-on-GPU、
KH-on-GPU、GPU MCA 和跨机器性能没有形成可隔离且可完成的匹配实现，因此在
此处一次性说明为 deliberate exclusions；C3 只列其方法学后果。

### Report 1 -> Report 2 决策草表

| Report 1 输入 | Report 2 开发决定 | 选择理由 | 正文边界 |
|---|---|---|---|
| 受控 Euler 基线已建立 | 复用 MUSCL--Hancock/配置驱动框架，扩展到理想 MHD | 隔离物理系统扩展，避免重做 Euler 教程 | 不重复 Euler 方程或验证结果 |
| 严格 CPU/GPU 保存状态在覆盖范围内一致 | 为 MHD 建立镜像 CPU/CUDA HLL 路径 | 保留匹配设备比较 | 不暗示普遍硬件独立性 |
| fast-math 与方法变化可影响非平稳输出 | 保留精度、有效编译语义、分支和求解器轴 | 把算法名称之外的实现语义显式化 | 具体矩阵与结果属于 C3/C5 |
| fp32/fp64 差异需要参考尺度 | 先建立 MHD 验证层级和物理状态门槛 | 防止把跨变体差异误称为准确度 | 验证数值属于 C4 |
| 终态不能刻画时间增长 | 增加完成性、检查点和时间序列兼容接口 | 支持固定窗口的差异跟踪 | 拟合方法与负结果属于 C3/C5 |

事实来源：Report 1 Chapter 7 与 evidence map 只提供能导出开发决定的结论；
Report 2 evidence map 确认当前能力边界；architecture convergence design
确认共享应用/完成性接口和 GPU 非目标。

## 2.2 Ideal-MHD and GLM additions

### 第 1 段：状态与通量增量

从 Report 1 的 Euler conserved state 过渡到九分量 GLM--MHD state：密度、
三分量动量、三分量磁场、总能量和清理变量 `psi`。正文只写新增关系：总能量
加入磁能，MHD 通量加入磁压力与张力项，快磁声速进入波速和 CFL 估计。不要
重推有限体积、MUSCL--Hancock 或斜率限制器；用一句交叉引用说明它们沿用
Report 1 框架。

源码事实锚点：`src/mhd/mhd_state.hpp`（九变量、状态转换、压力、快磁声速），
`src/mhd/mhd_flux.hpp`（MHD 通量和 GLM 耦合），以及
`src/mhd/mhd_reconstruct.hpp`（状态重构）。

### 第 2 段：二维更新、GLM 与保护逻辑

以“二维路径复用经旋转的法向问题”为主线：x/y sweeps 使用同一法向通量逻辑，
每步计算清理波速并在双曲更新后衰减 `psi`。说明 GLM 用于输运和衰减离散散度
误差，而不是保证离散 `div(B)` 恒为零。开发风险通过三层保护控制：重构态非物理
时回退到单元态；二阶行/列更新产生非物理候选时整条保守地回退到一阶 HLL；
每步结束后拒绝非有限、非正密度或非正压力状态。

源码与引用锚点：`src/mhd/mhd_solver.cpp`、`src/mhd/glm.hpp` 和
`dedner2002glm`。该引用只支持混合双曲/抛物 GLM 方法，不支持宣称
`glm_cr=0.18` 最优。

### Implementation-delta diagram 设计

```text
Report 1 Euler harness
        |
        +-- 9-variable ideal-MHD state + MHD flux/fast waves
        +-- x/y rotated sweeps + periodic/outflow MHD boundaries
        +-- GLM transport/damping + div(B) diagnostics
        +-- HLL baseline + CPU HLLD analysed path
        +-- CPU/OpenMP + bounded CUDA HLL mirror
        +-- physical-state + completion + regression gates
```

图注必须声明“development delta, not experimental coverage”。图中不要出现周次、
任务编号、提交哈希或结果数值。

## 2.3 HLL and HLLD solver paths

**第 1 段：为何保留 HLL。** HLL 以两波包络提供较简单、较耗散的基线路径，
便于首先验证 MHD/GLM、二维方向复用和 CPU/CUDA 镜像。它是当前 GPU MHD
支持的求解器，也是默认 MHD 路径；“默认”是实现选择，不是准确度或性能排名。

**第 2 段：为何增加但不提升 HLLD。** HLLD 显式恢复接触和 Alfvén/旋转波
结构，使研究可以检验求解器复杂度这一方法轴。项目实现先处理 GLM
`(B_n, psi)` 对，再在退化、非有限或不正的中间状态上回退到同一 GLM 分裂下
的 HLL 通量。HLLD 仍是分析用 CPU 路径；后续验证澄清了 stale-binary
解释，但没有把它提升为 production default 或 GPU 能力。

事实锚点为 `src/mhd/hll.hpp`、`src/mhd/hlld.hpp`、
`miyoshiKusano2005hlld` 和 HLLD divergence follow-up summary。后者只支持
开发问题得到澄清和当前验证边界；C2 不报告其数值。

## 2.4 CPU, OpenMP, and CUDA implementation

**第 1 段：CPU 与 OpenMP build control。** CPU MHD 路径保持配置驱动的
独立可执行入口，并复用共享应用层的配置、输出、诊断和完成性接口。当前提交
版本的 MHD sweeps 没有 OpenMP work-sharing directives；共享构建/运行层只
记录 OpenMP 选择和请求线程数。因此线程轴只能解释为对请求设置的不变性检查，
不能写成 parallel-schedule reproducibility 或 scaling。此处也明确该构建选项
不改变 Riemann 通量或 cfg 默认值。

**第 2 段：有界 CUDA 镜像。** CUDA 路径在设备上镜像 HLL 的边界处理、
x/y sweeps、GLM damping、波速/CFL 计算和 fp32/fp64 模板实例化，再通过统一
dispatch 和 completion gate 返回结果。正文必须把“代码支持”和“证据覆盖”
分开：支持范围是 opt-in HLL；经验证的研究范围仅为匹配 Brio--Wu 与
Orszag--Tang。HLLD、KH、GPU MCA 和通用 GPU 矩阵不在该路径结论范围内。

事实锚点为 `CMakeLists.txt`、`src/mhd_main.cpp`、
`src/gpu/mhd_gpu_solver.{hpp,cu}`、`src/gpu/mhd_kernels.{cuh,cu}`、
`src/app/run_completion.cpp` 和 architecture convergence design。

## 2.5 Testing and development gates

**第 1 段：从单元到实现级门槛。** 按风险层级而不是测试文件顺序叙述：
状态/通量转换与波速测试保护局部代数；HLL/HLLD 和 GLM 测试保护通量与清理
子系统；边界、方向交换和二维不变性测试保护扩维；CPU/GPU round-trip、CFL、
sweep 和案例测试保护设备镜像。只点名代表性门槛，不在正文列测试文件或断言数。

**第 2 段：进入实验管线的条件。** 一次运行只有在达到请求终止时间、步数为正、
最终时间和状态有限、密度与压力为正、所需输出新鲜且 metadata 报告完成时，
才可进入 measure/aggregate/plot。散度均值/最大值、不变性和 CPU/GPU 保存状态
比较是相互独立的门槛，任何一个都不能替代其余门槛。段末把读者交给 Chapter 3
的测量定义和 Chapter 4 的验证结果，不给出通过数值。

测试锚点包括 MHD state/flux/HLL/HLLD、GLM/divB、swap/solver/case、GPU 和
app run-config 单元测试，以及 `src/app/mhd_result.cpp`、
`src/app/run_completion.cpp` 与 `docs/HARNESS.md`。

## 3. 与 Chapters 3--5 的接口锁

| 主题 | C2 可以写 | C2 不写；所有者 |
|---|---|---|
| Report 1 | 能解释一个开发决定的压缩结论 | 完整结果回顾（C1 只作 signpost） |
| 测试案例 | 为什么选择 1D/2D 代表性物理 | 网格、终止时间、边界条件总表（C3） |
| 精度/编译/分支 | 为什么保留这些可控轴 | 构建矩阵和有效语义定义（C3），差异值（C5） |
| GLM/div(B) | 实现结构、诊断存在及其开发目的 | 诊断公式（C3），衰减/分辨率结果（C4） |
| HLL/HLLD | 波结构差异、fallback、默认与支持边界 | 结果/计时排名（C5） |
| CPU/OpenMP/CUDA | 执行路径、镜像语义和能力边界 | 硬件矩阵（C3），相等性与性能值（C4/C5） |
| positivity/completion | 进入实验前必须满足的门槛 | 量化 gate 定义（C3），通过结果（C4） |
| harness | 共享 config -> completion -> metadata 接口的开发意义 | 完整 pipeline 和 retention protocol（C3/Appendix） |

推荐章节过渡：2.5 末句只说明 “Chapter 3 turns these development gates into
the controlled experiment and measurement protocol”。Chapter 3 已经从 research
questions 开始，因此 C2 不需要预告完整实验轴。

## 4. Claim 和术语锁

允许的开发表述包括：项目扩展出 nine-variable GLM--MHD path；CPU 暴露 HLL
和 HLLD，而 opt-in CUDA 只覆盖 HLL；非物理二阶行更新触发 conservative
fallback；完成性和物理状态检查在测量前 gate 运行。学生重写后仍须对照源码。

| 禁止表述 | 原因 | 改写方向 |
|---|---|---|
| “HLLD is more accurate/better than HLL.” | C2 无结果所有权且无通用排名 | 只写 HLLD 恢复更多波结构并作为方法轴 |
| “GLM enforces div(B)=0.” | 项目只输运/衰减离散误差 | 写 divergence control/cleaning diagnostic |
| “The GPU implementation is validated.” | 范围缺失 | 加 HLL、案例、精度和保存状态边界 |
| “OpenMP makes the solver faster.” | C2 无性能证据所有权 | 只写并行化位置；结果交给 C5 |
| “HLL fallback guarantees positivity.” | fallback 后仍需显式状态检查 | 写 protection strategy，不写数学保证 |
| “p24 is fp32.” | 虚拟精度不等于 IEEE binary32 | C2 通常不需提 MCA |

全文不得出现 week、P0/P1、G0/G1、packet、smoke、headline 或本地 build label。
源码路径和内部证据标签只保留在本计划与附录 provenance map。

## 5. 起草顺序与验收清单

1. 先完成 2.2 和 2.3，锁定数值组件与 solver 边界。
2. 写 2.4，明确 CPU/OpenMP/CUDA 的能力与证据范围。
3. 写 2.5，把代码保护转化为开发验收逻辑。
4. 最后写 2.1，使选择理由准确指向实际交付，而不是早期计划。
5. 加 implementation-delta diagram，再压缩重复解释。

- [ ] 每个 Report 1 句子都导出一个 Report 2 决定。
- [ ] 理想 MHD 只写相对 Euler 的新增量，不重写 Report 1 方法章。
- [ ] 九变量 state、磁能、快磁声速、二维方向复用和 GLM 描述与源码一致。
- [ ] 不把 `glm_cr=0.18` 写成文献最优值。
- [ ] HLLD 的 GLM split、退化 HLL fallback 和 CPU-only 研究边界准确。
- [ ] HLL 是 GPU MHD 的唯一支持 solver；未暗示 HLLD/KH/GPU-MCA 覆盖。
- [ ] OpenMP 被准确写成 build/thread metadata control，没有暗示 MHD sweep
      已并行化、获得 scaling，或覆盖 parallel schedule ordering。
- [ ] CUDA 描述没有改变或暗示改变现有 cfg 默认值与输出格式。
- [ ] physical-state、completion 和 evidence gates 没有互相替代。
- [ ] 没有实验矩阵、指标公式、结果数值或性能排名侵入 C2。
- [ ] 每段首句给出已知问题或组件，段末承载新决定或明确边界。
- [ ] 主语是 solver、path、gate 或 project，而不是抽象的 “investigation”。
- [ ] 图在正文中被点名、解释并绑定到“implementation delta”这一条 claim。
- [ ] 学生已重写英文并单独执行 `avoiding-ai-flavor` 验收。

## 6. 完成定义

本计划已使 Chapter 2 进入 `evidence-locked`：源码审计覆盖 state/flux、GLM、
HLL/HLLD、CPU/OpenMP/CUDA 和 completion；diagram 每个节点已有代码或测试
锚点；C3--C5 接口没有重复结果或冲突术语；引用不为项目特定参数或排名背书。

进入 `author-rewrite` 前，学生还需确认 Report 1 -> Report 2 决策表，将本计划
转成不超过 950 词的英文正文、完成交叉引用，并按独立 Overleaf 计数记录本章
实际字数。
