# 执行计划 — Cross-Architecture LLM Inference Qualification Harness

> *Execution plan for workload family 2 (LLM inference). Written in Chinese because it is a
> working/interview-prep document; the outward-facing docs (`README.md`, `docs/INDEX.md`,
> `docs/HARNESS.md`) stay in English.*
>
> 决策依据见 [`ADR.md`](ADR.md)。仓库总览见 [`../INDEX.md`](../INDEX.md)。
> 状态：**已通过设计评审（2026-08-24）**，可从步骤 0 开工。

---

## 1. Context

**为什么做这件事。** 现有仓库是一套成熟的数值实验基础设施（1,065 份 provenance 完整的运行记录、
85 个聚合证据包、schema 化的 run-record 与 experiment-manifest、五态生命周期、SHA-256 产物清单），
其最强单点结论是：**匹配的 CPU/GPU 输出只有在关闭 nvcc multiply-add 合并时才位级一致；恢复编译器
默认值造成的位移，比把工作精度砍半还大**。这说明"可复现"是构建配置的属性，不是硬件的属性。

**问题是市场覆盖面。** 对 36 份 AI Infra JD 的调研显示：CUDA 约 19 次、PyTorch 约 13 次、推理引擎
（vLLM/SGLang/TRT-LLM）约 12 次、profiling 约 9 次、算子/kernel 约 9 次、Triton/编译器约 8 次、
量化约 6 次、集合通信约 6 次；而 `numerics / regression detection` **只出现 1 次**。现有项目在最后
一项上近乎完美匹配，在前面几项上是空白。**本计划补全前者，同时把后者做成别人复制不了的差异点。**

**预期结果。** 一个双负载族（LLM 推理 + HRSC 求解器）的 qualification 平台，对外主张是一个可证伪
的不变量：*在 {硬件 × 后端 × 精度 × 批大小 × 并行度} 空间里，LLM 推理输出在哪些条件下位级可复现、
破坏它的机制是什么、恢复它的代价是多少* —— 并在两个完全不同的负载上用同一套方法验证。

---

## 2. 硬件事实（已核实，决定全部实验设计）

### 2.1 三个执行平面

| | 本地 RTX 5070 Laptop | A30（lovelace，直连非 Slurm） | RTX 5090（`csc-mphil-gpu`） |
|---|---|---|---|
| 架构 / CC | Blackwell `sm_120`，消费级 | Ampere `sm_80`，数据中心 | Blackwell `sm_120`，消费级 |
| 显存 / 带宽 | **8,151 MiB**，驱动 591.91 | 24 GB HBM2 / **933 GB/s** | 32 GB GDDR7 / **1792 GB/s** |
| FP8 | 支持 | **不支持** | 支持（5th-gen TC） |
| 数量 | 1 张 | 2 张（共享机，`nice -19`） | 2 张/节点，**≤2 GPU、6h、非独占** |
| 角色 | 开发与 spike（**仅 0.5B**） | 匹配比较基准 | 主实验平面 |

**带宽比 1792/933 = 1.92×** 是所有 decode 性能结论的上界锚点。

### 2.2 本地环境（决定步骤 0–3 的可行性）

- WSL2 Ubuntu 存在，内核 `6.18.33.1-microsoft-standard-WSL2`，**GPU 直通可用**（WSL 内 `nvidia-smi`
  能看到 RTX 5070 Laptop / 8,151 MiB）。
- WSL 内 **Python 3.14.4** —— PyTorch/vLLM 装不上，必须另建 3.12 环境。
- WSL 内**没有 nvcc**；WSL 可见 RAM 15 GB。
- Docker 29.5.3 可用（现已用于 Verificarlo）。

**直接后果：本地装不下 7B（fp16 权重约 14 GB > 8 GB）。** 因此模型分两层，见 ADR-12。

### 2.3 集群

| Plane | Host | Spec | Limits |
|---|---|---|---|
| 控制面 | `athena` | Xeon E5-2430 v2, 6 核, 32 GB | 仅提交/聚合 |
| CPU | `csc-mphil` = phy-cerberus4/5/6 | Xeon Gold 5418Y, 48 核, 248 GB | 48 核, **6 h** |
| GPU | `csc-mphil-gpu` = phy-thetis / phy-damysus | 2 × RTX 5090 32 GB, 32 核, 128 GB | **≤2 GPU**, **6 h** |
| Ampere | `lovelace` | Xeon Silver 4314, 32 核, 257 GB, 2 × A30 | 直连共享机 |

- 提交用 `--clusters=CSC`，GPU 用 `--gpus=N`；官方样板 `/lsc/opt/slurm/slurm_gpu.sh`。
- **节点非独占**（≤4 作业/节点）→ 任何计时数字必须带共租户证据（ADR-10）。
- 工具链：GCC 13.2/14.2/15.2、Clang 18.1、CUDA 12.5/12.6/12.9/13.1、OpenMPI 4.1.6、Python 3.12.3。
- `/local/data` 为节点本地 scratch，**不备份、无公布配额**。
- 跨节点 GPU **文档未说明**，只能实测；跨节点 CPU MPI 文档明确可行。

### 2.4 分布式可达上限

**同时可用 2 张 GPU**（官方 per-job 硬上限）。集群唯一 4 卡机器 `hex` 是 Kepler `sm_35`，
CUDA 12.0 已移除其全部库支持，实际不可用。因此：

- **可做**：NCCL 集合通信实测、TP=2、PP 2 段、DP=2、ZeRO 分片、通信/计算重叠、
  A30 vs 5090 互联对照、CPU 多节点 MPI。
- **不可做**（必须标为未覆盖）：多节点 GPU、RDMA/InfiniBand、扩展性曲线、分布式训练框架。

---

## 3. 执行顺序（"随时可交付"，不设日历预算）

每一步都是独立可交付的资产；任意时点中断都留下完整成果。见 ADR-15。

| # | 步骤 | 平面 | 依赖 | 门槛 |
|---|---|---|---|---|
| **0** | **Spike：现象是否存在** | 本地容器 · 0.5B | — | L0/L1/L2，见 §4 |
| **1** | **P0 harness 加性泛化** | 本地 · 纯 CPU | — | 旧 matrix 命令**逐字相同**；465 测试保持全绿 |
| **2** | **根 README + 数值回归 CI** | 本地 | 1 | CI 能对注入的已知回归报警，假阳性 0 |
| **3** | **P1a 确定性 + 噪声地板** | 本地 · 0.5B | 0,1 | 破坏矩阵初版；地板先于任何跨配置判定 |
| — | *集群探针（你执行）* | 集群 | — | 见 §5 |
| **4** | P1b 引擎接入与服务化 | 集群 · 7B | 探针 | vLLM logits 与 eager 可对齐 |
| **5** | P1c 精度轴与 FP8 能力门 | 集群 | 4 | A30 的 FP8 格产出结构化 `unsupported_capability` |
| **6** | P2b Profiling 与 roofline（E1） | 集群 | 4 | 实测比 vs 1.92× 的偏离有机制归因 |
| **7** | P2a batch-invariant 算子 | 本地开发 + 集群测量 | 3 | 先正确后性能；ULP 差有界 |
| **8** | P2d TP=2 与 NCCL | 集群 | 4 | 互联类型与 NCCL 算法被记录而非假设 |
| **9** | P2e MPI 归约顺序 | 集群 CPU | 1 | 默认单进程路径逐字不变 |
| **10** | P3 余下对外资产 | — | 全部 | Artifact Description + 上游小 PR |

**步骤 0 与 1 现在就能开工，且都不依赖任何未验证的东西。**

---

## 4. 步骤 0 — Spike（差异化的生死判定）

计划的核心交付物是"破坏矩阵"，其门槛是"至少一个变量能稳定复现唯一输出数从 1 变 k"。
**这是经验假设，不是已知事实**：Thinking Machines 的结论来自特定模型与特定 vLLM 版本且是博客；
vLLM/SGLang 近一年一直在往 batch-invariance 方向修；小模型 + 短输出对唯一输出数不敏感。
因此在投入平台建设之前先用一天验证它。

**配置**：本地 WSL 容器 · `Qwen2.5-0.5B-Instruct`（pin revision）· greedy 解码 · 固定 prompt ·
输出长度取足够长以规避 ADR-8 记录的短输出不敏感问题 · 重复 50 次 · batch size ∈ {1, 8, 32}。

**判据（跑之前写死，不得事后调整）**

| 级别 | 判据 | 含义 |
|---|---|---|
| **L0** | 同配置重复 50 次 = **恰好 1 个**唯一输出 | 对照组成立，测量本身可信 |
| **L1** | **只改 batch size** 后唯一输出数 > 1 | 现象存在，headline 成立 |
| **L2** | L1 在 **3 次独立会话**中可复现 | 现象稳定，可作为矩阵基础 |

**三种结局的预案（都不是失败）**

- **L0 不通过**（同配置重复本身就不确定）→ 这是更强的结果。headline 改写成"连同配置重复都不可
  复现，恢复到 L0 需要付出 X"。
- **L1 不通过** → 降级到跨架构确定性（不同 kernel、不同归约顺序，几乎必然存在），但**必须等集群
  探针通过后才能验**。
- **L2 不通过**（时灵时不灵）→ 现象存在但不稳定，本身就是结论；矩阵改报"复现率"而非二值。

**任何一种情况我都会带数据回来重定 headline，不会自行改了继续跑。**

---

## 5. 集群探针（由你执行，产出为第一个证据包）

两个可执行脚本，输出结构化 JSON 到 `experiments/aiinfra/probe/`，走现有 manifest 校验。

**A. Slurm GPU 探针**（`scripts/cluster/aiinfra/probe_gpu.slurm`，约 2 分钟）
照抄官方 `/lsc/opt/slurm/slurm_gpu.sh` 头部，`--gpus=2`，采集：
`nvidia-smi -L` · `nvidia-smi topo -m` · `deviceQuery` · `bandwidthTest` · NCCL 版本 ·
`SLURM_JOB_*` · 有效 hostname · `CUDA_VISIBLE_DEVICES` · GPU UUID · 共租户进程快照 ·
以及一个 `--nodes=2 --gpus-per-node=1` 的最小跨节点尝试（**失败本身就是要记录的环境事实**）。

**B. lovelace 探针**（`scripts/cluster/aiinfra/probe_lovelace.sh`）
`groups`（判定是否在 LSC 组 → 是否解锁 A4000 第三代架构）· `nvidia-smi -L` · `topo -m` ·
`/local/data` 可写性与剩余空间 · 能否拉起选定的容器镜像。

**同时验证**：选定的容器 digest 能否在 `sm_120`（5090）与 `sm_80`（A30）上都跑通 —— 这是 ADR-13
的前提，也是探针最重要的一项。

---

## 6. 阶段细节

### 步骤 1 — P0 加性泛化

**目标**：让现有 harness 能跑非 HRSC 负载，且现有 HRSC 路径逐字不变。

**关键文件**
- 修改 `scripts/run_matrix.py`：`normalise_run` 增加可选 `arguments` 数组，插在 `binary` 与生成的
  config 之间
- 修改 `scripts/harness/contracts.py`：`RunSpec` 增加 `artifact_kind`；`FailureCategory` 增加
  `RESOURCE_EXHAUSTED`
- 修改 `scripts/harness/runner.py`：`parse_run_status` 加性支持
  `kind=workload completed=<n> expected=<n>`，旧的 `final_time/target_time/steps` 契约不变
- 修改 `scripts/harness/artifacts.py`：新增 `workload_result` JSON 校验器，走现有
  `get_artifact_validator` 分派
- 新增 `scripts/aiinfra/{config.py,result_schema.py,environment.py,prepare_assets.py,backends/{base.py,fake.py}}`
- 新增 `configs/aiinfra/models.json`
- 测试：`tests/py/test_harness_runner.py`、`test_harness_scripts.py`（回归）+ 新增
  `tests/py/test_aiinfra_{harness_contract,config,result_schema,environment}.py`

**复用**：`contracts.RequiredArtifact` 新鲜度校验、`runner.execute_run`、`runner.git_provenance`、
`metadata.serialise_record`、`config.materialise_config`。

**Gate**
1. 全部现有测试绿（465 passed），且不带 `arguments` 的旧 matrix 构造出**逐字相同**的命令；
2. fake 负载能跑通、产出通过校验的新鲜 JSON、拿到 `completion.reported=true`；
3. 未知 `artifact_kind` fail-closed；
4. OOM → `resource_exhausted`，能力拒绝 → `unsupported_capability`，二者都进聚合而不是消失。

### 步骤 2 — 根 README + CI

- 根 `README.md`（仓库目前没有）：一图 + 2–3 个归一化数字 + 三个链接，零形容词；一段说清两个
  负载族的关系。
- `.github/workflows/`：数值回归门禁 —— 读 `precexp_aggregate.py` 输出的显著位数，与存档 baseline
  比较，退化超阈值即 fail。算例为 1D Brio–Wu，n=10。

### 步骤 3 — P1a 确定性与保真度

- 新增 `scripts/aiinfra/{determinism.py,fidelity.py,noise_floor.py}`、
  `backends/{torch_eager.py,vllm_offline.py}`
- **复用（不要重写）**：ULP 计算复用 `scripts/regression/mhd_gpu_fma_axis.py:55` 的符号调整单调
  整数映射，提取为共享工具；噪声地板复用 `scripts/metrics/compute_noise_floor.py` 的判据结构；
  计时协议复用 `experiments/week18/kh_solver_timing` 的 warm-up + repeats + median/IQR 形态。
- **E3 破坏矩阵**：逐个扫 batch size / 并发度 / backend / attention backend / TP / 硬件，
  每格报唯一输出数与相对基线的延迟代价 %。
- **E4 保真度与地板**：先测同硬件同配置重复的 logits 差分布作为地板，再判定跨配置差异是否超出地板。

### 步骤 4–6 — 引擎、精度、性能

- **P1b**：vLLM 离线与在线，TTFT/TPOT/ITL 的 p50/p95/p99，KV cache 与 continuous batching。
- **P1c / E2**：{fp32-TF32关, fp32-TF32开, fp16, bf16, fp8(仅5090), W8A8 或 AWQ 择一} × {A30, 5090}。
  **必须记录有效路径而非请求路径** —— 验证 sm_120 上确实走了 FP8 kernel 而非静默回退。
- **P2b / E1**：decode token/s 的 A30↔5090 实测比 vs 带宽比 1.92×，偏离部分用 achieved bandwidth
  归因；prefill 单独分类为计算受限。采集与计时**必须分开跑**并在 metadata 标记。

### 步骤 7 — P2a 算子

`src/ai_kernels/batch_invariant/`（Triton 版 + C++/CUDA 版），接进一个真实 Transformer block；
报正确性（与 eager 的最大 ULP 差有界）、batch 不变性成立、以及吞吐代价。
**注意**：WSL 内没有 nvcc，CUDA 版需先在 WSL 装 CUDA toolkit，或改在集群编译。

### 步骤 8 — P2d TP=2 与 NCCL

`scripts/cluster/aiinfra/run_gpu_workload.slurm`。NCCL 微基准（allreduce/allgather/reduce-scatter
的消息尺寸扫描）+ TP ∈ {1,2} × {A30, 5090} 端到端 + 互联归因（`topo -m`、`NCCL_DEBUG=INFO`）。
**负结果是有效交付物**：5090 无 NVLink，TP=2 在 7B 上很可能无收益甚至负收益，按"通信开销超过
并行收益的临界模型尺寸"表述。

### 步骤 9 — P2e MPI 归约顺序（已批准，严格加性）

给 HRSC 加编译期可选的 MPI 域分解与归约。固定物理配置，只变进程数与归约顺序
（树形 / 线性 / `MPI_Allreduce` 默认），测 ULP 差与 wall time。
**默认单进程路径必须逐字不变**，现有全部证据包不受影响。

### 步骤 10 — P3 余下

`docs/ARTIFACT_DESCRIPTION.md`（SC AD/AE 模板 A.1–A.7）+ 上游小 PR 一个。

---

## 7. 集群作业约束（贯穿步骤 4–9）

- 6h 上限 → 长矩阵拆成 Slurm array，直接复用 `scripts/cluster/report2_w16_w17_slurm/` 的形态
  （Week 16/17 已用同一方法绕过同一限制）。
- 每次运行记录 `SLURM_JOB_*`、有效 hostname、`CUDA_VISIBLE_DEVICES`、GPU UUID、共租户进程快照、
  时钟/温度/功率状态。
- lovelace 是直连共享机：`nice -19`、先查占用、pin `CUDA_VISIBLE_DEVICES`、污染运行标记 non-headline。
- 模型缓存与原始结果放执行节点 `/local/data`；athena 仅做提交与聚合。
- 模型下载与环境搭建**不计入任何 headline 计时**；冷启动/加载时间单独记录。

---

## 8. 验证方式

```bash
# 1. 回归：现有 HRSC 路径未被破坏（步骤 1 的硬门槛）
python -m pytest tests/py -q          # 期望 465 passed, 23 skipped
./build-double/unit_tests -r compact

# 2. 加性泛化：假负载走通新路径
python scripts/run_matrix.py configs/aiinfra/smoke/fake_workload.json

# 3. 环境探针（只读，不装包不下载）
python scripts/aiinfra/environment.py --json

# 4. 确定性冒烟（本地 0.5B）
python scripts/aiinfra/determinism.py --config configs/aiinfra/smoke/determinism.json

# 5. 实验清单审计
python scripts/audit_experiments.py --format markdown
```

**端到端判据**：`experiments/aiinfra/` 下每个证据包都能通过
`scripts/harness/experiment_manifest.py` 校验，且带 lifecycle 状态、`claim_boundary`、
SHA-256 产物清单。

---

## 9. 风险与不可夸大的边界

| 风险 | 缓解 |
|---|---|
| **headline 现象可能不存在** | 步骤 0 spike 前置，判据先写死，三种结局都有预案 |
| **`csc-mphil-gpu` 权限未验证** | 步骤 0–3 全部不依赖它；探针失败则重评估步骤 4 以后 |
| **软件栈污染跨架构结论**（sm_120 与 sm_80 若用不同栈） | 一个容器 digest 打通三张卡；打不通则把软件栈记为显式实验轴（ADR-13） |
| **节点非独占污染计时** | 预先声明的剔除策略 + 共租户快照 + quiet-node 重试 |
| FP8 静默回退到 BF16 | 记录有效 kernel 路径而非请求 dtype；不可验证就标 `unsupported` |
| 5090 无 NVLink 致 TP=2 负收益 | 预期结果，作为互联归因结论交付 |
| 范围蔓延 | 步骤 0–3 是核心；步骤 4 以后各自独立可丢 |

**绝不能说的话**：分布式训练经验（无 Megatron/DeepSpeed/FSDP、无多节点 GPU）；把 TP=2 说成分布式
训练；生产流量/线上稳定性；Kubernetes/Go/国产芯片；把 A30 与 5090 的差异全部归因于架构代差
（**数据中心 vs 消费级是混杂因子，必须声明**）。

**仍未覆盖的 JD 关键词**：训练侧分布式框架、多节点 GPU、RDMA/InfiniBand、扩展性曲线（>2 卡）、
K8s、Go、国产芯片/CANN、生产流量。

**可诚实主张的分布式范围**：intra-node 2-GPU tensor parallelism、NCCL 集合通信实测与互联归因、
CPU 多节点 MPI 归约顺序对数值结果的影响。

---

## 10. 待确认

**由集群探针回答（阻塞步骤 4 以后）**

1. `csc-mphil-gpu` 是否确实可用（仓库有模板脚本但无证据包）。
2. 是否在 **LSC 组** → 是否解锁 philonis/atalanta/melete 的 2 × A4000 16 GB（`sm_86`），
   把架构轴从 2 代扩到 3 代。
3. lovelace 的 A30 是否有 NVLink bridge；5090 两卡是否同 PCIe root。
4. GPU 分区能否跨节点。
5. Slurm `--account=` 的实际取值（官方示例写的是管理员的 `pmb39`）。
6. lovelace / GPU 节点能否拉起选定的容器镜像。
7. `/local/data` 配额。

**已决（2026-08-24）**

- 不租用云 GPU（ADR-11）。
- 分布式止于 intra-node 2 GPU + CPU 多节点 MPI。
- P2e 修改 HRSC 求解器已批准，须严格加性。
- 不设日历预算，改"随时可交付"顺序（ADR-15）。
- 旧 MSc 周期的文档与手稿目录属历史，不恢复、不引用。
