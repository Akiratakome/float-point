# 本地可执行核心（步骤 0–3）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax
> for tracking.
>
> *这份计划是内部工作文档，与 `PLAN.md` / `ADR.md` 同为中文；代码、测试、提交信息、对外文档一律英文。*

**Goal（一句话）**：把 `docs/aiinfra/PLAN.md` 里**不依赖集群、不依赖未验证权限**的步骤 0–3
落成可执行、可测试、可交付的代码与证据，且现有 HRSC 路径逐字不变。

**Architecture**：三层加性改造。第一层在 `scripts/harness/` 与 `scripts/run_matrix.py` 上做**纯加性**
扩展（新增可选字段与新的 artifact/status 契约，旧路径默认值不变）；第二层在 `scripts/aiinfra/` 下
新建一个后端可插拔的 LLM 负载适配层，先用**不依赖 torch 的 fake 后端**打通全部管线；第三层才引入
真实模型（本地 0.5B），跑确定性/保真度/噪声地板测量并产出证据包。CI 与根 README 夹在第一层与第三层
之间，保证"任意时点中断都留下完整成果"。

**Tech Stack**：Python 3.12（Windows 主机，pytest）· Python 3.12（WSL2 Ubuntu，PyTorch/vLLM）·
numpy · CMake/Ninja（仅回归验证，不新增 C++）· Docker（容器 digest 固定软件栈）· GitHub Actions。

**Spec**：[`../PLAN.md`](../PLAN.md)（步骤 0–3、§4 spike 判据、§8 验证方式），
决策依据 [`../ADR.md`](../ADR.md)（ADR-8/9/12/13/14/15）。

---

## Global Constraints（每个任务的隐含要求）

从 spec 与仓库现状逐字抄录，**不得违反**：

1. **HRSC 路径逐字不变。** 不带新字段的旧 matrix 必须构造出**逐字相同**的命令、逐字相同的
   `config.cfg`、逐字相同的 metadata 字段集合。（`PLAN.md` 步骤 1 Gate 1；`AGENTS.md`：
   "Do not change solver numerics or existing cfg defaults"）
2. **测试基线（本工作树实测 2026-08-24）**：`python -m pytest tests/py -q` →
   **`463 passed, 25 skipped`**。25 个 skip 全部由"缺二进制/缺 `skimage`"导致，与本计划无关。
   任务门槛用"**passed 只增不减、skipped 数量不变**"表述，不写死 465。
   （spec 里的 "465 passed, 23 skipped" 是在装了 `scikit-image` 的机器上记录的，见本计划 §Review R-2。）
3. **不改 solver 数值、不改任何现有 `.cfg` 默认值、不新增 C++ 文件。** 步骤 0–3 完全是 Python 与文档。
4. **`experiments/` 整体被 `.gitignore` 忽略**（`.gitignore:24`）。新证据包里要提交的文件必须
   `git add -f` 显式强制加入，且只加 summary/manifest/figures/metadata，不加 `*.bin` 与模型权重。
5. **失败必须结构化，不得消失。** 能力缺失 → `unsupported_capability`；显存耗尽 →
   `resource_exhausted`；二者都要进 metadata 与聚合。（`PLAN.md` 步骤 1 Gate 4；ADR-6）
6. **spike 判据（L0/L1/L2）在跑之前写死，跑完不得调整。**（ADR-14；`PLAN.md` §4）
7. **噪声地板先于任何跨配置判定。** 没有同配置重复地板，不得声称任何跨配置差异是"差异"。（ADR-9）
8. **模型固定 revision**：`Qwen/Qwen2.5-0.5B-Instruct`，pin 到一个 commit revision，写进每条 run record。（ADR-12）
9. **软件栈固定**：一个容器 image digest 写进每条 run record；本地打不通就把软件栈记成显式轴，
   **不假装是同一个栈**。（ADR-13）
10. **模型下载、环境搭建、冷启动不计入任何 headline 计时**，单独记录。（`PLAN.md` §7）
11. **对外文档（根 `README.md`、`docs/INDEX.md`、`docs/HARNESS.md`）用英文**；本目录下的
    计划/ADR 用中文。（`PLAN.md` 抬头）
12. **不得链接 `docs/superpowers/`、`docs/weekN/`、`report1/`、`report2/`** —— 这些已被判定为历史，
    不在工作树内。（`docs/INDEX.md` §9）

---

## 范围：为什么是这四步

`PLAN.md` §3 的十一步里，只有下面四步**完全不依赖集群探针**，也不依赖 8 GB 显存装不下的 7B：

| spec 步骤 | 本计划任务 | 本地可行性依据 |
|---|---|---|
| **1** P0 harness 加性泛化 | Task 1–8 | 纯 CPU、纯 Python，零外部依赖 |
| **2** 根 README + 数值回归 CI | Task 9–11 | 纯文档 + GitHub Actions |
| **0** Spike：现象是否存在 | Task 12–14 | WSL2 GPU 直通已验证；0.5B fp16 ≈ 1 GB ≪ 8,151 MiB |
| **3** P1a 确定性 + 噪声地板 | Task 15–19 | 同上；只跑 0.5B |

**明确不在本计划内**（依赖集群或未验证权限）：步骤 4–6、8–10 全部；步骤 7 的 CUDA/Triton 算子
（WSL 内无 nvcc，见 `PLAN.md` §2.2）；E1 带宽比、E2 精度轴的 FP8 格、TP=2、NCCL。

**执行顺序与 spec 的差异（一处，已在 §Review R-1 论证）**：本计划把 Task 12（WSL 环境与模型下载，
纯等待、~1–3 h 墙钟）提前到与 Task 1–8 并行启动，spike 本身（Task 13–14）仍然在建平台之前完成。
ADR-14 要保护的是"不要在现象未验证前投入平台建设"，而 Task 1–8 在 spike 的三种结局下**都需要**
（三种结局改的是 headline 文案，不是 harness），所以让下载在后台跑不违反 ADR-14 的意图。

---

## File Structure

**修改（全部加性，默认值保证旧行为）**

| 文件 | 责任 | 本计划的改动 | Task |
|---|---|---|---|
| `scripts/run_matrix.py` | matrix → 命令 → metadata | `MatrixRun` 增 `arguments` / `config_filename` / `artifact_kind` | 1, 2, 3 |
| `scripts/harness/contracts.py` | 失败分类、RunSpec | `FailureCategory` 增 `RESOURCE_EXHAUSTED` | 5 |
| `scripts/harness/artifacts.py` | 产物校验分派 | 新增 `workload_result` 校验器 | 4 |
| `scripts/harness/runner.py` | 执行与 run-status 解析 | `parse_run_status` 支持 `kind=workload`；`reason` 收紧为枚举 | 5 |
| `scripts/harness/experiment_manifest.py` | 证据包清单校验 | `report` 由字面量 `"report2"` 放宽为集合 | 9 |
| `scripts/regression/mhd_gpu_fma_axis.py` | GPU FMA 轴驱动 | 改为从共享模块 import `ulp_max`，行为不变 | 18 |
| `docs/HARNESS.md` | 管线与运行契约 | 记录三个新可选字段与 workload status 行 | 10 |
| `scripts/README.md` | 脚本归属 | Canonical Entry Points 增两行 | 10 |
| `docs/INDEX.md` | 仓库总览 | §7 状态更新 + 指向本计划 | 10, 21 |
| `docs/aiinfra/PLAN.md` | spec 本身 | §3 表格加"状态 / 证据包"列 | 21 |
| `.gitignore` / `pytest.ini` | 工作树卫生 | 提交待提交改动，把 `pytest.ini` 纳入版本控制 | 0 |

**新增**

| 文件 | 责任 | Task |
|---|---|---|
| `scripts/metrics/ulp.py` | 符号调整单调整数映射的 ULP 距离（从 `mhd_gpu_fma_axis.py:55` 提取） | 18 |
| `scripts/aiinfra/__init__.py` | 包标记 | 4 |
| `scripts/aiinfra/config.py` | 负载配置 JSON 的加载与 fail-closed 校验 | 6 |
| `scripts/aiinfra/result_schema.py` | `aiinfra.workload-result` 的构造与校验（单一真相） | 4 |
| `scripts/aiinfra/environment.py` | 只读环境探针（不装包、不下载） | 6 |
| `scripts/aiinfra/prepare_assets.py` | 按 pin 下载模型，不做任何计算 | 14 |
| `scripts/aiinfra/run_workload.py` | matrix 调用的负载入口：配置 → 后端 → 结果 JSON + run-status | 8 |
| `scripts/aiinfra/backends/__init__.py` | 包标记 | 7 |
| `scripts/aiinfra/backends/base.py` | 后端接口、`WorkloadFailure`、注册表 | 7, 19 |
| `scripts/aiinfra/backends/fake.py` | 无 torch 依赖的确定性假后端（含 OOM / 能力拒绝注入） | 7, 19 |
| `scripts/aiinfra/backends/torch_eager.py` | PyTorch eager 后端（黄金参考，唯一有完整 logits 的路径） | 15, 19 |
| `scripts/aiinfra/backends/vllm_offline.py` | vLLM 离线后端 | 15, 19 |
| `scripts/aiinfra/determinism.py` | warm-up + 重复 N 次 → 唯一输出数 + 复现率；CLI | 7, 20 |
| `scripts/aiinfra/fidelity.py` | logits 差：ULP / L∞ / L2 / KL | 19 |
| `scripts/aiinfra/noise_floor.py` | 同配置重复的地板与"是否超出地板"判定 | 19 |
| `scripts/aiinfra/spike_evaluate.py` | 只**应用**已注册判据，自己不定义任何阈值 | 16 |
| `scripts/aiinfra/spike_run.py` | 跑一次 spike 会话并落盘判定 | 17 |
| `scripts/aiinfra/breakage_matrix.py` | 破坏矩阵驱动：失败格子记录下来并继续 | 20 |
| `scripts/regression/ci_numerical_gate.py` | 两层数值回归门禁（位级重复 + 跨机器容差） | 13 |
| `configs/aiinfra/models.json` | 模型 pin（id、revision、source、大小） | 6, 14 |
| `configs/aiinfra/smoke/fake_workload.json` | run_matrix 矩阵文件（假负载冒烟） | 8 |
| `configs/aiinfra/smoke/fake_workload_run.json` | 假负载自身的配置 | 8 |
| `configs/aiinfra/smoke/determinism.json` | 确定性冒烟配置（spec §8 第 4 条命令） | 20 |
| `configs/aiinfra/spike/spike_criteria.json` | **跑之前写死**的 L0/L1/L2 判据 | 16 |
| `configs/aiinfra/spike/spike_l0.json` · `spike_l1.json` | spike 的 eager / vLLM 两份负载配置 | 16 |
| `configs/aiinfra/p1a/breakage_matrix_local.json` | 本地破坏矩阵的格子定义 | 20 |
| `tests/cases/brio_wu_1d/brio_wu_n10.cfg` | CI 数值门禁的 canary 算例 | 13 |
| `README.md`（仓库根） | 对外入口（英文） | 11 |
| `docs/aiinfra/ENVIRONMENT.md` | 本地执行环境实况（装成了什么、没装成什么） | 14 |
| `docs/aiinfra/SPIKE_RESULT.md` | spike 结论一页纸（对外可引用） | 17 |
| `.github/workflows/tests.yml` | pytest CI | 12 |
| `.github/workflows/numerical-regression.yml` | 数值回归门禁 + 手动 Verificarlo 作业 | 13 |
| `tests/py/test_aiinfra_harness_contract.py` | Task 1–3、5、8 的契约测试 | 1, 2, 3, 5, 8 |
| `tests/py/test_aiinfra_result_schema.py` | 结果 schema | 4 |
| `tests/py/test_aiinfra_config.py` | 配置加载与 fail-closed | 6 |
| `tests/py/test_aiinfra_environment.py` | 环境探针在缺依赖时不崩 | 6 |
| `tests/py/test_aiinfra_determinism.py` | 确定性统计（用 fake 后端） | 7 |
| `tests/py/test_aiinfra_backends_capability.py` | 缺依赖时给出结构化失败而非 ImportError | 15 |
| `tests/py/test_aiinfra_spike_criteria.py` | 已注册判据与 L0/L1/L2 判定逻辑 | 16 |
| `tests/py/test_aiinfra_noise_floor.py` | 地板与超限判定 | 19 |
| `tests/py/test_aiinfra_breakage_matrix.py` | 失败格子被记录且矩阵继续 | 20 |
| `tests/py/test_ulp_shared.py` | 提取后的 ULP 工具 | 18 |
| `tests/py/test_ci_numerical_gate.py` | 数值门禁的两层判据 | 13 |
| `tests/py/test_root_readme.py` | 根 README 的链接与数字有据可查 | 11 |
| `experiments/aiinfra/ci_baseline/` | CI 数值门禁的参考剖面（`git add -f`） | 13 |
| `experiments/aiinfra/env_probe_local/` | 环境证据包（`git add -f`） | 14 |
| `experiments/aiinfra/spike_determinism_0p5b/` | 步骤 0 证据包（`git add -f`） | 17 |
| `experiments/aiinfra/p1a_breakage_matrix_local/` | 步骤 3 证据包（`git add -f`） | 20 |

---

## 阶段 A — 基线卫生（必须先做）

### Task 0: 把工作树归零并锁定基线

**为什么必须先做**：`scripts/harness/runner.py:git_provenance` 把
`git status --porcelain --untracked-files=no` 的结果写进**每一条** run record 的
`provenance.git.dirty`。当前工作树有 **346 个未提交改动 / 96,478 行删除**，
`pytest.ini` 还是未跟踪状态。在这个状态下产出的任何证据包，provenance 都是 `dirty: true`，
等于自毁本项目最核心的卖点。

**Files:**
- Modify: `.gitignore`（已改，待提交）
- Add: `pytest.ini`（当前未跟踪）
- Add: `docs/aiinfra/`（当前未跟踪）
- Commit: 已在工作树里的 339 个删除 + 7 个修改

**Interfaces:**
- Consumes: 无
- Produces: 一个 clean 的 `git status --porcelain`（空输出），后续所有任务依赖它

- [ ] **Step 1: 记录并冻结测试基线**

```bash
python -m pytest tests/py -q 2>&1 | tail -3
```
Expected: `463 passed, 25 skipped`。把这一行原样贴进提交信息。
若数字不同，**停下来先查清差异**，不要继续 —— 基线不可信时后面所有 gate 都失效。

- [ ] **Step 2: 确认 25 个 skip 全部是环境性的，与本计划无关**

```bash
python -m pytest tests/py -q -rs 2>&1 | grep SKIPPED
```
Expected: 全部命中这五类之一，没有第六类 ——
`no built executable` / `set HRSC_TEST_BINARY` / `missing baseline binary` /
`could not import 'skimage.metrics'` / `requires a clean build-matrix reference binary`。

- [ ] **Step 3: 提交工作树**

```bash
git add -A
git status --porcelain | head
git commit -F - <<'MSG'
chore: retire MSc-cycle documents and track pytest configuration

Baseline after this commit: 463 passed, 25 skipped (tests/py).
All 25 skips are environment-gated (missing binaries, missing scikit-image).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
```

- [ ] **Step 4: 验证 provenance 已经干净**

```bash
python -c "import sys; sys.path.insert(0,'.'); from pathlib import Path; from scripts.harness.runner import git_provenance; print(git_provenance(Path('.')))"
```
Expected: `{'commit': '<sha>', 'dirty': False}`

---

## 阶段 B — 步骤 1：P0 harness 加性泛化

> Spec 门槛（`PLAN.md` 步骤 1 Gate 1–4）由 Task 1–8 共同满足，Task 8 收尾统一验收。

### Task 1: `run_matrix` 支持可选 `arguments`

**Files:**
- Modify: `scripts/run_matrix.py`（`MatrixRun`、`normalise_run`、`run_one`）
- Test: `tests/py/test_aiinfra_harness_contract.py`（新建）

**Interfaces:**
- Consumes: 无
- Produces: `MatrixRun.arguments: tuple[str, ...]`（默认 `()`）；
  模块级函数 `build_command(run: MatrixRun, config: Path) -> tuple[str, ...]`，
  规则为 `(str(binary), *arguments, str(config))`

- [ ] **Step 1: 写失败测试**

新建 `tests/py/test_aiinfra_harness_contract.py`：

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


def _cfg(tmp_path: Path) -> Path:
    path = tmp_path / "case.cfg"
    path.write_text("test = sod\nnx = 4\n", encoding="utf-8")
    return path


def test_run_without_arguments_builds_the_legacy_two_token_command(tmp_path: Path) -> None:
    """The HRSC path must stay byte-identical: (binary, config), nothing else."""
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {"name": "sod", "binary": "build-double/hrsc", "config": str(_cfg(tmp_path))},
        output_root=tmp_path / "out",
    )
    config = run_matrix.materialise_run_config(run)

    assert run.arguments == ()
    assert run_matrix.build_command(run, config) == ("build-double/hrsc", str(config))


def test_arguments_are_inserted_between_binary_and_config(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "arguments": ["scripts/aiinfra/run_workload.py", "--strict"],
            "config": str(_cfg(tmp_path)),
        },
        output_root=tmp_path / "out",
    )
    config = run_matrix.materialise_run_config(run)

    assert run_matrix.build_command(run, config) == (
        "python",
        "scripts/aiinfra/run_workload.py",
        "--strict",
        str(config),
    )


@pytest.mark.parametrize("bad", ("not-a-list", [1, 2], [None]))
def test_non_string_arguments_are_rejected(tmp_path: Path, bad) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="arguments"):
        run_matrix.normalise_run(
            {"name": "bad", "binary": "b", "config": str(_cfg(tmp_path)), "arguments": bad},
            output_root=tmp_path / "out",
        )
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q
```
Expected: FAIL — `AttributeError: module 'scripts.run_matrix' has no attribute 'build_command'`

- [ ] **Step 3: 最小实现**

在 `scripts/run_matrix.py` 的 `MatrixRun` 里加字段（放在 `extra_cfg` 之后、`build_semantics` 之前）：

```python
    arguments: tuple[str, ...] = ()
```

在 `normalise_run` 里，`binary = Path(str(raw["binary"]))` 之后插入：

```python
    raw_arguments = raw.get("arguments", [])
    if not isinstance(raw_arguments, list) or not all(
        isinstance(argument, str) for argument in raw_arguments
    ):
        raise ValueError(f"run '{name}' field 'arguments' must be an array of strings")
```

在 `MatrixRun(...)` 构造里加 `arguments=tuple(raw_arguments),`。

在模块级新增（放在 `materialise_run_config` 之后）：

```python
def build_command(run: MatrixRun, config: Path) -> tuple[str, ...]:
    """Binary, then optional workload arguments, then the materialised config."""
    return (str(run.binary), *run.arguments, str(config))
```

在 `run_one` 里把 `command=(str(run.binary), str(config))` 换成
`command=build_command(run, config)`。

- [ ] **Step 4: 跑测试确认通过，并确认旧测试没被打破**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_scripts.py tests/py/test_harness_runner.py -q
```
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/run_matrix.py tests/py/test_aiinfra_harness_contract.py
git commit -m "feat(harness): allow optional workload arguments in a matrix run" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: `config_filename` — 让非 `.cfg` 配置不被 cfg 覆写逻辑污染

**为什么需要**：`materialise_config` 用 `replace_or_append_cfg`（`key = value` 行格式）写覆写。
LLM 负载的配置是 JSON。把 JSON 命名成 `config.cfg` 并让 cfg 覆写逻辑碰它，会静默产生损坏文件。
本任务用一个可选字段把两条路径**在类型上分开**，并对危险组合 fail-closed。
（这是相对 spec 的一处小扩展，理由见 §Review R-4。）

**Files:**
- Modify: `scripts/run_matrix.py`（`MatrixRun`、`normalise_run`、`materialise_run_config`、`build_metadata`、`_legacy_metadata`）
- Test: `tests/py/test_aiinfra_harness_contract.py`

**Interfaces:**
- Consumes: Task 1 的 `MatrixRun`
- Produces: `MatrixRun.config_filename: str`（默认 `"config.cfg"`）；
  约定：**负载入口从 `Path(config).parent` 取自己的 run 目录**，因此不需要任何路径模板替换

- [ ] **Step 1: 写失败测试**

追加到 `tests/py/test_aiinfra_harness_contract.py`：

```python
def test_default_config_filename_is_config_cfg(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {"name": "sod", "binary": "b", "config": str(_cfg(tmp_path))},
        output_root=tmp_path / "out",
    )
    assert run_matrix.materialise_run_config(run).name == "config.cfg"


def test_json_config_is_copied_verbatim_under_its_own_name(tmp_path: Path) -> None:
    from scripts import run_matrix

    source = tmp_path / "workload.json"
    source.write_text('{"backend": "fake"}\n', encoding="utf-8")

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "config": str(source),
            "config_filename": "config.json",
        },
        output_root=tmp_path / "out",
    )
    target = run_matrix.materialise_run_config(run)

    assert target.name == "config.json"
    assert json.loads(target.read_text(encoding="utf-8")) == {"backend": "fake"}


def test_cfg_overrides_on_a_json_config_fail_closed(tmp_path: Path) -> None:
    from scripts import run_matrix

    source = tmp_path / "workload.json"
    source.write_text('{"backend": "fake"}\n', encoding="utf-8")

    run = run_matrix.normalise_run(
        {
            "name": "workload",
            "binary": "python",
            "config": str(source),
            "config_filename": "config.json",
            "extra_cfg": {"nx": "8"},
        },
        output_root=tmp_path / "out",
    )
    with pytest.raises(ValueError, match="config_filename"):
        run_matrix.materialise_run_config(run)


@pytest.mark.parametrize("bad", ("", ".", "..", "sub/config.cfg", "..\\escape.cfg"))
def test_config_filename_must_be_a_bare_file_name(tmp_path: Path, bad: str) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="config_filename"):
        run_matrix.normalise_run(
            {
                "name": "bad",
                "binary": "b",
                "config": str(_cfg(tmp_path)),
                "config_filename": bad,
            },
            output_root=tmp_path / "out",
        )
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k config_filename
```
Expected: FAIL — `TypeError: MatrixRun.__init__() got an unexpected keyword argument 'config_filename'`

- [ ] **Step 3: 最小实现**

`MatrixRun` 加字段：

```python
    config_filename: str = "config.cfg"
```

`normalise_run` 里，在 `arguments` 校验之后插入：

```python
    config_filename = str(raw.get("config_filename", "config.cfg"))
    if (
        config_filename in ("", ".", "..")
        or "/" in config_filename
        or "\\" in config_filename
    ):
        raise ValueError(
            f"run '{name}' field 'config_filename' must be a bare file name"
        )
```
并在构造里加 `config_filename=config_filename,`。

`materialise_run_config` 整体替换为：

```python
def materialise_run_config(run: MatrixRun) -> Path:
    target = run.run_dir / run.config_filename
    overrides = dict(run.extra_cfg or {})
    is_cfg = run.config_filename.endswith(".cfg")
    if run.raw_output is not None and is_cfg:
        overrides["output_format"] = "binary"
        overrides["output_file"] = str(run.raw_output)
    if overrides and not is_cfg:
        raise ValueError(
            f"run '{run.name}' sets cfg overrides but config_filename "
            f"'{run.config_filename}' is not a '.cfg' file"
        )
    return materialise_config(run.source_config, target, overrides)
```

把 `build_metadata` 里 `RunSpec(..., run_config=run.run_dir / "config.cfg", ...)` 和
`_legacy_metadata` 里 `"run_config": str(run.run_dir / "config.cfg")` 两处字面量换成
`run.run_dir / run.config_filename`。`run_one` 已经用 `materialise_run_config` 的返回值，无需改动。

- [ ] **Step 4: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_scripts.py -q
```
Expected: 全部 PASS（尤其 `test_run_matrix_writes_metadata_and_preserves_cfg` 仍绿）

- [ ] **Step 5: 提交**

```bash
git add scripts/run_matrix.py tests/py/test_aiinfra_harness_contract.py
git commit -m "feat(harness): keep non-cfg workload configs out of the cfg override path" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: 矩阵级 `artifact_kind`，未知种类 fail-closed

**注意**：spec 写的是"`RunSpec` 增加 `artifact_kind`"。实际上 `RequiredArtifact.kind` 已经存在
（`scripts/harness/contracts.py:26`），缺的是**从 matrix JSON 把它传下去**的通道 ——
`run_matrix.run_one` 现在把 `kind="hrsc_binary"` 写死了。所以字段加在 `MatrixRun` 上，
不加在 `RunSpec` 上。（见 §Review R-3）

**Files:**
- Modify: `scripts/run_matrix.py`（import、`MatrixRun`、`normalise_run`、`run_one`）
- Test: `tests/py/test_aiinfra_harness_contract.py`

**Interfaces:**
- Consumes: `scripts.harness.artifacts.get_artifact_validator(kind) -> ArtifactValidator`
- Produces: `MatrixRun.artifact_kind: str`（默认 `"hrsc_binary"`）

- [ ] **Step 1: 写失败测试**

```python
def test_artifact_kind_defaults_to_the_hrsc_binary(tmp_path: Path) -> None:
    from scripts import run_matrix

    run = run_matrix.normalise_run(
        {
            "name": "sod",
            "binary": "b",
            "config": str(_cfg(tmp_path)),
            "output_file": "grid.bin",
        },
        output_root=tmp_path / "out",
    )
    assert run.artifact_kind == "hrsc_binary"


def test_unknown_artifact_kind_is_rejected_at_normalise_time(tmp_path: Path) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="unknown artifact kind"):
        run_matrix.normalise_run(
            {
                "name": "bad",
                "binary": "b",
                "config": str(_cfg(tmp_path)),
                "output_file": "out.json",
                "artifact_kind": "does_not_exist",
            },
            output_root=tmp_path / "out",
        )
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k artifact_kind
```
Expected: FAIL — `AttributeError: 'MatrixRun' object has no attribute 'artifact_kind'`

- [ ] **Step 3: 最小实现**

`scripts/run_matrix.py` 顶部 import 区补上：

```python
from scripts.harness.artifacts import ArtifactValidationError, get_artifact_validator
```

`MatrixRun` 加字段：

```python
    artifact_kind: str = "hrsc_binary"
```

`normalise_run` 里，在 `config_filename` 校验之后插入：

```python
    artifact_kind = str(raw.get("artifact_kind", "hrsc_binary"))
    try:
        get_artifact_validator(artifact_kind)
    except ArtifactValidationError as exc:
        raise ValueError(f"run '{name}' has an {exc}") from exc
```
并在构造里加 `artifact_kind=artifact_kind,`。

`run_one` 里把

```python
            (RequiredArtifact(run.raw_output, kind="hrsc_binary"),)
```
换成
```python
            (RequiredArtifact(run.raw_output, kind=run.artifact_kind),)
```

- [ ] **Step 4: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_scripts.py -q
```
Expected: 全部 PASS

- [ ] **Step 5: 提交**

```bash
git add scripts/run_matrix.py tests/py/test_aiinfra_harness_contract.py
git commit -m "feat(harness): route the artifact kind from the matrix and fail closed on unknown kinds" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: `workload_result` 产物校验器与结果 schema

**Files:**
- Create: `scripts/aiinfra/__init__.py`、`scripts/aiinfra/result_schema.py`
- Modify: `scripts/harness/artifacts.py`
- Test: `tests/py/test_aiinfra_result_schema.py`（新建）

**Interfaces:**
- Produces:
  - `scripts.aiinfra.result_schema.SCHEMA == {"name": "aiinfra.workload-result", "version": 1}`
  - `validate_workload_result(document: Any) -> None`（不合法则 `raise ValueError`，信息里带字段名）
  - `build_workload_result(*, workload, backend, model, environment, cells, completed, expected) -> dict`
  - `scripts.harness.artifacts` 注册表新增键 `"workload_result"`

**文档形状（本计划里结果格式的唯一真相）**

```json
{
  "schema": {"name": "aiinfra.workload-result", "version": 1},
  "workload": "determinism",
  "backend": {"name": "fake", "version": "0", "requested_path": "fake", "effective_path": "fake"},
  "model": {"id": "fake/tiny", "revision": "0000000", "dtype": "float32"},
  "environment": {"container_digest": "none", "python": "3.12.10", "device": "cpu"},
  "cells": [
    {"cell_id": "batch=1", "axes": {"batch_size": 1}, "repeats": 4,
     "unique_output_count": 1, "reproduction_rate": 1.0,
     "output_digests": ["ab12"], "latency_median_s": 0.01, "latency_iqr_s": 0.0}
  ],
  "completion": {"completed": 4, "expected": 4}
}
```

`requested_path` 与 `effective_path` 是分开的两个字段，这是 ADR-6 "记录有效路径而非请求路径"
在 schema 层的落点：本地 fake/eager 阶段两者相同，集群 FP8 阶段它们会不同。

- [ ] **Step 1: 写失败测试**

新建 `tests/py/test_aiinfra_result_schema.py`：

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.harness.artifacts import ArtifactValidationError, validate_artifact


def _document() -> dict:
    from scripts.aiinfra import result_schema

    return result_schema.build_workload_result(
        workload="determinism",
        backend={"name": "fake", "version": "0", "requested_path": "fake", "effective_path": "fake"},
        model={"id": "fake/tiny", "revision": "0000000", "dtype": "float32"},
        environment={"container_digest": "none", "python": "3.12.10", "device": "cpu"},
        cells=[
            {
                "cell_id": "batch=1",
                "axes": {"batch_size": 1},
                "repeats": 4,
                "unique_output_count": 1,
                "reproduction_rate": 1.0,
                "output_digests": ["ab12"],
                "latency_median_s": 0.01,
                "latency_iqr_s": 0.0,
            }
        ],
        completed=4,
        expected=4,
    )


def test_builder_produces_a_document_that_validates() -> None:
    from scripts.aiinfra import result_schema

    result_schema.validate_workload_result(_document())


def test_completed_below_expected_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["completion"]["completed"] = 3
    with pytest.raises(ValueError, match="completion"):
        result_schema.validate_workload_result(document)


def test_unexpected_top_level_field_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["surprise"] = 1
    with pytest.raises(ValueError, match="unexpected"):
        result_schema.validate_workload_result(document)


def test_unique_output_count_must_agree_with_the_digests() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0]["output_digests"] = ["ab12", "cd34"]
    with pytest.raises(ValueError, match="unique_output_count"):
        result_schema.validate_workload_result(document)


def test_non_finite_latency_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0]["latency_median_s"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        result_schema.validate_workload_result(document)


def test_artifact_validator_accepts_a_valid_result_file(tmp_path: Path) -> None:
    path = tmp_path / "workload_result.json"
    path.write_text(json.dumps(_document()), encoding="utf-8")

    validate_artifact(path, "workload_result")


def test_artifact_validator_rejects_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "workload_result.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ArtifactValidationError):
        validate_artifact(path, "workload_result")
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_result_schema.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.aiinfra'`

- [ ] **Step 3: 最小实现 — `scripts/aiinfra/__init__.py`**

```python
"""Workload family 2 (LLM inference) adapters for the shared harness."""
```

- [ ] **Step 4: 最小实现 — `scripts/aiinfra/result_schema.py`**

```python
"""Single source of truth for the `aiinfra.workload-result` document."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


SCHEMA = {"name": "aiinfra.workload-result", "version": 1}

TOP_LEVEL_FIELDS = {
    "schema",
    "workload",
    "backend",
    "model",
    "environment",
    "cells",
    "completion",
}
BACKEND_FIELDS = {"name", "version", "requested_path", "effective_path"}
MODEL_FIELDS = {"id", "revision", "dtype"}
CELL_FIELDS = {
    "cell_id",
    "axes",
    "repeats",
    "unique_output_count",
    "reproduction_rate",
    "output_digests",
    "latency_median_s",
    "latency_iqr_s",
}


def _exact_fields(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"workload result {where} must be an object")
    missing = sorted(fields - value.keys())
    unexpected = sorted(value.keys() - fields)
    if missing:
        raise ValueError(f"workload result {where} is missing {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"workload result {where} has unexpected {', '.join(unexpected)}")
    return value


def _finite(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"workload result {where} must be a number")
    if not math.isfinite(float(value)):
        raise ValueError(f"workload result {where} must be finite")
    return float(value)


def _nonneg_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"workload result {where} must be a non-negative integer")
    return value


def _nonempty_string(value: Any, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"workload result {where} must be a non-empty string")
    return value


def validate_workload_result(document: Any) -> None:
    """Raise ValueError with one readable reason if *document* is not schema v1."""
    _exact_fields(document, TOP_LEVEL_FIELDS, "document")

    schema = _exact_fields(document["schema"], set(SCHEMA), "schema")
    if schema["name"] != SCHEMA["name"]:
        raise ValueError("workload result schema.name is unsupported")
    if type(schema["version"]) is not int or schema["version"] != SCHEMA["version"]:
        raise ValueError("workload result schema.version is unsupported")

    _nonempty_string(document["workload"], "workload")

    backend = _exact_fields(document["backend"], BACKEND_FIELDS, "backend")
    for field in sorted(BACKEND_FIELDS):
        _nonempty_string(backend[field], f"backend.{field}")

    model = _exact_fields(document["model"], MODEL_FIELDS, "model")
    for field in sorted(MODEL_FIELDS):
        _nonempty_string(model[field], f"model.{field}")

    if not isinstance(document["environment"], Mapping):
        raise ValueError("workload result environment must be an object")

    cells = document["cells"]
    if not isinstance(cells, Sequence) or isinstance(cells, str) or not cells:
        raise ValueError("workload result cells must be a non-empty array")
    for index, cell in enumerate(cells):
        where = f"cells[{index}]"
        _exact_fields(cell, CELL_FIELDS, where)
        _nonempty_string(cell["cell_id"], f"{where}.cell_id")
        if not isinstance(cell["axes"], Mapping):
            raise ValueError(f"workload result {where}.axes must be an object")
        repeats = _nonneg_int(cell["repeats"], f"{where}.repeats")
        if repeats == 0:
            raise ValueError(f"workload result {where}.repeats must be positive")
        unique = _nonneg_int(cell["unique_output_count"], f"{where}.unique_output_count")
        digests = cell["output_digests"]
        if not isinstance(digests, Sequence) or isinstance(digests, str):
            raise ValueError(f"workload result {where}.output_digests must be an array")
        if len(digests) != repeats:
            raise ValueError(
                f"workload result {where}.output_digests must hold one digest per repeat"
            )
        if len(set(digests)) != unique:
            raise ValueError(
                f"workload result {where}.unique_output_count disagrees with output_digests"
            )
        rate = _finite(cell["reproduction_rate"], f"{where}.reproduction_rate")
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"workload result {where}.reproduction_rate must lie in [0, 1]")
        _finite(cell["latency_median_s"], f"{where}.latency_median_s")
        _finite(cell["latency_iqr_s"], f"{where}.latency_iqr_s")

    completion = _exact_fields(
        document["completion"], {"completed", "expected"}, "completion"
    )
    completed = _nonneg_int(completion["completed"], "completion.completed")
    expected = _nonneg_int(completion["expected"], "completion.expected")
    if completed != expected:
        raise ValueError(
            f"workload result completion is partial: {completed} of {expected}"
        )


def build_workload_result(
    *,
    workload: str,
    backend: Mapping[str, str],
    model: Mapping[str, str],
    environment: Mapping[str, Any],
    cells: Sequence[Mapping[str, Any]],
    completed: int,
    expected: int,
) -> dict[str, Any]:
    """Assemble a schema-v1 document; the caller validates before writing."""
    return {
        "schema": dict(SCHEMA),
        "workload": workload,
        "backend": dict(backend),
        "model": dict(model),
        "environment": dict(environment),
        "cells": [dict(cell) for cell in cells],
        "completion": {"completed": completed, "expected": expected},
    }
```

- [ ] **Step 5: 最小实现 — 注册到 `scripts/harness/artifacts.py`**

顶部加 `import json`；在 `_validate_hrsc_binary` 之后新增：

```python
def _validate_workload_result(path: Path) -> None:
    from scripts.aiinfra.result_schema import validate_workload_result

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactValidationError(f"cannot read workload result: {path}: {exc}") from exc
    try:
        validate_workload_result(document)
    except ValueError as exc:
        raise ArtifactValidationError(f"{path}: {exc}") from exc
```

在 `_ARTIFACT_VALIDATORS` 里加一行：

```python
    "workload_result": _validate_workload_result,
```

> 延迟 import 是刻意的：`scripts/harness/` 不应在 import 期依赖 `scripts/aiinfra/`，
> 只在真正校验这一种产物时才拉进来。

- [ ] **Step 6: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_result_schema.py tests/py/test_harness_runner.py -q
```
Expected: 全部 PASS

- [ ] **Step 7: 提交**

```bash
git add scripts/aiinfra/__init__.py scripts/aiinfra/result_schema.py scripts/harness/artifacts.py tests/py/test_aiinfra_result_schema.py
git commit -m "feat(harness): validate aiinfra workload-result artifacts" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: `run-status` 支持 `kind=workload`，并把 `reason` 收紧为枚举

**Files:**
- Modify: `scripts/harness/contracts.py`（`FailureCategory`）
- Modify: `scripts/harness/runner.py`（`parse_run_status`）
- Test: `tests/py/test_aiinfra_harness_contract.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `FailureCategory.RESOURCE_EXHAUSTED = "resource_exhausted"`
  - 新 status 行格式：`[run-status] status=success kind=workload completed=<n> expected=<n>`
  - `parse_run_status` 对该行返回 `completion == {"kind": "workload", "completed": n, "expected": n}`
  - 不带 `kind` 的旧行为逐字不变（仍要 `final_time` / `target_time` / `steps`）
  - `status=failed reason=<x>`：`<x>` 必须是 `FailureCategory` 的成员值，否则 `schema_error`

**为什么收紧 `reason`**：现在 `runner.py:66` 是 `parsed.get("reason", "infrastructure_error")`，
任意字符串都会原样进入 metadata 并流进聚合。C++ 侧（`src/app/run_completion.cpp:9-22`）只发出
5 个已知类别，全部已在 Python 枚举里，所以收紧是零风险的，却能挡住新负载写错类别时的静默污染。

- [ ] **Step 1: 写失败测试**

追加到 `tests/py/test_aiinfra_harness_contract.py`：

```python
def test_legacy_success_line_still_requires_the_solver_fields() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success final_time=0.1 target_time=0.1 steps=4\n"
    )
    assert (status, failure) == ("success", None)
    assert completion == {"final_time": 0.1, "target_time": 0.1, "steps": 4}


def test_workload_success_line_reports_completed_and_expected() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success kind=workload completed=50 expected=50\n"
    )
    assert (status, failure) == ("success", None)
    assert completion == {"kind": "workload", "completed": 50, "expected": 50}


def test_workload_line_with_fewer_completed_than_expected_is_incomplete() -> None:
    from scripts.harness.runner import parse_run_status

    status, completion, failure = parse_run_status(
        "[run-status] status=success kind=workload completed=49 expected=50\n"
    )
    assert status == "failed"
    assert completion is None
    assert failure["category"] == "incomplete_run"


def test_unknown_status_kind_is_a_schema_error() -> None:
    from scripts.harness.runner import parse_run_status

    status, _completion, failure = parse_run_status(
        "[run-status] status=success kind=telepathy completed=1 expected=1\n"
    )
    assert status == "failed"
    assert failure["category"] == "schema_error"


def test_resource_exhausted_is_a_recognised_failure_category() -> None:
    from scripts.harness.contracts import FailureCategory
    from scripts.harness.runner import parse_run_status

    assert FailureCategory.RESOURCE_EXHAUSTED.value == "resource_exhausted"

    status, _completion, failure = parse_run_status(
        "[run-status] status=failed reason=resource_exhausted\n"
    )
    assert status == "failed"
    assert failure["category"] == "resource_exhausted"


def test_unknown_failure_reason_is_a_schema_error() -> None:
    from scripts.harness.runner import parse_run_status

    status, _completion, failure = parse_run_status(
        "[run-status] status=failed reason=made_up_category\n"
    )
    assert status == "failed"
    assert failure["category"] == "schema_error"
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k "workload or resource_exhausted or reason or kind"
```
Expected: FAIL — `AttributeError: RESOURCE_EXHAUSTED` 与 `KeyError: 'final_time'`

- [ ] **Step 3: 最小实现 — `scripts/harness/contracts.py`**

在 `FailureCategory` 里，`INCOMPLETE` 之后加一行：

```python
    RESOURCE_EXHAUSTED = "resource_exhausted"
```

- [ ] **Step 4: 最小实现 — `scripts/harness/runner.py`**

顶部 import 改为：

```python
from .contracts import FailureCategory, RunRecord, RunSpec
```

把 `parse_run_status` 从 `if parsed.get("status") == "success":` 起的整段替换为：

```python
    if parsed.get("status") == "success":
        kind = parsed.get("kind")
        if kind is None:
            return _parse_solver_completion(parsed)
        if kind == "workload":
            return _parse_workload_completion(parsed)
        return "failed", None, _failure(
            "schema_error", f"unknown run-status kind: {kind!r}"
        )
    category = parsed.get("reason", FailureCategory.INFRASTRUCTURE.value)
    if category not in {member.value for member in FailureCategory}:
        return "failed", None, _failure(
            "schema_error", f"unknown run-status reason: {category!r}"
        )
    return "failed", None, {"category": category, "message": category}
```

并在 `parse_run_status` **之前**新增两个私有解析器（原有的求解器分支原样搬进
`_parse_solver_completion`，一个字符都不改）：

```python
def _parse_solver_completion(
    parsed: dict[str, str],
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    try:
        final_time = float(parsed["final_time"])
        target_time = float(parsed["target_time"])
        steps = int(parsed["steps"])
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        return "failed", None, _failure("schema_error", f"invalid completion fields: {exc}")
    if not math.isfinite(final_time) or not math.isfinite(target_time):
        return "failed", None, _failure("schema_error", "completion times must be finite")
    if steps < 0:
        return "failed", None, _failure(
            "schema_error", "completion steps must be non-negative"
        )
    if final_time < target_time:
        return "failed", None, _failure(
            "schema_error", "completion final_time must reach target_time"
        )
    return "success", {
        "final_time": final_time,
        "target_time": target_time,
        "steps": steps,
    }, None


def _parse_workload_completion(
    parsed: dict[str, str],
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    try:
        completed = int(parsed["completed"])
        expected = int(parsed["expected"])
    except (KeyError, TypeError, ValueError) as exc:
        return "failed", None, _failure("schema_error", f"invalid workload fields: {exc}")
    if completed < 0 or expected <= 0:
        return "failed", None, _failure(
            "schema_error", "workload counts must be non-negative with a positive expected"
        )
    if completed != expected:
        return "failed", None, _failure(
            FailureCategory.INCOMPLETE.value,
            f"workload completed {completed} of {expected} units",
        )
    return "success", {
        "kind": "workload",
        "completed": completed,
        "expected": expected,
    }, None
```

- [ ] **Step 5: 跑测试确认通过，尤其确认旧 runner 测试全绿**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py tests/py/test_harness_runner.py tests/py/test_application_status_contract.py -q
```
Expected: 全部 PASS（`test_application_status_contract.py` 会 skip 9+3 个需要二进制的用例）

- [ ] **Step 6: 提交**

```bash
git add scripts/harness/contracts.py scripts/harness/runner.py tests/py/test_aiinfra_harness_contract.py
git commit -m "feat(harness): accept workload completion status and reject unknown failure reasons" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: 负载配置加载与只读环境探针

**Files:**
- Create: `scripts/aiinfra/config.py`、`scripts/aiinfra/environment.py`
- Create: `configs/aiinfra/models.json`
- Test: `tests/py/test_aiinfra_config.py`、`tests/py/test_aiinfra_environment.py`（均新建）

**Interfaces:**
- Produces:
  - `config.CONFIG_SCHEMA == {"name": "aiinfra.workload-config", "version": 1}`
  - `config.load_workload_config(path: Path) -> WorkloadConfig`（frozen dataclass）
  - `WorkloadConfig` 字段：`workload: str`、`backend: str`、`model_key: str`、`dtype: str`、
    `prompt: str`、`max_new_tokens: int`、`repeats: int`、`batch_sizes: tuple[int, ...]`、
    `seed: int`、`decode: str`、`options: dict[str, Any]`
  - `config.load_model_pins(path: Path) -> dict[str, dict[str, str]]`
  - `config.resolve_model(config: WorkloadConfig, pins: Mapping) -> dict[str, str]`
    → `{"id", "revision", "dtype"}`
  - `environment.probe() -> dict[str, Any]`（**永不抛异常**）
  - `environment.main()` → `--json` 打印探针结果

**配置文件形状**

```json
{
  "schema": {"name": "aiinfra.workload-config", "version": 1},
  "workload": "determinism",
  "backend": "fake",
  "model": "fake-tiny",
  "dtype": "float32",
  "prompt": "Explain why floating-point addition is not associative.",
  "max_new_tokens": 64,
  "repeats": 4,
  "batch_sizes": [1, 8],
  "seed": 0,
  "decode": "greedy",
  "options": {"nondeterminism": "none"}
}
```

`decode` 只接受 `"greedy"`（`PLAN.md` §4 固定 greedy 解码；采样一旦引入就无法区分
"实现不确定性"与"采样随机性"）。

**`configs/aiinfra/models.json` 初始内容**（只放 fake 条目；真实 Qwen 的 revision 由
Task 14 解析出真值后写入，本计划**不预先编造 sha**）：

```json
{
  "schema": {"name": "aiinfra.model-pins", "version": 1},
  "models": {
    "fake-tiny": {
      "id": "fake/tiny",
      "revision": "builtin",
      "source": "builtin",
      "approx_weight_bytes": 0
    }
  }
}
```

- [ ] **Step 1: 写失败测试 — `tests/py/test_aiinfra_config.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(tmp_path: Path, **overrides) -> Path:
    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 8,
        "repeats": 4,
        "batch_sizes": [1, 8],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_valid_config_round_trips(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    loaded = config.load_workload_config(_write(tmp_path))

    assert loaded.workload == "determinism"
    assert loaded.batch_sizes == (1, 8)
    assert loaded.decode == "greedy"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    (
        ({"decode": "sampling"}, "decode"),
        ({"repeats": 0}, "repeats"),
        ({"batch_sizes": []}, "batch_sizes"),
        ({"batch_sizes": [0]}, "batch_sizes"),
        ({"max_new_tokens": -1}, "max_new_tokens"),
        ({"prompt": ""}, "prompt"),
        ({"schema": {"name": "aiinfra.workload-config", "version": 2}}, "schema"),
    ),
)
def test_invalid_configs_fail_closed(tmp_path: Path, overrides, expected: str) -> None:
    from scripts.aiinfra import config

    with pytest.raises(ValueError, match=expected):
        config.load_workload_config(_write(tmp_path, **overrides))


def test_unknown_field_is_rejected(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    with pytest.raises(ValueError, match="unexpected"):
        config.load_workload_config(_write(tmp_path, surprise=1))


def test_committed_model_pins_load_and_resolve(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    pins = config.load_model_pins(REPO_ROOT / "configs" / "aiinfra" / "models.json")
    resolved = config.resolve_model(config.load_workload_config(_write(tmp_path)), pins)

    assert set(resolved) == {"id", "revision", "dtype"}
    assert resolved["id"] == "fake/tiny"
    assert resolved["dtype"] == "float32"


def test_unknown_model_key_fails_closed(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    pins = config.load_model_pins(REPO_ROOT / "configs" / "aiinfra" / "models.json")
    loaded = config.load_workload_config(_write(tmp_path, model="not-pinned"))

    with pytest.raises(ValueError, match="not-pinned"):
        config.resolve_model(loaded, pins)
```

- [ ] **Step 2: 写失败测试 — `tests/py/test_aiinfra_environment.py`**

```python
from __future__ import annotations

import builtins

import pytest


def test_probe_returns_a_serialisable_mapping() -> None:
    import json

    from scripts.aiinfra import environment

    probe = environment.probe()

    assert set(probe) >= {"platform", "python", "container_digest", "torch", "vllm", "devices", "git"}
    json.dumps(probe)


def test_probe_never_raises_when_torch_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.aiinfra import environment

    real_import = builtins.__import__

    def fail_on_torch(name, *args, **kwargs):
        if name.split(".")[0] in {"torch", "vllm"}:
            raise ImportError(f"blocked {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_on_torch)

    probe = environment.probe()

    assert probe["torch"]["available"] is False
    assert probe["vllm"]["available"] is False
    assert "blocked" in probe["torch"]["reason"]


def test_container_digest_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.aiinfra import environment

    monkeypatch.setenv("AIINFRA_CONTAINER_DIGEST", "sha256:deadbeef")

    assert environment.probe()["container_digest"] == "sha256:deadbeef"
```

- [ ] **Step 3: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_config.py tests/py/test_aiinfra_environment.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.aiinfra.config'`

- [ ] **Step 4: 实现 `scripts/aiinfra/config.py`**

```python
"""Loading and fail-closed validation of aiinfra workload configurations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CONFIG_SCHEMA = {"name": "aiinfra.workload-config", "version": 1}
PINS_SCHEMA = {"name": "aiinfra.model-pins", "version": 1}
CONFIG_FIELDS = {
    "schema",
    "workload",
    "backend",
    "model",
    "dtype",
    "prompt",
    "max_new_tokens",
    "repeats",
    "batch_sizes",
    "seed",
    "decode",
    "options",
}
SUPPORTED_DECODES = {"greedy"}
SUPPORTED_DTYPES = {"float32", "float16", "bfloat16"}
PIN_FIELDS = {"id", "revision", "source", "approx_weight_bytes"}


@dataclass(frozen=True)
class WorkloadConfig:
    workload: str
    backend: str
    model_key: str
    dtype: str
    prompt: str
    max_new_tokens: int
    repeats: int
    batch_sizes: tuple[int, ...]
    seed: int
    decode: str
    options: dict[str, Any] = field(default_factory=dict)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def _exact_fields(value: Any, fields: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{where} must be an object")
    missing = sorted(fields - value.keys())
    unexpected = sorted(value.keys() - fields)
    if missing:
        raise ValueError(f"{where} is missing {', '.join(missing)}")
    if unexpected:
        raise ValueError(f"{where} has unexpected {', '.join(unexpected)}")
    return value


def _check_schema(value: Any, expected: Mapping[str, Any], where: str) -> None:
    schema = _exact_fields(value, set(expected), where)
    if schema["name"] != expected["name"] or schema["version"] != expected["version"]:
        raise ValueError(f"{where} is unsupported: {schema}")


def _positive_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{where} must be a positive integer")
    return value


def _nonneg_int(value: Any, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{where} must be a non-negative integer")
    return value


def load_workload_config(path: Path) -> WorkloadConfig:
    """Load *path* as a schema-v1 workload configuration or raise ValueError."""
    document = _read_json(path)
    _exact_fields(document, CONFIG_FIELDS, "workload config")
    _check_schema(document["schema"], CONFIG_SCHEMA, "workload config schema")

    for name in ("workload", "backend", "model", "prompt"):
        if not isinstance(document[name], str) or not document[name]:
            raise ValueError(f"workload config {name} must be a non-empty string")
    if document["dtype"] not in SUPPORTED_DTYPES:
        raise ValueError(f"workload config dtype must be one of {sorted(SUPPORTED_DTYPES)}")
    if document["decode"] not in SUPPORTED_DECODES:
        raise ValueError(f"workload config decode must be one of {sorted(SUPPORTED_DECODES)}")

    batch_sizes = document["batch_sizes"]
    if not isinstance(batch_sizes, list) or not batch_sizes:
        raise ValueError("workload config batch_sizes must be a non-empty array")
    for index, size in enumerate(batch_sizes):
        _positive_int(size, f"workload config batch_sizes[{index}]")
    if not isinstance(document["options"], Mapping):
        raise ValueError("workload config options must be an object")

    return WorkloadConfig(
        workload=document["workload"],
        backend=document["backend"],
        model_key=document["model"],
        dtype=document["dtype"],
        prompt=document["prompt"],
        max_new_tokens=_positive_int(document["max_new_tokens"], "workload config max_new_tokens"),
        repeats=_positive_int(document["repeats"], "workload config repeats"),
        batch_sizes=tuple(batch_sizes),
        seed=_nonneg_int(document["seed"], "workload config seed"),
        decode=document["decode"],
        options=dict(document["options"]),
    )


def load_model_pins(path: Path) -> dict[str, dict[str, Any]]:
    """Load the committed model pin table or raise ValueError."""
    document = _read_json(path)
    _exact_fields(document, {"schema", "models"}, "model pins")
    _check_schema(document["schema"], PINS_SCHEMA, "model pins schema")
    models = document["models"]
    if not isinstance(models, Mapping) or not models:
        raise ValueError("model pins models must be a non-empty object")
    for key, pin in models.items():
        _exact_fields(pin, PIN_FIELDS, f"model pins models[{key!r}]")
    return {str(key): dict(pin) for key, pin in models.items()}


def resolve_model(config: WorkloadConfig, pins: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Return the run-record model block for *config*, or raise on an unpinned key."""
    try:
        pin = pins[config.model_key]
    except KeyError as exc:
        raise ValueError(
            f"workload config model {config.model_key!r} is not pinned in models.json"
        ) from exc
    return {"id": str(pin["id"]), "revision": str(pin["revision"]), "dtype": config.dtype}
```

- [ ] **Step 5: 实现 `scripts/aiinfra/environment.py`**

```python
#!/usr/bin/env python3
"""Read-only environment probe. Installs nothing, downloads nothing, never raises."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.harness.runner import git_provenance


REPO_ROOT = Path(__file__).resolve().parents[2]
NVIDIA_SMI_TIMEOUT_S = 10.0


def _probe_module(name: str) -> dict[str, Any]:
    try:
        module = __import__(name)
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {"available": True, "version": str(getattr(module, "__version__", "unknown"))}


def _probe_torch() -> dict[str, Any]:
    probe = _probe_module("torch")
    if not probe["available"]:
        return probe
    try:
        import torch

        probe["cuda_version"] = str(torch.version.cuda)
        probe["cuda_available"] = bool(torch.cuda.is_available())
        probe["device_count"] = int(torch.cuda.device_count()) if probe["cuda_available"] else 0
    except Exception as exc:
        probe["cuda_probe_error"] = f"{type(exc).__name__}: {exc}"
    return probe


def _probe_devices() -> list[dict[str, str]]:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=NVIDIA_SMI_TIMEOUT_S,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        return [{"error": f"{type(exc).__name__}: {exc}"}]
    devices = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            devices.append(
                {
                    "name": parts[0],
                    "memory_total": parts[1],
                    "driver_version": parts[2],
                    "compute_capability": parts[3],
                }
            )
    return devices


def probe() -> dict[str, Any]:
    """Collect everything a run record needs about this machine. Never raises."""
    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "container_digest": os.environ.get("AIINFRA_CONTAINER_DIGEST", "none"),
        "torch": _probe_torch(),
        "vllm": _probe_module("vllm"),
        "devices": _probe_devices(),
        "git": git_provenance(REPO_ROOT),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the probe as JSON")
    args = parser.parse_args()
    document = probe()
    if args.json:
        json.dump(document, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for key, value in sorted(document.items()):
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_config.py tests/py/test_aiinfra_environment.py -q
python scripts/aiinfra/environment.py --json
```
Expected: 测试全绿；探针在本机打印
`"torch": {"available": false, ...}` 与一条 RTX 5070 Laptop 设备记录（8151 MiB / 591.91）。

- [ ] **Step 7: 提交**

```bash
git add scripts/aiinfra/config.py scripts/aiinfra/environment.py configs/aiinfra/models.json tests/py/test_aiinfra_config.py tests/py/test_aiinfra_environment.py
git commit -m "feat(aiinfra): add workload configuration loading and a read-only environment probe" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: 后端接口、fake 后端与重复测量核心

**Files:**
- Create: `scripts/aiinfra/backends/__init__.py`、`scripts/aiinfra/backends/base.py`、
  `scripts/aiinfra/backends/fake.py`、`scripts/aiinfra/determinism.py`
- Test: `tests/py/test_aiinfra_determinism.py`（新建）

**Interfaces:**
- Consumes: `config.WorkloadConfig`
- Produces:
  - `base.GenerationRequest(prompt: str, batch_size: int, max_new_tokens: int, seed: int, dtype: str)`
  - `base.GenerationResult(texts: tuple[str, ...], logits: Any | None, latency_s: float)`
  - `base.WorkloadFailure(category: str, message: str)` — 携带 `FailureCategory` 值的异常
  - `base.get_backend(name: str, *, model: Mapping[str, str], options: Mapping) -> Backend`
    未知后端 → `WorkloadFailure("unsupported_capability", ...)`
  - `Backend.describe() -> dict[str, str]`，键为 `{"name", "version", "requested_path", "effective_path"}`
  - `determinism.measure_cells(backend, config) -> list[dict]` — 每个 `batch_size` 一格，
    形状与 `result_schema.CELL_FIELDS` 完全一致

**测量单元的定义（ADR-8 落地，必须照做）**：一格 = 一个 `batch_size`。每次 repeat 用
**同一个 prompt 填满整个 batch**，只统计 `texts[0]`（batch 内第 0 号序列）的输出。
digest = `sha256(texts[0].encode("utf-8")).hexdigest()`。这样"只改 batch size"就是唯一变量，
和 Thinking Machines / LMSYS 的报告口径一致。

**同时报 `unique_output_count` 与 `reproduction_rate`**：前者是 headline（ADR-8），后者
= 最常见 digest 的出现次数 / repeats，在 spike 落到 L2 不通过（时灵时不灵）时**不需要改代码**
就能改口径。（见 §Review R-6）

**计时协议**：每格先跑 1 次 warm-up 并**丢弃它的延迟与 digest**，然后 `repeats` 次计入，
报 median 与 IQR —— 与 `experiments/week18/kh_solver_timing`（`warmups_per_group: 1`,
`timing_statistic: median`, `variability_statistic: IQR`）同形。丢弃 warm-up 的 digest 是
刻意的：冷启动差异属于加载路径，不是推理不确定性。（见 §Review R-16）

- [ ] **Step 1: 写失败测试 — `tests/py/test_aiinfra_determinism.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _config(tmp_path: Path, **overrides):
    from scripts.aiinfra import config

    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 8,
        "repeats": 4,
        "batch_sizes": [1, 8],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return config.load_workload_config(path)


def _backend(loaded):
    from scripts.aiinfra.backends import base

    return base.get_backend(
        loaded.backend,
        model={"id": "fake/tiny", "revision": "builtin", "dtype": loaded.dtype},
        options=loaded.options,
    )


def test_deterministic_backend_gives_one_unique_output_per_cell(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path)
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert [cell["cell_id"] for cell in cells] == ["batch_size=1", "batch_size=8"]
    assert all(cell["unique_output_count"] == 1 for cell in cells)
    assert all(cell["reproduction_rate"] == 1.0 for cell in cells)
    assert all(len(cell["output_digests"]) == 4 for cell in cells)


def test_batch_sensitive_backend_changes_the_output_across_batch_sizes(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path, options={"nondeterminism": "batch"})
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert all(cell["unique_output_count"] == 1 for cell in cells)
    assert cells[0]["output_digests"][0] != cells[1]["output_digests"][0]


def test_repeat_sensitive_backend_reports_more_than_one_unique_output(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path, options={"nondeterminism": "repeat"})
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert cells[0]["unique_output_count"] == 4
    assert cells[0]["reproduction_rate"] == 0.25


def test_cells_satisfy_the_result_schema(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism, result_schema

    loaded = _config(tmp_path)
    cells = determinism.measure_cells(_backend(loaded), loaded)
    document = result_schema.build_workload_result(
        workload=loaded.workload,
        backend=_backend(loaded).describe(),
        model={"id": "fake/tiny", "revision": "builtin", "dtype": loaded.dtype},
        environment={"container_digest": "none"},
        cells=cells,
        completed=len(cells),
        expected=len(cells),
    )

    result_schema.validate_workload_result(document)


@pytest.mark.parametrize(
    ("fault", "category"),
    (("resource_exhausted", "resource_exhausted"), ("unsupported_capability", "unsupported_capability")),
)
def test_injected_faults_raise_a_categorised_workload_failure(
    tmp_path: Path, fault: str, category: str
) -> None:
    from scripts.aiinfra import determinism
    from scripts.aiinfra.backends import base

    loaded = _config(tmp_path, options={"fault": fault})
    with pytest.raises(base.WorkloadFailure) as excinfo:
        determinism.measure_cells(_backend(loaded), loaded)

    assert excinfo.value.category == category


def test_unknown_backend_is_an_unsupported_capability(tmp_path: Path) -> None:
    from scripts.aiinfra.backends import base

    loaded = _config(tmp_path, backend="does-not-exist")
    with pytest.raises(base.WorkloadFailure) as excinfo:
        _backend(loaded)

    assert excinfo.value.category == "unsupported_capability"
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_determinism.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.aiinfra.backends'`

- [ ] **Step 3: 实现 `scripts/aiinfra/backends/__init__.py`**

```python
"""Backend adapters. Import `base` and call `get_backend`; never import a backend directly."""
```

- [ ] **Step 4: 实现 `scripts/aiinfra/backends/base.py`**

```python
"""Backend interface, failure type, and the registry the workload entry point uses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from scripts.harness.contracts import FailureCategory


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    batch_size: int
    max_new_tokens: int
    seed: int
    dtype: str


@dataclass(frozen=True)
class GenerationResult:
    texts: tuple[str, ...]
    logits: Any | None
    latency_s: float


class WorkloadFailure(Exception):
    """A failure that must reach the run record as a structured category."""

    def __init__(self, category: str, message: str) -> None:
        valid = {member.value for member in FailureCategory}
        if category not in valid:
            raise ValueError(f"unknown failure category: {category!r}")
        super().__init__(message)
        self.category = category


class Backend(Protocol):
    def describe(self) -> dict[str, str]: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


def get_backend(
    name: str, *, model: Mapping[str, str], options: Mapping[str, Any]
) -> Backend:
    """Construct a backend by name. Unknown names are a capability failure, not a crash."""
    if name == "fake":
        from scripts.aiinfra.backends.fake import FakeBackend

        return FakeBackend(model=model, options=options)
    if name == "torch_eager":
        from scripts.aiinfra.backends.torch_eager import TorchEagerBackend

        return TorchEagerBackend(model=model, options=options)
    if name == "vllm_offline":
        from scripts.aiinfra.backends.vllm_offline import VllmOfflineBackend

        return VllmOfflineBackend(model=model, options=options)
    raise WorkloadFailure(
        FailureCategory.UNSUPPORTED.value, f"no backend named {name!r}"
    )
```

> `torch_eager` / `vllm_offline` 的 import 在 Task 18 之前会 `ModuleNotFoundError`。
> 这是刻意的：注册表不应吞掉"文件还没写"和"依赖没装"的区别 —— Task 18 会让这两个模块在
> 缺依赖时抛 `WorkloadFailure("unsupported_capability", ...)`，而不是让注册表提前假装。

- [ ] **Step 5: 实现 `scripts/aiinfra/backends/fake.py`**

```python
"""A CPU-only, torch-free backend that exercises every harness path deterministically."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping
from typing import Any

from scripts.aiinfra.backends.base import (
    GenerationRequest,
    GenerationResult,
    WorkloadFailure,
)


VERSION = "1"
NONDETERMINISM_MODES = {"none", "batch", "repeat"}
FAULTS = {"none", "resource_exhausted", "unsupported_capability"}
# One synthetic token is eight hex characters of a SHA-256 stream; the count is the
# only thing max_new_tokens controls here, so output length tracks the request.
TOKEN_HEX_WIDTH = 8


class FakeBackend:
    """Generates reproducible pseudo-text without loading any model weights."""

    def __init__(self, *, model: Mapping[str, str], options: Mapping[str, Any]) -> None:
        self._model = dict(model)
        self._mode = str(options.get("nondeterminism", "none"))
        if self._mode not in NONDETERMINISM_MODES:
            raise WorkloadFailure(
                "configuration_error",
                f"fake backend nondeterminism must be one of {sorted(NONDETERMINISM_MODES)}",
            )
        self._fault = str(options.get("fault", "none"))
        if self._fault not in FAULTS:
            raise WorkloadFailure(
                "configuration_error", f"fake backend fault must be one of {sorted(FAULTS)}"
            )
        self._call_index = 0

    def describe(self) -> dict[str, str]:
        return {
            "name": "fake",
            "version": VERSION,
            "requested_path": f"fake:{self._mode}",
            "effective_path": f"fake:{self._mode}",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._fault == "resource_exhausted":
            raise WorkloadFailure(
                "resource_exhausted",
                f"fake backend refused batch_size={request.batch_size}",
            )
        if self._fault == "unsupported_capability":
            raise WorkloadFailure(
                "unsupported_capability",
                f"fake backend does not implement dtype={request.dtype}",
            )

        started = time.perf_counter()
        parts = [self._model.get("id", ""), request.prompt, str(request.seed), request.dtype]
        if self._mode == "batch":
            parts.append(f"batch={request.batch_size}")
        if self._mode == "repeat":
            parts.append(f"call={self._call_index}")
        seed_material = "|".join(parts).encode("utf-8")

        text = self._stream(seed_material, request.max_new_tokens)
        self._call_index += 1
        return GenerationResult(
            texts=tuple([text] * request.batch_size),
            logits=None,
            latency_s=time.perf_counter() - started,
        )

    @staticmethod
    def _stream(seed_material: bytes, token_count: int) -> str:
        tokens = []
        digest = hashlib.sha256(seed_material).digest()
        while len(tokens) < token_count:
            digest = hashlib.sha256(digest).digest()
            chunk = digest.hex()
            tokens.extend(
                chunk[index : index + TOKEN_HEX_WIDTH]
                for index in range(0, len(chunk), TOKEN_HEX_WIDTH)
            )
        return " ".join(tokens[:token_count])
```

- [ ] **Step 6: 实现 `scripts/aiinfra/determinism.py`（本任务只做核心函数，CLI 在 Task 19）**

```python
"""Repeat-sampled determinism measurement: unique output count and reproduction rate."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

import numpy as np

from scripts.aiinfra.backends.base import Backend, GenerationRequest
from scripts.aiinfra.config import WorkloadConfig


# One discarded warm-up call per cell, matching experiments/week18/kh_solver_timing
# ("warmups_per_group": 1). Its latency and its digest are both dropped: a cold-start
# difference belongs to the loading path, not to inference nondeterminism.
WARMUP_CALLS = 1


def digest_output(text: str) -> str:
    """Digest of the measured sequence. The unit is one batch position, not the batch."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _median_iqr(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return (
        float(np.median(array)),
        float(np.percentile(array, 75) - np.percentile(array, 25)),
    )


def measure_cells(backend: Backend, config: WorkloadConfig) -> list[dict[str, Any]]:
    """One cell per batch size; each cell repeats the same request `config.repeats` times.

    The measured unit is batch position 0, so batch size is the only variable that moves
    between cells. Both the unique-output count (the headline statistic) and the
    reproduction rate (the fallback when the phenomenon is intermittent) are reported.
    Each cell discards WARMUP_CALLS leading calls before counting.
    """
    cells: list[dict[str, Any]] = []
    for batch_size in config.batch_sizes:
        digests: list[str] = []
        latencies: list[float] = []
        request = GenerationRequest(
            prompt=config.prompt,
            batch_size=batch_size,
            max_new_tokens=config.max_new_tokens,
            seed=config.seed,
            dtype=config.dtype,
        )
        for _warmup in range(WARMUP_CALLS):
            backend.generate(request)
        for _repeat in range(config.repeats):
            result = backend.generate(request)
            digests.append(digest_output(result.texts[0]))
            latencies.append(result.latency_s)
        median, iqr = _median_iqr(latencies)
        modal_count = Counter(digests).most_common(1)[0][1]
        cells.append(
            {
                "cell_id": f"batch_size={batch_size}",
                "axes": {"batch_size": batch_size},
                "repeats": config.repeats,
                "unique_output_count": len(set(digests)),
                "reproduction_rate": modal_count / config.repeats,
                "output_digests": digests,
                "latency_median_s": median,
                "latency_iqr_s": iqr,
            }
        )
    return cells
```

- [ ] **Step 7: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_determinism.py -q
```
Expected: 全部 PASS

- [ ] **Step 8: 提交**

```bash
git add scripts/aiinfra/backends scripts/aiinfra/determinism.py tests/py/test_aiinfra_determinism.py
git commit -m "feat(aiinfra): add the backend interface, a torch-free fake backend, and repeat measurement" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: 负载入口与端到端假负载冒烟（步骤 1 Gate 2 与 Gate 4）

**Files:**
- Create: `scripts/aiinfra/run_workload.py`
- Create: `configs/aiinfra/smoke/fake_workload.json`（matrix）、
  `configs/aiinfra/smoke/fake_workload_run.json`（负载配置）
- Test: `tests/py/test_aiinfra_harness_contract.py`

**Interfaces:**
- Consumes: `config.load_workload_config`、`config.load_model_pins`、`config.resolve_model`、
  `backends.base.get_backend`、`determinism.measure_cells`、`result_schema.build_workload_result`
- Produces:
  - `run_workload.RESULT_FILENAME == "workload_result.json"`
  - `run_workload.main(argv: list[str] | None = None) -> int`
  - stderr 契约：成功发 `[run-status] status=success kind=workload completed=<n> expected=<n>`；
    失败发 `[run-status] status=failed reason=<FailureCategory 值>` 并返回非 0
  - 结果文件写在**配置文件所在目录**（即 run 目录），不需要任何路径参数

- [ ] **Step 1: 写失败测试**

追加到 `tests/py/test_aiinfra_harness_contract.py`：

```python
def _workload_config(tmp_path: Path, **overrides) -> Path:
    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 8,
        "repeats": 3,
        "batch_sizes": [1, 4],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def _matrix(tmp_path: Path, source_config: Path) -> dict:
    return {
        "experiment": "pytest-aiinfra",
        "runs": [
            {
                "name": "fake-workload",
                "binary": sys.executable,
                "arguments": ["scripts/aiinfra/run_workload.py"],
                "config": str(source_config),
                "config_filename": "config.json",
                "output_file": "workload_result.json",
                "artifact_kind": "workload_result",
            }
        ],
    }


def test_fake_workload_runs_end_to_end_through_run_matrix(tmp_path: Path) -> None:
    from scripts import run_matrix

    source = _workload_config(tmp_path)
    run = run_matrix.normalise_run(
        _matrix(tmp_path, source)["runs"][0], output_root=tmp_path / "out"
    )
    metadata = run_matrix.run_one(run, experiment="pytest-aiinfra")

    assert metadata["status"] == "success"
    assert metadata["completion"] == {"kind": "workload", "completed": 2, "expected": 2}
    assert metadata["failure"] is None

    result = json.loads((run.run_dir / "workload_result.json").read_text(encoding="utf-8"))
    assert result["schema"] == {"name": "aiinfra.workload-result", "version": 1}
    assert [cell["cell_id"] for cell in result["cells"]] == ["batch_size=1", "batch_size=4"]


@pytest.mark.parametrize(
    ("fault", "category"),
    (
        ("resource_exhausted", "resource_exhausted"),
        ("unsupported_capability", "unsupported_capability"),
    ),
)
def test_injected_backend_faults_reach_the_run_record(
    tmp_path: Path, fault: str, category: str
) -> None:
    from scripts import run_matrix

    source = _workload_config(tmp_path, options={"fault": fault})
    run = run_matrix.normalise_run(
        _matrix(tmp_path, source)["runs"][0], output_root=tmp_path / "out"
    )

    with pytest.raises(RuntimeError, match=category):
        run_matrix.run_one(run, experiment="pytest-aiinfra")

    metadata = json.loads((run.run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["failure"]["category"] == category
    assert metadata["completion"] is None


def test_committed_smoke_matrix_agrees_with_the_result_filename() -> None:
    from scripts import run_matrix
    from scripts.aiinfra import run_workload

    repo_root = Path(__file__).resolve().parents[2]
    matrix = run_matrix.load_matrix(
        repo_root / "configs" / "aiinfra" / "smoke" / "fake_workload.json"
    )
    for raw in matrix["runs"]:
        assert raw["output_file"] == run_workload.RESULT_FILENAME
        assert raw["artifact_kind"] == "workload_result"
        assert (repo_root / raw["config"]).is_file()
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k "workload or smoke"
```
Expected: FAIL — 找不到 `scripts/aiinfra/run_workload.py`

- [ ] **Step 3: 实现 `scripts/aiinfra/run_workload.py`**

```python
#!/usr/bin/env python3
"""Matrix entry point for aiinfra workloads.

Reads one workload configuration, runs it through the requested backend, writes a
validated `aiinfra.workload-result` document beside that configuration, and reports the
structured run status the shared harness parses.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.aiinfra import determinism, environment, result_schema
from scripts.aiinfra.backends.base import WorkloadFailure, get_backend
from scripts.aiinfra.config import load_model_pins, load_workload_config, resolve_model
from scripts.harness.contracts import FailureCategory


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PINS = REPO_ROOT / "configs" / "aiinfra" / "models.json"
RESULT_FILENAME = "workload_result.json"
WORKLOADS = {"determinism"}


def _fail(category: str, message: str) -> int:
    print(f"[run-status] status=failed reason={category}", file=sys.stderr)
    print(f"[error] {message}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path, help="Materialised workload configuration")
    args = parser.parse_args(argv)

    run_dir = args.config.resolve().parent
    try:
        config = load_workload_config(args.config)
        if config.workload not in WORKLOADS:
            raise WorkloadFailure(
                FailureCategory.CONFIGURATION.value,
                f"unknown workload {config.workload!r}; known: {sorted(WORKLOADS)}",
            )
        model = resolve_model(config, load_model_pins(MODEL_PINS))
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except ValueError as exc:
        return _fail(FailureCategory.CONFIGURATION.value, str(exc))

    try:
        backend = get_backend(config.backend, model=model, options=config.options)
        cells = determinism.measure_cells(backend, config)
    except WorkloadFailure as exc:
        return _fail(exc.category, str(exc))
    except MemoryError as exc:
        return _fail(FailureCategory.RESOURCE_EXHAUSTED.value, f"MemoryError: {exc}")

    document = result_schema.build_workload_result(
        workload=config.workload,
        backend=backend.describe(),
        model=model,
        environment=environment.probe(),
        cells=cells,
        completed=len(cells),
        expected=len(config.batch_sizes),
    )
    try:
        result_schema.validate_workload_result(document)
    except ValueError as exc:
        return _fail(FailureCategory.SCHEMA.value, str(exc))

    (run_dir / RESULT_FILENAME).write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"[run-status] status=success kind=workload "
        f"completed={len(cells)} expected={len(config.batch_sizes)}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 写 `configs/aiinfra/smoke/fake_workload_run.json`**

```json
{
  "schema": {"name": "aiinfra.workload-config", "version": 1},
  "workload": "determinism",
  "backend": "fake",
  "model": "fake-tiny",
  "dtype": "float32",
  "prompt": "Explain why floating-point addition is not associative.",
  "max_new_tokens": 32,
  "repeats": 5,
  "batch_sizes": [1, 8, 32],
  "seed": 0,
  "decode": "greedy",
  "options": {"nondeterminism": "none"}
}
```

- [ ] **Step 5: 写 `configs/aiinfra/smoke/fake_workload.json`**

```json
{
  "experiment": "aiinfra-smoke-fake-workload",
  "output_root": "experiments/aiinfra/smoke/fake_workload",
  "runs": [
    {
      "name": "fake-deterministic",
      "binary": "python",
      "arguments": ["scripts/aiinfra/run_workload.py"],
      "config": "configs/aiinfra/smoke/fake_workload_run.json",
      "config_filename": "config.json",
      "output_file": "workload_result.json",
      "artifact_kind": "workload_result"
    }
  ]
}
```

> 这个矩阵**只放会成功的格子**。`run_matrix.run_one` 在第一个失败的 run 上就 `raise RuntimeError`
> 并中止整个矩阵（`scripts/run_matrix.py:run_one` 末尾），所以"预期会失败的格子"不能放进
> 通用矩阵，必须由包专属驱动脚本驱动 —— 这正是 Task 20 的做法。见 §Review R-7。
>
> `"binary": "python"` 依赖 `python` 在 PATH 上解析到项目解释器（本机为
> `C:\Users\tangy\AppData\Local\Programs\Python\Python312\python.exe`）。`docs/INDEX.md` §8
> 记录过 Microsoft Store 的 `python` stub 会劫持 PATH；跑之前先 `python -c "import sys; print(sys.executable)"`
> 确认。pytest 里的等价用例用 `sys.executable`，不受此影响。

- [ ] **Step 6: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q
```
Expected: 全部 PASS

- [ ] **Step 7: 手动跑通 spec §8 的第 2 条验证命令**

```bash
python scripts/run_matrix.py configs/aiinfra/smoke/fake_workload.json
```
Expected: stdout 打印 summary JSON，`runs[0].status == "success"`，
`runs[0].completion == {"kind": "workload", "completed": 3, "expected": 3}`；
`experiments/aiinfra/smoke/fake_workload/runs/fake-deterministic/` 下有
`config.json`、`workload_result.json`、`metadata.json`、`stdout.txt`、`stderr.txt`。

- [ ] **Step 8: 提交（注意 `experiments/` 被 gitignore，冒烟产物不提交）**

```bash
git add scripts/aiinfra/run_workload.py configs/aiinfra/smoke tests/py/test_aiinfra_harness_contract.py
git commit -m "feat(aiinfra): add the workload matrix entry point and a fake-workload smoke matrix" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: 让证据包清单接受 `aiinfra` 报告 id

**为什么需要**：`scripts/harness/experiment_manifest.py:104` 现在写死
`if data.get("report") != "report2"`。`PLAN.md` §8 的端到端判据要求
`experiments/aiinfra/` 下每个证据包都能通过这个校验器 —— 不放宽就永远过不了。

**Files:**
- Modify: `scripts/harness/experiment_manifest.py`
- Test: `tests/py/test_experiment_manifests.py`

**Interfaces:**
- Produces: `experiment_manifest.REPORTS == {"report2", "aiinfra"}`；未知 `report` 值仍然报错

- [ ] **Step 1: 写失败测试**

追加到 `tests/py/test_experiment_manifests.py`：

```python
def test_aiinfra_report_id_is_accepted(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["report"] = "aiinfra"
    data["id"] = "aiinfra-test"
    _write_manifest(path, data)

    assert validate_manifest(path, tmp_path) == []


def test_unknown_report_id_is_still_rejected(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["report"] = "report9"
    _write_manifest(path, data)

    assert any("report" in error for error in validate_manifest(path, tmp_path))
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_experiment_manifests.py -q -k "aiinfra or unknown_report"
```
Expected: FAIL — `assert ["report must equal 'report2'"] == []`

- [ ] **Step 3: 最小实现**

在 `SCHEMA` 常量下面加：

```python
REPORTS = {"report2", "aiinfra"}
```

把

```python
    if data.get("report") != "report2":
        errors.append("report must equal 'report2'")
```
换成
```python
    if data.get("report") not in REPORTS:
        errors.append(f"report must be one of {sorted(REPORTS)}")
```

- [ ] **Step 4: 跑测试确认通过**

```bash
python -m pytest tests/py/test_experiment_manifests.py -q
```
Expected: 全部 PASS（包括 14 个已提交 report2 清单的校验）

- [ ] **Step 5: 提交**

```bash
git add scripts/harness/experiment_manifest.py tests/py/test_experiment_manifests.py
git commit -m "feat(harness): accept aiinfra experiment manifests alongside report2" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: 步骤 1 收尾验收与文档同步

**Files:**
- Modify: `docs/HARNESS.md`（Run Matrix Schema、Run Contract、Experiment Manifests 三节）
- Modify: `scripts/README.md`（Canonical Entry Points 加一行）
- Modify: `docs/INDEX.md`（§7 把步骤 1 从 planned 改为 delivered，并链到本计划）

**Interfaces:**
- Consumes: Task 1–9 的全部产出
- Produces: `PLAN.md` 步骤 1 的四条 Gate 全部有证据

- [ ] **Step 1: Gate 1 — 全量回归 + 旧命令逐字相同**

```bash
python -m pytest tests/py -q 2>&1 | tail -2
```
Expected: `skipped` 数仍为 **25**，`passed` **≥ 463**（新增的 aiinfra 测试计入 passed）。
若 skipped 变了，说明动到了别的东西，停下来查。

```bash
python -m pytest tests/py/test_harness_scripts.py tests/py/test_harness_runner.py tests/py/test_application_status_contract.py -q
```
Expected: 全部 PASS。

- [ ] **Step 2: Gate 2 — 假负载走通新路径并产出通过校验的新鲜 JSON**

```bash
rm -rf experiments/aiinfra/smoke
python scripts/run_matrix.py configs/aiinfra/smoke/fake_workload.json > /dev/null
python -c "import json,sys; m=json.load(open('experiments/aiinfra/smoke/fake_workload/matrix_summary.json')); r=m['runs'][0]; print(r['status'], r['completion'])"
```
Expected: `success {'kind': 'workload', 'completed': 3, 'expected': 3}`

- [ ] **Step 3: Gate 3 — 未知 `artifact_kind` fail-closed**

```bash
python -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from scripts import run_matrix
try:
    run_matrix.normalise_run({'name':'x','binary':'b','config':'configs/aiinfra/smoke/fake_workload_run.json','output_file':'o.json','artifact_kind':'nope'}, output_root=Path('.'))
except ValueError as exc:
    print('rejected:', exc)
"
```
Expected: `rejected: run 'x' has an unknown artifact kind: nope`

- [ ] **Step 4: Gate 4 — 两类结构化失败都进 metadata**

```bash
python -m pytest tests/py/test_aiinfra_harness_contract.py -q -k injected_backend_faults -v
```
Expected: 两个参数化用例都 PASS。

- [ ] **Step 5: 更新 `docs/HARNESS.md`**

在 **Run Matrix Schema** 一节的最小 JSON 之后追加：

```markdown
Optional fields for non-HRSC workloads (all default to the historical behaviour, so an
existing matrix builds a byte-identical command):

| Field | Default | Meaning |
|---|---|---|
| `arguments` | `[]` | Tokens inserted between the binary and the materialised config |
| `config_filename` | `"config.cfg"` | Name of the materialised config inside the run directory. A non-`.cfg` name is copied verbatim and rejects `extra_cfg` overrides. |
| `artifact_kind` | `"hrsc_binary"` | Validator applied to `output_file`; an unknown kind is rejected when the matrix is normalised. |
```

在 **Run Contract** 一节末尾追加：

```markdown
Workloads that are not time-stepped solvers report completion with
`[run-status] status=success kind=workload completed=<n> expected=<n>`. A line without a
`kind` token keeps the solver contract (`final_time`, `target_time`, `steps`) unchanged.
`status=failed reason=<category>` must name a member of `FailureCategory`; anything else
is recorded as `schema_error` rather than passed through.
```

在 **Experiment Manifests And Retention** 一节，把 "Report 2 experiment lifecycle manifests"
一句改为 "Experiment lifecycle manifests (`report` is `report2` or `aiinfra`)"。

- [ ] **Step 6: 更新 `scripts/README.md` 与 `docs/INDEX.md`**

`scripts/README.md` 的 Canonical Entry Points 表加两行：

```markdown
| Run (LLM workload) | `aiinfra/run_workload.py` | Matrix entry point for workload family 2; writes a validated `workload_result.json` beside its config. |
| Probe (environment) | `aiinfra/environment.py` | Read-only device/toolchain probe. Installs nothing, downloads nothing. |
```

`docs/INDEX.md` §7 第 1 条 "Additive generalisation of the harness" 后面加
`**[delivered]**`，并在该节开头加一行：
`Local execution plan: [`aiinfra/plans/2026-08-25-local-core-steps-0-3.md`](aiinfra/plans/2026-08-25-local-core-steps-0-3.md).`

- [ ] **Step 7: 提交**

```bash
git add docs/HARNESS.md docs/INDEX.md scripts/README.md
git commit -m "docs: record the additive workload contract in the harness guide" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## 阶段 C — 步骤 2：根 README 与数值回归 CI

### Task 11: 根 `README.md`（英文，数字全部来自已提交的 `summary.json`）

**Files:**
- Create: `README.md`（仓库根，目前没有）
- Create: `tests/py/test_root_readme.py`
- Reuse: `experiments/week20/gpu_fma_contraction/figures/`（若已有图）或
  `experiments/week18/report2_publication_figures/` 里的一张已提交 PNG

**Interfaces:**
- Consumes: `experiments/week20/gpu_fma_contraction/summary.json`、
  `experiments/week21/euler_openmp_thread_axis/summary.json`
- Produces: 一个测试可验证的 README —— README 里出现的每个数字都必须能在
  committed summary 里找到同值

**约束（spec 步骤 2 + `docs/INDEX.md` §9）**：一图 + 2–3 个归一化数字 + 三个链接，零形容词；
一段说清两个负载族的关系。**任何数字都不许手抄**，必须由 Step 1 的脚本从 summary 里取出来再写进
README，且由测试锁住。

**已核对可用的数字（本计划撰写时从 committed summary 直接读出）**

| 事实 | 来源 |
|---|---|
| `--fmad=false` 的 4 个匹配对全部 `ulp_max = 0`、`bitwise_identical = true` | `week20/gpu_fma_contraction/summary.json` |
| 恢复 `--fmad=true` 后 OT 256² fp32 的 ρ `L∞ = 2.0742416381835938e-05` | 同上 |
| 恢复 `--fmad=true` 后 Brio–Wu 800 fp32 的 ρ `L∞ = 2.2649765014648438e-06` | 同上 |
| Euler OpenMP 1/2/4/8 线程全部 `bitwise identical`，8 线程相对 1 线程 4.79×(fp64) | `week21/euler_openmp_thread_axis/summary.json` |

**不要写进 README 的一句话**：`PLAN.md` §1 的"恢复编译器默认值造成的位移，比把工作精度砍半还大"。
已核对：没有任何 committed summary 支持这个形式的比较（跨精度无法定义 ULP；能拿到的两个 L∞
分别来自 OT 与 KH 两个不同算例，是混杂比较）。详见 §Review R-8。

- [ ] **Step 1: 先把数字抽出来，确认它们真的存在**

```bash
python - <<'PY'
import json
fma = json.load(open("experiments/week20/gpu_fma_contraction/summary.json"))
off = [r for r in fma["rows"] if r["fma_contraction"] == "off"]
on = {(r["case"], r["precision"]): r for r in fma["rows"] if r["fma_contraction"] == "on"}
print("fmad=false pairs:", len(off), "all bitwise:", all(r["bitwise_identical"] for r in off))
print("OT fp32 rho Linf:", on[("orszag_tang_2d", "float")]["rho_linf_abs"])
print("BW fp32 rho Linf:", on[("brio_wu_1d", "float")]["rho_linf_abs"])
omp = json.load(open("experiments/week21/euler_openmp_thread_axis/summary.json"))
print("omp all bitwise:", omp["all_thread_counts_bitwise_identical"])
PY
```
Expected:
```
fmad=false pairs: 4 all bitwise: True
OT fp32 rho Linf: 2.0742416381835938e-05
BW fp32 rho Linf: 2.2649765014648438e-06
omp all bitwise: True
```

- [ ] **Step 2: 写失败测试 `tests/py/test_root_readme.py`**

```python
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def test_readme_exists_and_links_the_three_entry_points() -> None:
    text = _readme()
    for link in ("docs/INDEX.md", "docs/HARNESS.md", "docs/aiinfra/PLAN.md"):
        assert link in text, f"root README must link {link}"


def test_readme_numbers_match_the_committed_summaries() -> None:
    text = _readme()
    fma = json.loads(
        (REPO_ROOT / "experiments/week20/gpu_fma_contraction/summary.json").read_text(
            encoding="utf-8"
        )
    )
    rows = {(r["case"], r["precision"]): r for r in fma["rows"] if r["fma_contraction"] == "on"}
    ot = rows[("orszag_tang_2d", "float")]["rho_linf_abs"]
    brio = rows[("brio_wu_1d", "float")]["rho_linf_abs"]

    assert f"{ot:.3e}" in text
    assert f"{brio:.3e}" in text


def test_readme_does_not_repeat_the_unsupported_precision_comparison() -> None:
    """No committed summary supports 'larger than halving the working precision'."""
    assert not re.search(r"halv\w*\s+the\s+working\s+precision", _readme(), re.IGNORECASE)


def test_readme_states_the_distributed_scope_honestly() -> None:
    text = _readme().lower()
    assert "no multi-node gpu" in text
    assert "intra-node" in text


def test_readme_does_not_link_retired_directories() -> None:
    text = _readme()
    for retired in ("docs/superpowers/", "report1/", "report2/", "docs/week"):
        assert retired not in text, f"root README must not link retired path {retired}"
```

- [ ] **Step 3: 跑测试确认失败**

```bash
python -m pytest tests/py/test_root_readme.py -q
```
Expected: FAIL — `FileNotFoundError: README.md`

- [ ] **Step 4: 写 `README.md`**

```markdown
# floatpoint — a numerical qualification harness

Under which conditions is a computation bit-for-bit reproducible, which mechanisms break
that, and what does restoring it cost?

![CPU/GPU multiply-add contraction axis](experiments/week20/gpu_fma_contraction/figures/gpu_fma_contraction.png)

## Three measured results

- Matched CPU and GPU HLL outputs are bit-identical in all four measured pairs
  (`ulp_max = 0`) **only** when the device kernels are compiled `--fmad=false`.
- Restoring nvcc's default `--fmad=true` moves the fp32 density by
  `L-infinity = 2.074e-05` on Orszag--Tang 256^2 and `2.265e-06` on Brio--Wu 800.
- The Euler OpenMP sweep is bit-identical at 1, 2, 4 and 8 threads while really
  parallelising (4.79x at 8 threads over 1 thread, fp64).

Reproducibility is therefore a property of the build configuration, not of the hardware.

## Two workload families, one method

Family 1 is a CPU/CUDA compressible-Euler and ideal-MHD solver: a numerically sensitive
non-ML workload that produced the results above. Family 2 is LLM inference under PyTorch
and vLLM. They share one harness, one run-record schema and one failure taxonomy, so the
same determinism question is answered on two unrelated computations. Family 1 exists to
show the harness is not hard-coded to a Transformer; Family 2 exists to show the method is
not hard-coded to a solver.

## Scope

Distributed coverage stops at intra-node 2-GPU tensor parallelism plus multi-node CPU MPI.
No multi-node GPU, no RDMA or InfiniBand, no scaling curves beyond two devices, and no
distributed training framework.

## Where to go next

- [`docs/INDEX.md`](docs/INDEX.md) — architecture, compute resources, delivered evidence
- [`docs/HARNESS.md`](docs/HARNESS.md) — pipeline, run contract, manifests
- [`docs/aiinfra/PLAN.md`](docs/aiinfra/PLAN.md) — the Family 2 execution plan
```

> **图的处理**：若 `experiments/week20/gpu_fma_contraction/figures/` 下没有已提交 PNG，
> 就改用 `experiments/week18/report2_publication_figures/` 里任意一张**已提交**的 PNG，
> 并把 alt text 与 caption 改成那张图的实际内容。**不要为 README 现造一张图** ——
> 那会引入一个没有 provenance 的产物。先跑
> `git ls-files 'experiments/**/*.png' | head -20` 挑一张。

- [ ] **Step 5: 跑测试确认通过**

```bash
git ls-files 'experiments/**/*.png' | head -20
python -m pytest tests/py/test_root_readme.py -q
```
Expected: 全部 PASS，且 README 里引用的 PNG 出现在 `git ls-files` 的输出里。

- [ ] **Step 6: 提交**

```bash
git add README.md tests/py/test_root_readme.py
git commit -m "docs: add a root README whose numbers are locked to committed summaries" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 12: CI 之一 —— pytest 门禁

**Files:**
- Create: `.github/workflows/tests.yml`

**Interfaces:**
- Consumes: `pytest.ini`（Task 0 已跟踪）
- Produces: 每次 push/PR 都跑 `pytest tests/py`

**注意**：CI runner 上没有 `scikit-image`、没有编译好的求解器，所以 skip 数会与本机不同。
门禁只断言 **0 failed**，不断言具体的 passed/skipped 数字 —— 把机器相关的数字写进 CI 会变成
定时炸弹。

- [ ] **Step 1: 写工作流**

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install runtime dependencies
        run: python -m pip install --upgrade pip numpy matplotlib pytest
      - name: Run the Python test suite
        run: python -m pytest tests/py -q
```

- [ ] **Step 2: 本地先确认依赖清单是够的**

```bash
python -c "import numpy, matplotlib, pytest; print('ok')"
python -m pytest tests/py -q 2>&1 | tail -2
```
Expected: `ok`，然后 `0 failed`。
若本机跑测试还需要别的第三方包，把它加进上面的 `pip install` 行 —— 逐个加，不要写
`pip install -r` 指向一个不存在的 requirements 文件。

- [ ] **Step 3: 提交并观察第一次 CI**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: run the Python test suite on push and pull request" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push
gh run watch
```
Expected: 绿。若红，**先看 skip 是不是变成了 fail**（例如某个测试在 Linux 上路径分隔符不同），
逐个修，不要用 `continue-on-error` 掩盖。

---

### Task 13: CI 之二 —— 数值回归门禁（Brio–Wu 1D，n=10）

**Files:**
- Create: `.github/workflows/numerical-regression.yml`
- Create: `scripts/regression/ci_numerical_gate.py`
- Create: `tests/cases/brio_wu_1d/brio_wu_n10.cfg`
- Create: `experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json`（**需 `git add -f`**）
- Test: `tests/py/test_ci_numerical_gate.py`

**Interfaces:**
- Produces:
  - `ci_numerical_gate.compare(reference: dict, observed: dict) -> dict`
    → `{"max_rel_dev": float, "bitwise_identical": bool, "pass": bool}`
  - `ci_numerical_gate.main(argv) -> int`（0 = 通过，1 = 回归）

**门禁的两层，理由必须写进 workflow 注释**

| 层 | 判据 | 它能抓什么 |
|---|---|---|
| A：同机器重复位级一致 | 同一个二进制跑两次，`ulp_max == 0` | 新引入的不确定性（线程、未初始化内存、hash 序） |
| B：跨机器容差 | 与已提交参考的 ρ 最大相对偏差 ≤ `TOLERANCE` | 真实的数值改动 |

**为什么 B 不能用位级判据**：CI runner 是 GCC/Linux/x86-64，已提交证据是本机 MSVC 19.51。
换编译器换 CPU 后位级一致本来就不成立，硬拿位级当门禁会 100% 假阳性。
`TOLERANCE` **必须实测再写死**，不许拍脑袋（做法见 Step 5）。

**为什么不在这个门禁里跑 Verificarlo**：`experiments/report2_w16_verificarlo_findings/` 记录
MCA 参考后端比原生慢 **≈417×**（24.0 vs 0.0575 s/step）。放进 per-push CI 不可行。
精度位数（`precexp_aggregate.py` 的 `minimum_precision_bits`）比较放在同一个 workflow 的
`workflow_dispatch` 手动作业里，见 Step 7。详见 §Review R-9。

- [ ] **Step 1: 写 n=10 的算例配置 `tests/cases/brio_wu_1d/brio_wu_n10.cfg`**

```
# CI regression canary. Ten cells is not a physics result; it is a cheap, sensitive
# fingerprint of the update path. Physics claims use brio_wu.cfg (nx = 800).
test    = brio_wu
nx      = 10
xmin    = 0.0
xmax    = 1.0
x0      = 0.5
gamma   = 2.0
cfl     = 0.4
t_end   = 0.1
bc      = outflow
```

- [ ] **Step 2: 写失败测试 `tests/py/test_ci_numerical_gate.py`**

```python
from __future__ import annotations

import pytest


def _reference() -> dict:
    return {
        "case": "brio_wu_n10",
        "nx": 10,
        "precision": "double",
        "tolerance_rel": 1e-9,
        "rho": [1.0, 1.0, 1.0, 0.9, 0.6, 0.4, 0.2, 0.125, 0.125, 0.125],
    }


def test_identical_values_pass_both_layers() -> None:
    from scripts.regression import ci_numerical_gate

    reference = _reference()
    verdict = ci_numerical_gate.compare(
        reference, {"rho": list(reference["rho"]), "rho_repeat": list(reference["rho"])}
    )

    assert verdict["bitwise_identical"] is True
    assert verdict["max_rel_dev"] == 0.0
    assert verdict["pass"] is True


def test_a_repeat_that_differs_fails_even_within_tolerance() -> None:
    from scripts.regression import ci_numerical_gate

    reference = _reference()
    observed = list(reference["rho"])
    repeat = list(reference["rho"])
    repeat[0] = repeat[0] * (1.0 + 1e-15)
    verdict = ci_numerical_gate.compare(reference, {"rho": observed, "rho_repeat": repeat})

    assert verdict["bitwise_identical"] is False
    assert verdict["pass"] is False


def test_a_deviation_beyond_tolerance_fails() -> None:
    from scripts.regression import ci_numerical_gate

    reference = _reference()
    observed = list(reference["rho"])
    observed[4] = observed[4] * 1.01
    verdict = ci_numerical_gate.compare(
        reference, {"rho": observed, "rho_repeat": list(observed)}
    )

    assert verdict["max_rel_dev"] == pytest.approx(0.01, rel=1e-6)
    assert verdict["pass"] is False


def test_a_deviation_inside_tolerance_passes() -> None:
    from scripts.regression import ci_numerical_gate

    reference = _reference()
    observed = list(reference["rho"])
    observed[4] = observed[4] * (1.0 + 1e-12)
    verdict = ci_numerical_gate.compare(
        reference, {"rho": observed, "rho_repeat": list(observed)}
    )

    assert verdict["pass"] is True


def test_shape_mismatch_is_a_failure_not_a_crash() -> None:
    from scripts.regression import ci_numerical_gate

    verdict = ci_numerical_gate.compare(_reference(), {"rho": [1.0], "rho_repeat": [1.0]})

    assert verdict["pass"] is False
    assert "length" in verdict["reason"]
```

- [ ] **Step 3: 跑测试确认失败**

```bash
python -m pytest tests/py/test_ci_numerical_gate.py -q
```
Expected: FAIL — `ImportError: cannot import name 'ci_numerical_gate'`

- [ ] **Step 4: 实现 `scripts/regression/ci_numerical_gate.py`**

```python
#!/usr/bin/env python3
"""Two-layer numerical regression gate for CI.

Layer A: the same binary run twice must agree bit for bit on this machine.
Layer B: the density profile must stay within a pre-declared relative tolerance of the
committed reference. Layer B is a tolerance and not a bitwise check because CI runs a
different compiler and CPU from the machine that produced the reference.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from io_helper import read_binary


IDX_RHO = 0


def compare(reference: dict, observed: dict) -> dict:
    """Judge one observation against the committed reference. Never raises."""
    expected = np.asarray(reference["rho"], dtype=np.float64)
    first = np.asarray(observed["rho"], dtype=np.float64)
    repeat = np.asarray(observed["rho_repeat"], dtype=np.float64)

    if first.shape != expected.shape or repeat.shape != expected.shape:
        return {
            "max_rel_dev": float("inf"),
            "bitwise_identical": False,
            "pass": False,
            "reason": (
                f"length mismatch: reference {expected.shape}, "
                f"observed {first.shape}, repeat {repeat.shape}"
            ),
        }

    bitwise = bool(np.array_equal(first.view(np.uint64), repeat.view(np.uint64)))
    denominator = np.where(expected == 0.0, 1.0, np.abs(expected))
    max_rel_dev = float(np.max(np.abs(first - expected) / denominator))
    tolerance = float(reference["tolerance_rel"])
    within = max_rel_dev <= tolerance
    return {
        "max_rel_dev": max_rel_dev,
        "bitwise_identical": bitwise,
        "pass": bool(bitwise and within),
        "reason": (
            "ok"
            if bitwise and within
            else (
                "repeat run is not bit-identical"
                if not bitwise
                else f"max relative deviation {max_rel_dev:.3e} exceeds {tolerance:.3e}"
            )
        ),
    }


def _run(binary: Path, config: Path, output: Path) -> list[float]:
    output.parent.mkdir(parents=True, exist_ok=True)
    text = config.read_text(encoding="utf-8")
    generated = output.parent / f"{output.stem}.cfg"
    generated.write_text(
        text + f"\noutput_format = binary\noutput_file = {output}\n", encoding="utf-8"
    )
    subprocess.run([str(binary), str(generated)], check=True)
    _header, grid = read_binary(output)
    return [float(value) for value in grid[0, :, IDX_RHO]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, default=Path("ci-gate"))
    parser.add_argument(
        "--write-reference",
        action="store_true",
        help="Write the observed profile to --reference instead of judging it",
    )
    args = parser.parse_args(argv)

    first = _run(args.binary, args.config, args.work_dir / "run_a.bin")
    repeat = _run(args.binary, args.config, args.work_dir / "run_b.bin")

    if args.write_reference:
        args.reference.parent.mkdir(parents=True, exist_ok=True)
        args.reference.write_text(
            json.dumps(
                {
                    "case": args.config.stem,
                    "nx": len(first),
                    "precision": "double",
                    "tolerance_rel": 0.0,
                    "rho": first,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"wrote": str(args.reference), "nx": len(first)}))
        return 0

    reference = json.loads(args.reference.read_text(encoding="utf-8"))
    verdict = compare(reference, {"rho": first, "rho_repeat": repeat})
    json.dump(verdict, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if verdict["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: 生成参考并**实测**容差（不许拍脑袋）**

先在本机（MSVC）生成参考：

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
cmake --build build-double
python scripts/regression/ci_numerical_gate.py --binary build-double/hrsc_mhd \
  --config tests/cases/brio_wu_1d/brio_wu_n10.cfg \
  --reference experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json \
  --work-dir .pytest_tmp/ci_gate --write-reference
```

再在一台 **Linux/GCC** 上跑同一条命令（WSL 里 `cmake -B build-double-gcc ...`，或临时把
workflow 改成 `--write-reference` 跑一次并把结果贴出来），记下 `max_rel_dev`。
把 `tolerance_rel` 设为 **实测值的 10 倍**，向上取到一位有效数字，并把这句话写进参考 JSON 的
`"tolerance_basis"` 字段：

```json
"tolerance_basis": "10x the maximum relative density deviation observed between MSVC 19.51 (reference machine) and GCC on ubuntu-latest, measured 2026-08-__."
```
（`compare` 忽略未知字段，加这个字段不需要改代码。）

**若 Linux 编译不过**：这是必须记录的环境事实，不是可以跳过的一步。把编译错误抄进
`docs/aiinfra/plans/` 下的一条说明，把这个 job 降级为
`continue-on-error: true` 并在 workflow 里注明原因，**不要删掉它假装没这回事**。

- [ ] **Step 6: 验证门禁真的会报警（spec 步骤 2 的 "假阳性 0"）**

注入一个已知回归，确认门禁变红，然后**立刻还原**：

```bash
python - <<'PY'
import json, pathlib
p = pathlib.Path("experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json")
d = json.loads(p.read_text())
d["rho"][4] *= 1.05          # 5% perturbation stands in for a real regression
p.with_suffix(".perturbed.json").write_text(json.dumps(d, indent=2))
PY
python scripts/regression/ci_numerical_gate.py --binary build-double/hrsc_mhd \
  --config tests/cases/brio_wu_1d/brio_wu_n10.cfg \
  --reference experiments/aiinfra/ci_baseline/brio_wu_n10_reference.perturbed.json \
  --work-dir .pytest_tmp/ci_gate; echo "exit=$?"
rm experiments/aiinfra/ci_baseline/brio_wu_n10_reference.perturbed.json
```
Expected: 打印 `"pass": false`，`exit=1`。

然后连跑 3 次未扰动的门禁，确认 3 次都 `exit=0`（假阳性 0）：

```bash
for i in 1 2 3; do
  python scripts/regression/ci_numerical_gate.py --binary build-double/hrsc_mhd \
    --config tests/cases/brio_wu_1d/brio_wu_n10.cfg \
    --reference experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json \
    --work-dir .pytest_tmp/ci_gate > /dev/null; echo "run $i exit=$?"
done
```
Expected: 三行都是 `exit=0`。

- [ ] **Step 7: 写 `.github/workflows/numerical-regression.yml`**

```yaml
name: numerical-regression

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  brio-wu-canary:
    # Layer A (same-machine bitwise) plus Layer B (cross-machine tolerance). Layer B is a
    # tolerance because this runner uses GCC on x86-64 Linux while the committed reference
    # was produced by MSVC 19.51 on the development workstation.
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: python -m pip install --upgrade pip numpy
      - name: Configure and build the double-precision MHD solver
        run: |
          cmake -B build-double -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release
          cmake --build build-double --target hrsc_mhd --parallel
      - name: Run the numerical regression gate
        run: |
          python scripts/regression/ci_numerical_gate.py \
            --binary build-double/hrsc_mhd \
            --config tests/cases/brio_wu_1d/brio_wu_n10.cfg \
            --reference experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json \
            --work-dir ci-gate

  verificarlo-precision-bits:
    # The MCA reference backend is about 417x slower than native
    # (experiments/report2_w16_verificarlo_findings). It cannot run per push, so this job
    # is manual only and compares precexp_aggregate's minimum_precision_bits with the
    # archived baseline.
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Populated in a follow-up once a Verificarlo image digest is pinned."
```

> 第二个 job 目前只有一个占位命令，因为 pin 哪个 Verificarlo 镜像 digest 属于 ADR-13 的
> 待办，本计划范围内还没定。**它不会在任何 push 上运行**，所以不会造成假绿。
> 一旦 Task 14 确定了容器 digest，把它填上。

- [ ] **Step 8: 提交（注意参考 JSON 在 `experiments/` 下，需要 `-f`）**

```bash
git add .github/workflows/numerical-regression.yml scripts/regression/ci_numerical_gate.py \
        tests/cases/brio_wu_1d/brio_wu_n10.cfg tests/py/test_ci_numerical_gate.py
git add -f experiments/aiinfra/ci_baseline/brio_wu_n10_reference.json
git commit -m "ci: add a two-layer Brio-Wu numerical regression gate" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git push && gh run watch
```
Expected: 两个 workflow 都绿（`verificarlo-precision-bits` 被 `if` 跳过）。

---

## 阶段 D — 步骤 0：Spike（差异化的生死判定）

> **可以与阶段 B 并行启动**：Task 14 是纯下载与安装，墙钟 1–3 小时但不占人。
> 先把它挂上，再回去做 Task 1–8。Task 15 以后必须等 Task 14 完成。

### Task 14: WSL 执行环境、容器 digest 与模型 pin

**Files:**
- Create: `scripts/aiinfra/prepare_assets.py`
- Modify: `configs/aiinfra/models.json`（加入 Qwen 条目，revision 填**实测真值**）
- Create: `docs/aiinfra/ENVIRONMENT.md`（英文，记录实际装成了什么、没装成什么）
- Create: `experiments/aiinfra/env_probe_local/{summary.json,summary.md,manifest.json}`（需 `git add -f`）

**Interfaces:**
- Consumes: `environment.probe()`
- Produces:
  - 环境变量约定 `AIINFRA_CONTAINER_DIGEST`（跑在容器里时设，跑在 venv 里时留空 → 探针记 `"none"`）
  - `configs/aiinfra/models.json` 里 `qwen2.5-0.5b-instruct` 条目的**真实 revision sha**
  - `prepare_assets.download(model_key, pins, target: Path) -> dict`

**已核实的本地事实（本计划撰写时实测）**：WSL2 有 `Ubuntu` 发行版（当前 Stopped）；
Docker 29.5.3 可用；Windows 侧 `python` = 3.12.10（无 torch）；
`nvidia-smi` 报 RTX 5070 Laptop、8151 MiB、驱动 591.91。
`PLAN.md` §2.2 记录 WSL 内的 Python 是 3.14.4（装不上 torch），所以 WSL 里必须另建 3.12 环境。

- [ ] **Step 1: 决定执行载体，二选一，并把选择写进 `ENVIRONMENT.md`**

**首选（ADR-13 的目标形态）**：容器。

```bash
wsl -d Ubuntu -- docker run --rm --gpus all <image> nvidia-smi
wsl -d Ubuntu -- docker image inspect --format '{{index .RepoDigests 0}}' <image>
```
选一个官方 PyTorch CUDA 镜像，要求它在 `sm_120` 上跑得动。把 `RepoDigests` 记下来，
以后每次运行都 `export AIINFRA_CONTAINER_DIGEST=<digest>`。

**备选（容器在 sm_120 上跑不通时）**：WSL 内的 3.12 venv。

```bash
wsl -d Ubuntu -- bash -lc "sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv"
wsl -d Ubuntu -- bash -lc "python3.12 -m venv ~/aiinfra-venv && ~/aiinfra-venv/bin/pip install --upgrade pip"
```

**如果只能用备选**：这直接触发 ADR-13 的第二分支 —— 软件栈成为**显式实验轴**，
必须在 `ENVIRONMENT.md` 里写明"本地栈 ≠ 集群栈"，此后所有跨平面比较都要带这个标注。
**不要为了让叙事整齐而假装是同一个栈。**

- [ ] **Step 2: 装依赖，逐条记录版本与失败**

```bash
wsl -d Ubuntu -- bash -lc "~/aiinfra-venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cu124"
wsl -d Ubuntu -- bash -lc "~/aiinfra-venv/bin/pip install transformers accelerate huggingface_hub"
wsl -d Ubuntu -- bash -lc "~/aiinfra-venv/bin/pip install vllm"   # 允许失败
```

**vLLM 装不上是一个可接受的结局**（`sm_120` 是消费级 Blackwell，官方 wheel 支持面窄）。
装不上就原样抄下错误信息，spike 退化为 eager-only，vLLM 那一格在结果里记
`unsupported_capability` 而不是留空。（ADR-6 的同一条原则）

- [ ] **Step 3: 确认 GPU 在 WSL 里真的可用**

```bash
wsl -d Ubuntu -- bash -lc "~/aiinfra-venv/bin/python -c \"import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))\""
```
Expected: `... True NVIDIA GeForce RTX 5070 Laptop GPU (12, 0)`
若 `is_available()` 是 `False`，停在这里查驱动/WSL 直通，不要往下走。

- [ ] **Step 4: 解析模型 revision 的真值**

```bash
wsl -d Ubuntu -- bash -lc "~/aiinfra-venv/bin/python -c \"from huggingface_hub import HfApi; print(HfApi().model_info('Qwen/Qwen2.5-0.5B-Instruct').sha)\""
```
把打印出来的 40 位 sha 写进 `configs/aiinfra/models.json`：

```json
    "qwen2.5-0.5b-instruct": {
      "id": "Qwen/Qwen2.5-0.5B-Instruct",
      "revision": "<paste the 40-character sha printed above>",
      "source": "huggingface",
      "approx_weight_bytes": 1000000000
    }
```

> **不要凭空写一个 sha。** 本计划刻意没有预填 —— 编造的 pin 比没有 pin 更糟，
> 因为它看起来像证据。

- [ ] **Step 5: 实现 `scripts/aiinfra/prepare_assets.py`**

```python
#!/usr/bin/env python3
"""Fetch a pinned model snapshot. Downloads weights; performs no computation.

Download time is deliberately outside every headline timing (PLAN section 7).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.aiinfra.config import load_model_pins


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PINS = REPO_ROOT / "configs" / "aiinfra" / "models.json"


def download(model_key: str, pins: dict[str, dict[str, Any]], target: Path) -> dict[str, Any]:
    """Snapshot the pinned revision into *target* and report what landed there."""
    try:
        pin = pins[model_key]
    except KeyError as exc:
        raise ValueError(f"model {model_key!r} is not pinned in models.json") from exc
    if pin["source"] == "builtin":
        return {"model_key": model_key, "source": "builtin", "path": None, "files": 0}

    from huggingface_hub import snapshot_download

    path = snapshot_download(
        repo_id=str(pin["id"]),
        revision=str(pin["revision"]),
        local_dir=str(target),
    )
    files = sorted(p.name for p in Path(path).rglob("*") if p.is_file())
    return {
        "model_key": model_key,
        "source": pin["source"],
        "id": pin["id"],
        "revision": pin["revision"],
        "path": path,
        "files": len(files),
        "total_bytes": sum(p.stat().st_size for p in Path(path).rglob("*") if p.is_file()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model_key")
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args(argv)

    report = download(args.model_key, load_model_pins(MODEL_PINS), args.target)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: 下载权重（不计入任何计时）**

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && ~/aiinfra-venv/bin/python scripts/aiinfra/prepare_assets.py qwen2.5-0.5b-instruct --target ~/models/qwen2.5-0.5b-instruct"
```
Expected: 打印 `"revision"` 与 `"total_bytes"`（0.5B 约 1.0 GB 量级）。
**权重不进仓库** —— `~/models/` 在 WSL 家目录，不在工作树里。

- [ ] **Step 7: 产出环境证据包**

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && AIINFRA_CONTAINER_DIGEST=${DIGEST:-none} ~/aiinfra-venv/bin/python scripts/aiinfra/environment.py --json > experiments/aiinfra/env_probe_local/summary.json"
```

手写 `experiments/aiinfra/env_probe_local/summary.md`（英文），内容为：探针输出的关键行、
装成功/失败的包与原文错误、容器 digest 或"未用容器"的声明、
`claim_boundary`（"This packet records one workstation on one date; it is not a portability claim."）。

手写 `experiments/aiinfra/env_probe_local/manifest.json`：

```json
{
  "schema": {"name": "hrsc.experiment-manifest", "version": 1},
  "id": "aiinfra-env-probe-local",
  "report": "aiinfra",
  "lifecycle": "canonical",
  "purpose": "Record the local WSL execution environment, container digest and model pin that every step-0 and step-3 run record refers to.",
  "pipeline": {
    "config": ["configs/aiinfra/models.json"],
    "build": ["scripts/aiinfra/prepare_assets.py"],
    "run": ["scripts/aiinfra/environment.py"],
    "measure": ["scripts/aiinfra/environment.py"],
    "aggregate": ["experiments/aiinfra/env_probe_local/summary.json"],
    "plot": ["experiments/aiinfra/env_probe_local/summary.md"]
  },
  "evidence": [
    "experiments/aiinfra/env_probe_local/summary.md",
    "experiments/aiinfra/env_probe_local/summary.json"
  ],
  "retention": {
    "keep": ["manifest.json", "summary.*"],
    "transient": ["model weights (kept outside the tree under ~/models)"]
  },
  "provenance": {
    "notes": "Probe is read-only: it installs nothing and downloads nothing. Model weights are not committed; the pinned revision in configs/aiinfra/models.json is the authority."
  }
}
```

> `pipeline.plot` 这一格用 `summary.md` 顶上，因为环境探针没有图而校验器要求六个阶段都非空。
> 这是有意的：与其造一张没有意义的图，不如让 `plot` 指向人读的那份文档。见 §Review R-10。

- [ ] **Step 8: 校验证据包并提交**

```bash
python -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from scripts.harness.experiment_manifest import validate_manifest
print(validate_manifest(Path('experiments/aiinfra/env_probe_local/manifest.json'), Path('.')))
"
```
Expected: `[]`

```bash
git add configs/aiinfra/models.json scripts/aiinfra/prepare_assets.py docs/aiinfra/ENVIRONMENT.md
git add -f experiments/aiinfra/env_probe_local
git commit -m "feat(aiinfra): pin the local execution environment and the 0.5B model revision" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 15: PyTorch eager 与 vLLM 离线后端

**Files:**
- Create: `scripts/aiinfra/backends/torch_eager.py`、`scripts/aiinfra/backends/vllm_offline.py`
- Test: `tests/py/test_aiinfra_backends_capability.py`（新建）

**Interfaces:**
- Consumes: `backends.base.{GenerationRequest, GenerationResult, WorkloadFailure}`
- Produces: 两个满足 `Backend` 协议的类；**依赖缺失时抛
  `WorkloadFailure("unsupported_capability", ...)`，而不是 `ImportError`**；
  显存耗尽时抛 `WorkloadFailure("resource_exhausted", ...)`
- `describe()` 的 `effective_path` 必须来自**运行时实测**（参数真实 dtype、真实 device），
  不是配置里请求的值（ADR-6）

**不许做的事**：不要调用 `torch.use_deterministic_algorithms(True)`，不要设
`CUBLAS_WORKSPACE_CONFIG`。我们**在测量**不确定性，强行关掉它就把要测的东西抹掉了。
这些开关的当前状态要记进 `describe()`，不要改动。

- [ ] **Step 1: 写失败测试 `tests/py/test_aiinfra_backends_capability.py`**

这个测试**在没有 torch 的机器上也必须通过** —— 它断言的正是"缺依赖时给出结构化失败"。

```python
from __future__ import annotations

import builtins

import pytest


def _blocked(monkeypatch: pytest.MonkeyPatch, blocked: set[str]) -> None:
    real_import = builtins.__import__

    def guard(name, *args, **kwargs):
        if name.split(".")[0] in blocked:
            raise ImportError(f"blocked {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guard)


def test_torch_eager_without_torch_is_an_unsupported_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.aiinfra.backends.base import WorkloadFailure
    from scripts.aiinfra.backends.torch_eager import TorchEagerBackend

    _blocked(monkeypatch, {"torch", "transformers"})

    with pytest.raises(WorkloadFailure) as excinfo:
        TorchEagerBackend(
            model={"id": "Qwen/Qwen2.5-0.5B-Instruct", "revision": "x", "dtype": "float16"},
            options={},
        )

    assert excinfo.value.category == "unsupported_capability"
    assert "blocked" in str(excinfo.value)


def test_vllm_without_vllm_is_an_unsupported_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts.aiinfra.backends.base import WorkloadFailure
    from scripts.aiinfra.backends.vllm_offline import VllmOfflineBackend

    _blocked(monkeypatch, {"vllm"})

    with pytest.raises(WorkloadFailure) as excinfo:
        VllmOfflineBackend(
            model={"id": "Qwen/Qwen2.5-0.5B-Instruct", "revision": "x", "dtype": "float16"},
            options={},
        )

    assert excinfo.value.category == "unsupported_capability"


def test_registry_reaches_both_real_backends() -> None:
    """The registry must not silently fall back to fake when a real backend is asked for."""
    from scripts.aiinfra.backends import base

    for name in ("torch_eager", "vllm_offline"):
        with pytest.raises(base.WorkloadFailure) as excinfo:
            base.get_backend(
                name,
                model={"id": "nope", "revision": "nope", "dtype": "float16"},
                options={},
            )
        assert excinfo.value.category in {"unsupported_capability", "configuration_error"}
```

> 最后一个用例在**装了 torch 的机器上**会因为模型加载失败而抛别的东西。
> 实现时用 `revision="nope"` 触发的 repo 错误映射成 `configuration_error`，
> 这样两种机器上断言都成立。

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_backends_capability.py -q
```
Expected: FAIL — `ModuleNotFoundError: scripts.aiinfra.backends.torch_eager`

- [ ] **Step 3: 实现 `scripts/aiinfra/backends/torch_eager.py`**

```python
"""PyTorch eager backend: the fidelity reference (simplest semantics, fewest layers)."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from scripts.aiinfra.backends.base import (
    GenerationRequest,
    GenerationResult,
    WorkloadFailure,
)


_DTYPES = {"float32": "float32", "float16": "float16", "bfloat16": "bfloat16"}


class TorchEagerBackend:
    """Greedy generation through `transformers` with no determinism flags forced."""

    def __init__(self, *, model: Mapping[str, str], options: Mapping[str, Any]) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise WorkloadFailure(
                "unsupported_capability", f"torch_eager backend unavailable: {exc}"
            ) from exc

        self._torch = torch
        dtype_name = str(model.get("dtype", "float16"))
        if dtype_name not in _DTYPES:
            raise WorkloadFailure(
                "configuration_error", f"torch_eager cannot use dtype {dtype_name!r}"
            )
        self._device = str(options.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                model["id"], revision=model["revision"]
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                model["id"],
                revision=model["revision"],
                torch_dtype=getattr(torch, dtype_name),
            ).to(self._device)
        except Exception as exc:
            raise WorkloadFailure(
                "configuration_error", f"cannot load {model['id']}@{model['revision']}: {exc}"
            ) from exc
        self._model.eval()
        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

    def describe(self) -> dict[str, str]:
        torch = self._torch
        parameter = next(self._model.parameters())
        return {
            "name": "torch_eager",
            "version": str(torch.__version__),
            "requested_path": f"{self._model.config.torch_dtype}@{self._device}",
            "effective_path": f"{parameter.dtype}@{parameter.device.type}",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        torch = self._torch
        prompts = [request.prompt] * request.batch_size
        encoded = self._tokenizer(prompts, return_tensors="pt", padding=True).to(self._device)
        started = time.perf_counter()
        try:
            with torch.inference_mode():
                output = self._model.generate(
                    **encoded,
                    do_sample=False,
                    num_beams=1,
                    max_new_tokens=request.max_new_tokens,
                    pad_token_id=self._tokenizer.pad_token_id,
                )
            if self._device == "cuda":
                torch.cuda.synchronize()
        except torch.cuda.OutOfMemoryError as exc:
            raise WorkloadFailure(
                "resource_exhausted", f"CUDA OOM at batch_size={request.batch_size}: {exc}"
            ) from exc
        latency = time.perf_counter() - started
        generated = output[:, encoded["input_ids"].shape[1] :]
        texts = tuple(self._tokenizer.batch_decode(generated, skip_special_tokens=True))
        return GenerationResult(texts=texts, logits=None, latency_s=latency)
```

- [ ] **Step 4: 实现 `scripts/aiinfra/backends/vllm_offline.py`**

```python
"""vLLM offline backend: continuous batching and PagedAttention are the mechanisms under test."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

from scripts.aiinfra.backends.base import (
    GenerationRequest,
    GenerationResult,
    WorkloadFailure,
)


DEFAULT_GPU_MEMORY_UTILISATION = 0.80


class VllmOfflineBackend:
    """Greedy offline generation through vLLM's `LLM` entry point."""

    def __init__(self, *, model: Mapping[str, str], options: Mapping[str, Any]) -> None:
        try:
            import vllm
            from vllm import LLM
        except ImportError as exc:
            raise WorkloadFailure(
                "unsupported_capability", f"vllm_offline backend unavailable: {exc}"
            ) from exc

        self._vllm = vllm
        self._options = dict(options)
        try:
            self._llm = LLM(
                model=str(model["id"]),
                revision=str(model["revision"]),
                dtype=str(model.get("dtype", "float16")),
                gpu_memory_utilization=float(
                    options.get("gpu_memory_utilization", DEFAULT_GPU_MEMORY_UTILISATION)
                ),
                enforce_eager=bool(options.get("enforce_eager", False)),
                seed=int(options.get("seed", 0)),
            )
        except Exception as exc:
            category = (
                "resource_exhausted" if "out of memory" in str(exc).lower() else "configuration_error"
            )
            raise WorkloadFailure(category, f"cannot start vLLM for {model['id']}: {exc}") from exc

    def describe(self) -> dict[str, str]:
        config = self._llm.llm_engine.model_config
        return {
            "name": "vllm_offline",
            "version": str(self._vllm.__version__),
            "requested_path": f"dtype={self._options.get('dtype', 'float16')} "
            f"enforce_eager={self._options.get('enforce_eager', False)}",
            "effective_path": f"dtype={config.dtype} attention={type(self._llm.llm_engine).__name__}",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        from vllm import SamplingParams

        params = SamplingParams(
            temperature=0.0, top_p=1.0, max_tokens=request.max_new_tokens, seed=request.seed
        )
        prompts = [request.prompt] * request.batch_size
        started = time.perf_counter()
        try:
            outputs = self._llm.generate(prompts, params)
        except Exception as exc:
            if "out of memory" in str(exc).lower():
                raise WorkloadFailure(
                    "resource_exhausted",
                    f"vLLM OOM at batch_size={request.batch_size}: {exc}",
                ) from exc
            raise WorkloadFailure("infrastructure_error", f"vLLM generate failed: {exc}") from exc
        latency = time.perf_counter() - started
        texts = tuple(output.outputs[0].text for output in outputs)
        return GenerationResult(texts=texts, logits=None, latency_s=latency)
```

- [ ] **Step 5: 跑测试确认通过（Windows 主机上跑，无 torch 也必须绿）**

```bash
python -m pytest tests/py/test_aiinfra_backends_capability.py tests/py/test_aiinfra_determinism.py -q
```
Expected: 全部 PASS

- [ ] **Step 6: 在 WSL 里冒烟一次真后端**

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && ~/aiinfra-venv/bin/python -c \"
import sys; sys.path.insert(0,'.')
from scripts.aiinfra.backends.base import GenerationRequest, get_backend
b = get_backend('torch_eager', model={'id':'Qwen/Qwen2.5-0.5B-Instruct','revision':'<pinned sha>','dtype':'float16'}, options={})
print(b.describe())
r = b.generate(GenerationRequest(prompt='Hello', batch_size=2, max_new_tokens=8, seed=0, dtype='float16'))
print(len(r.texts), repr(r.texts[0][:40]), round(r.latency_s,3))
\""
```
Expected: `describe()` 的 `effective_path` 显示 `torch.float16@cuda`；生成 2 条文本。

- [ ] **Step 7: 提交**

```bash
git add scripts/aiinfra/backends/torch_eager.py scripts/aiinfra/backends/vllm_offline.py tests/py/test_aiinfra_backends_capability.py
git commit -m "feat(aiinfra): add eager and vLLM backends that report capability failures structurally" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 16: 把 spike 判据写死（**必须在跑之前提交**）

**Files:**
- Create: `configs/aiinfra/spike/spike_criteria.json`
- Create: `configs/aiinfra/spike/spike_l0.json`、`spike_l1.json`（负载配置）
- Create: `scripts/aiinfra/spike_evaluate.py`
- Test: `tests/py/test_aiinfra_spike_criteria.py`

**Interfaces:**
- Produces:
  - `spike_evaluate.evaluate(criteria: dict, cells: list[dict]) -> dict`
    → `{"L0": bool, "L1": bool, "L2": bool, "verdict": str, "evidence": {...}}`
  - `verdict ∈ {"phenomenon_confirmed", "L0_failed", "L1_failed", "L2_failed"}`

**判据（抄自 `PLAN.md` §4，一个字都不许改）**

| 级别 | 判据 |
|---|---|
| L0 | 同配置重复 50 次 = **恰好 1 个**唯一输出 |
| L1 | **只改 batch size** 后唯一输出数 > 1 |
| L2 | L1 在 **3 次独立会话**中可复现 |

**固定配置（`PLAN.md` §4）**：`Qwen2.5-0.5B-Instruct`（pin revision）· greedy ·
固定 prompt · 重复 50 次 · batch size ∈ {1, 8, 32} · 输出长度足够长以规避 ADR-8 的短输出不敏感问题
→ 本计划取 `max_new_tokens = 256`。

- [ ] **Step 1: 写 `configs/aiinfra/spike/spike_criteria.json`**

```json
{
  "schema": {"name": "aiinfra.spike-criteria", "version": 1},
  "registered_on": "2026-08-24",
  "immutable": true,
  "model": "qwen2.5-0.5b-instruct",
  "decode": "greedy",
  "repeats": 50,
  "max_new_tokens": 256,
  "batch_sizes": [1, 8, 32],
  "sessions": 3,
  "criteria": {
    "L0": {
      "statement": "Fifty repeats of one fixed configuration produce exactly one unique output.",
      "cell": "batch_size=1",
      "required_unique_output_count": 1
    },
    "L1": {
      "statement": "Changing only batch size makes the unique output count exceed one.",
      "baseline_cell": "batch_size=1",
      "compared_cells": ["batch_size=8", "batch_size=32"],
      "required": "at least one compared cell differs from the baseline digest, or has unique_output_count > 1"
    },
    "L2": {
      "statement": "L1 reproduces in three independent sessions.",
      "required_sessions_passing": 3
    }
  },
  "outcome_plan": {
    "L0_failed": "Stronger result. Headline becomes: repeating one configuration is already irreproducible; restoring L0 costs X.",
    "L1_failed": "Fall back to cross-architecture determinism. Cannot be verified until the cluster probe passes.",
    "L2_failed": "Phenomenon exists but is intermittent. The matrix reports reproduction_rate instead of a binary verdict."
  }
}
```

- [ ] **Step 2: 写 `configs/aiinfra/spike/spike_l0.json`**（L0 与 L1 共用一份配置：
      一次运行同时覆盖三个 batch size）

```json
{
  "schema": {"name": "aiinfra.workload-config", "version": 1},
  "workload": "determinism",
  "backend": "torch_eager",
  "model": "qwen2.5-0.5b-instruct",
  "dtype": "float16",
  "prompt": "Describe, step by step, how a numerical algorithm can produce different results on identical inputs when the batch size changes. Be specific about reduction order.",
  "max_new_tokens": 256,
  "repeats": 50,
  "batch_sizes": [1, 8, 32],
  "seed": 0,
  "decode": "greedy",
  "options": {"device": "cuda"}
}
```

`spike_l1.json` 与之相同，只把 `"backend"` 改成 `"vllm_offline"`、
`"options"` 改成 `{"enforce_eager": false, "gpu_memory_utilization": 0.8}`。
（vLLM 装不上时这一份产出 `unsupported_capability`，是记录不是空白。）

- [ ] **Step 3: 写失败测试 `tests/py/test_aiinfra_spike_criteria.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CRITERIA = REPO_ROOT / "configs" / "aiinfra" / "spike" / "spike_criteria.json"


def _criteria() -> dict:
    return json.loads(CRITERIA.read_text(encoding="utf-8"))


def _cells(baseline_unique: int, other_unique: int, baseline_digest: str, other_digest: str):
    return [
        {
            "cell_id": "batch_size=1",
            "unique_output_count": baseline_unique,
            "output_digests": [baseline_digest] * 50,
            "reproduction_rate": 1.0,
        },
        {
            "cell_id": "batch_size=8",
            "unique_output_count": other_unique,
            "output_digests": [other_digest] * 50,
            "reproduction_rate": 1.0,
        },
        {
            "cell_id": "batch_size=32",
            "unique_output_count": 1,
            "output_digests": [baseline_digest] * 50,
            "reproduction_rate": 1.0,
        },
    ]


def test_committed_criteria_match_the_plan_verbatim() -> None:
    criteria = _criteria()
    assert criteria["repeats"] == 50
    assert criteria["batch_sizes"] == [1, 8, 32]
    assert criteria["sessions"] == 3
    assert criteria["criteria"]["L0"]["required_unique_output_count"] == 1
    assert criteria["immutable"] is True


def test_l0_fails_when_one_configuration_is_already_irreproducible() -> None:
    from scripts.aiinfra import spike_evaluate

    verdict = spike_evaluate.evaluate(_criteria(), _cells(3, 1, "aa", "aa"))

    assert verdict["L0"] is False
    assert verdict["verdict"] == "L0_failed"


def test_l1_passes_when_batch_size_changes_the_output() -> None:
    from scripts.aiinfra import spike_evaluate

    verdict = spike_evaluate.evaluate(_criteria(), _cells(1, 1, "aa", "bb"))

    assert verdict["L0"] is True
    assert verdict["L1"] is True


def test_l1_fails_when_every_batch_size_gives_the_same_single_output() -> None:
    from scripts.aiinfra import spike_evaluate

    verdict = spike_evaluate.evaluate(_criteria(), _cells(1, 1, "aa", "aa"))

    assert verdict["L0"] is True
    assert verdict["L1"] is False
    assert verdict["verdict"] == "L1_failed"


def test_l2_requires_three_passing_sessions() -> None:
    from scripts.aiinfra import spike_evaluate

    sessions = [
        spike_evaluate.evaluate(_criteria(), _cells(1, 1, "aa", "bb")) for _ in range(2)
    ]
    sessions.append(spike_evaluate.evaluate(_criteria(), _cells(1, 1, "aa", "aa")))

    combined = spike_evaluate.combine_sessions(_criteria(), sessions)

    assert combined["L2"] is False
    assert combined["sessions_passing_l1"] == 2
    assert combined["verdict"] == "L2_failed"
```

- [ ] **Step 4: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_spike_criteria.py -q
```
Expected: FAIL — `ModuleNotFoundError: scripts.aiinfra.spike_evaluate`

- [ ] **Step 5: 实现 `scripts/aiinfra/spike_evaluate.py`**

```python
"""Apply the pre-registered spike criteria to measured cells. No criterion is computed here.

Every threshold comes from configs/aiinfra/spike/spike_criteria.json, which is committed
before the spike runs (ADR-14). This module only reads and applies it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _cell(cells: Sequence[Mapping[str, Any]], cell_id: str) -> Mapping[str, Any]:
    for cell in cells:
        if cell["cell_id"] == cell_id:
            return cell
    raise ValueError(f"spike cells are missing {cell_id!r}")


def evaluate(criteria: Mapping[str, Any], cells: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Judge one session against L0 and L1. L2 needs `combine_sessions`."""
    l0_spec = criteria["criteria"]["L0"]
    l1_spec = criteria["criteria"]["L1"]

    baseline = _cell(cells, l0_spec["cell"])
    l0 = baseline["unique_output_count"] == l0_spec["required_unique_output_count"]

    baseline_digests = set(baseline["output_digests"])
    l1 = False
    differing: list[str] = []
    for cell_id in l1_spec["compared_cells"]:
        cell = _cell(cells, cell_id)
        moved = cell["unique_output_count"] > 1 or set(cell["output_digests"]) != baseline_digests
        if moved:
            l1 = True
            differing.append(cell_id)

    verdict = "L0_failed" if not l0 else ("L1_failed" if not l1 else "L1_passed")
    return {
        "L0": l0,
        "L1": l1,
        "L2": None,
        "verdict": verdict,
        "evidence": {
            "baseline_unique_output_count": baseline["unique_output_count"],
            "baseline_reproduction_rate": baseline["reproduction_rate"],
            "cells_that_moved": differing,
        },
    }


def combine_sessions(
    criteria: Mapping[str, Any], sessions: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    """Judge L2 across independent sessions."""
    required = criteria["criteria"]["L2"]["required_sessions_passing"]
    passing = sum(1 for session in sessions if session["L1"])
    l0_all = all(session["L0"] for session in sessions)
    l2 = passing >= required

    if not l0_all:
        verdict = "L0_failed"
    elif passing == 0:
        verdict = "L1_failed"
    elif not l2:
        verdict = "L2_failed"
    else:
        verdict = "phenomenon_confirmed"

    return {
        "L0": l0_all,
        "L1": passing > 0,
        "L2": l2,
        "sessions_run": len(sessions),
        "sessions_passing_l1": passing,
        "sessions_required": required,
        "verdict": verdict,
        "outcome_plan": criteria["outcome_plan"].get(verdict, "Headline stands as planned."),
    }
```

- [ ] **Step 6: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_spike_criteria.py -q
```
Expected: 全部 PASS

- [ ] **Step 7: 提交 —— 这一步必须在任何 spike 运行之前完成**

```bash
git add configs/aiinfra/spike scripts/aiinfra/spike_evaluate.py tests/py/test_aiinfra_spike_criteria.py
git commit -m "feat(aiinfra): register the spike L0/L1/L2 criteria before running the spike" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
git log -1 --format=%H
```
把这个 commit sha 记下来 —— 它是"判据先于数据"的证据，要写进 spike 证据包。

---

### Task 17: 跑 spike，按判据出结论

**Files:**
- Create: `scripts/aiinfra/spike_run.py`
- Create: `experiments/aiinfra/spike_determinism_0p5b/{summary.json,summary.md,manifest.json,figures/}`（`git add -f`）
- Create: `docs/aiinfra/SPIKE_RESULT.md`（英文，对外可引用的一页结论）

**Interfaces:**
- Consumes: Task 14 的环境、Task 15 的后端、Task 16 的判据与 `spike_evaluate`
- Produces: 一个 `verdict ∈ {phenomenon_confirmed, L0_failed, L1_failed, L2_failed}`
  与对应的 headline 文案

- [ ] **Step 1: 实现 `scripts/aiinfra/spike_run.py`**

```python
#!/usr/bin/env python3
"""Run one spike session and judge it against the pre-registered criteria."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.aiinfra import determinism, environment, result_schema, spike_evaluate
from scripts.aiinfra.backends.base import WorkloadFailure, get_backend
from scripts.aiinfra.config import load_model_pins, load_workload_config, resolve_model


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PINS = REPO_ROOT / "configs" / "aiinfra" / "models.json"
CRITERIA = REPO_ROOT / "configs" / "aiinfra" / "spike" / "spike_criteria.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--session", type=int, required=True, help="1-based session index")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    config = load_workload_config(args.config)
    model = resolve_model(config, load_model_pins(MODEL_PINS))
    criteria = json.loads(CRITERIA.read_text(encoding="utf-8"))
    args.out_dir.mkdir(parents=True, exist_ok=True)
    target = args.out_dir / f"session_{args.session}.json"

    try:
        backend = get_backend(config.backend, model=model, options=config.options)
        cells = determinism.measure_cells(backend, config)
        describe = backend.describe()
    except WorkloadFailure as exc:
        target.write_text(
            json.dumps(
                {
                    "session": args.session,
                    "config": str(args.config),
                    "status": "failed",
                    "failure": {"category": exc.category, "message": str(exc)},
                    "environment": environment.probe(),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[spike] session {args.session} failed: {exc.category}: {exc}", file=sys.stderr)
        return 1

    document = result_schema.build_workload_result(
        workload=config.workload,
        backend=describe,
        model=model,
        environment=environment.probe(),
        cells=cells,
        completed=len(cells),
        expected=len(config.batch_sizes),
    )
    result_schema.validate_workload_result(document)
    session_verdict = spike_evaluate.evaluate(criteria, cells)
    target.write_text(
        json.dumps(
            {
                "session": args.session,
                "config": str(args.config),
                "status": "success",
                "result": document,
                "verdict": session_verdict,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(session_verdict, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 跑三次独立会话（每次都是一个全新进程，L2 要求的就是这个）**

```bash
for s in 1 2 3; do
  wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && AIINFRA_CONTAINER_DIGEST=${DIGEST:-none} ~/aiinfra-venv/bin/python scripts/aiinfra/spike_run.py --config configs/aiinfra/spike/spike_l0.json --session $s --out-dir experiments/aiinfra/spike_determinism_0p5b"
done
```
每次约 `50 repeats × 3 batch sizes × 256 tokens`；0.5B 上单次大致数分钟到半小时量级。
**跑之前先关掉其它占用 GPU 的进程**（本机只有 8,151 MiB），并 `nvidia-smi` 记一次占用快照
存进 `summary.md` —— 与集群侧的共租户记录同一条纪律（ADR-10）。

- [ ] **Step 3: vLLM 那一份也跑一次（装不上就记录失败，不跳过）**

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && ~/aiinfra-venv/bin/python scripts/aiinfra/spike_run.py --config configs/aiinfra/spike/spike_l1.json --session 1 --out-dir experiments/aiinfra/spike_determinism_0p5b/vllm"
```
Expected: 要么产出结果，要么产出
`{"status": "failed", "failure": {"category": "unsupported_capability", ...}}`。
**两种都是交付物。**

- [ ] **Step 4: 合成三次会话的 L2 结论**

```bash
python - <<'PY'
import json, pathlib, sys
sys.path.insert(0, ".")
from scripts.aiinfra import spike_evaluate

root = pathlib.Path("experiments/aiinfra/spike_determinism_0p5b")
criteria = json.loads(pathlib.Path("configs/aiinfra/spike/spike_criteria.json").read_text())
sessions = []
for path in sorted(root.glob("session_*.json")):
    payload = json.loads(path.read_text())
    if payload["status"] == "success":
        sessions.append(payload["verdict"])
combined = spike_evaluate.combine_sessions(criteria, sessions)
(root / "summary.json").write_text(json.dumps({
    "schema": {"name": "aiinfra.spike-verdict", "version": 1},
    "criteria_commit": "<paste the Task 16 Step 7 commit sha>",
    "sessions": sessions,
    "combined": combined,
    "claim_boundary": "One model (0.5B), one prompt, one workstation GPU, one software stack. This establishes whether the phenomenon exists locally; it does not establish its magnitude at 7B, on datacentre silicon, or under a different stack.",
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps(combined, indent=2))
PY
```

- [ ] **Step 5: 按判据写 headline —— 四种结局各有既定文案，不许现编**

| `verdict` | headline 写法（`docs/aiinfra/SPIKE_RESULT.md` 与 `summary.md` 同一句） |
|---|---|
| `phenomenon_confirmed` | "Changing only the batch size turns one unique output into k on the local 0.5B configuration, reproducibly across three sessions." |
| `L0_failed` | "Repeating one fixed configuration is already irreproducible: N repeats produced k unique outputs. Restoring a single unique output is the cost this project measures." |
| `L1_failed` | "Batch size alone does not break determinism on this model, backend and stack. The determinism axis moves to cross-architecture comparison, which is blocked on the cluster probe." |
| `L2_failed` | "The phenomenon exists but is intermittent: it appeared in m of 3 sessions. The breakage matrix reports a reproduction rate, not a binary verdict." |

把选中的那一句写进 `docs/aiinfra/SPIKE_RESULT.md`，并附：判据 commit sha、
三次会话的原始唯一输出数、环境探针摘要、`claim_boundary`。

- [ ] **Step 6: 出一张图**

```bash
python - <<'PY'
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = pathlib.Path("experiments/aiinfra/spike_determinism_0p5b")
summary = json.loads((root / "summary.json").read_text())
sessions = summary["sessions"]
labels = ["batch_size=1", "batch_size=8", "batch_size=32"]

fig, ax = plt.subplots(figsize=(6.0, 3.4))
for index, session in enumerate(sessions, start=1):
    payload = json.loads((root / f"session_{index}.json").read_text())
    counts = {c["cell_id"]: c["unique_output_count"] for c in payload["result"]["cells"]}
    ax.plot(labels, [counts[label] for label in labels], marker="o", label=f"session {index}")
ax.set_ylabel("Unique outputs in 50 repeats")
ax.set_xlabel("Batch size (only variable changed)")
ax.axhline(1, color="#888888", linewidth=0.8)
ax.legend(frameon=False)
fig.tight_layout()
(root / "figures").mkdir(exist_ok=True)
fig.savefig(root / "figures" / "spike_unique_outputs.png", dpi=200)
print("wrote", root / "figures" / "spike_unique_outputs.png")
PY
```

- [ ] **Step 7: 写 `manifest.json` 并校验**

```json
{
  "schema": {"name": "hrsc.experiment-manifest", "version": 1},
  "id": "aiinfra-spike-determinism-0p5b",
  "report": "aiinfra",
  "lifecycle": "canonical",
  "purpose": "Decide, against criteria registered before the run, whether changing only batch size turns one unique greedy output into several on a locally runnable 0.5B model.",
  "pipeline": {
    "config": ["configs/aiinfra/spike/spike_criteria.json"],
    "build": ["scripts/aiinfra/prepare_assets.py"],
    "run": ["scripts/aiinfra/spike_run.py"],
    "measure": ["scripts/aiinfra/spike_evaluate.py"],
    "aggregate": ["experiments/aiinfra/spike_determinism_0p5b/summary.json"],
    "plot": ["experiments/aiinfra/spike_determinism_0p5b/figures/spike_unique_outputs.png"]
  },
  "evidence": [
    "experiments/aiinfra/spike_determinism_0p5b/summary.md",
    "experiments/aiinfra/spike_determinism_0p5b/summary.json"
  ],
  "retention": {
    "keep": ["manifest.json", "summary.*", "figures/", "session_*.json"],
    "transient": ["model weights (outside the tree)"]
  },
  "provenance": {
    "notes": "The L0/L1/L2 criteria were committed before any session ran; summary.json records that commit sha. Model revision, container digest and environment probe are recorded per session."
  }
}
```

```bash
python -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from scripts.harness.experiment_manifest import validate_manifest
print(validate_manifest(Path('experiments/aiinfra/spike_determinism_0p5b/manifest.json'), Path('.')))
"
```
Expected: `[]`

- [ ] **Step 8: 提交**

```bash
git add scripts/aiinfra/spike_run.py docs/aiinfra/SPIKE_RESULT.md
git add -f experiments/aiinfra/spike_determinism_0p5b
git commit -m "feat(aiinfra): run the determinism spike and record the verdict against registered criteria" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 9: 停下来，把结论带回给人**

`PLAN.md` §4 最后一句是硬约束：**"任何一种情况我都会带数据回来重定 headline，不会自行改了继续跑。"**
在这里停，把 `verdict`、三次会话的数字、以及它对后续步骤的影响交给人决定，
**不要自行跳进阶段 E**。

---

## 阶段 E — 步骤 3：P1a 确定性与保真度

> **前置**：Task 17 Step 9 的结论已经交给人并确认过 headline。三种"不通过"的结局都不阻塞
> 本阶段的代码 —— 它们只改 `summary.md` 的措辞，不改测量本身。

### Task 18: 把 ULP 距离提取为共享工具

**Files:**
- Create: `scripts/metrics/ulp.py`
- Modify: `scripts/regression/mhd_gpu_fma_axis.py`（改为 import，删掉本地定义）
- Test: `tests/py/test_ulp_shared.py`（新建）

**Interfaces:**
- Produces: `scripts.metrics.ulp.ulp_max(a: np.ndarray, b: np.ndarray, dtype: str) -> int`

**不要碰的东西**：`scripts/regression/matrix_summary_report.py:394` 的 `_ulp_max` 是
**另一个量** —— 它是 `max|Δ| / (eps × max|left|)` 的 eps 归一化相对量，不是位模式整数距离。
名字像，语义不同。**不要把两者统一**，那会静默改掉 report 2 的已发表数字。见 §Review R-11。

- [ ] **Step 1: 写失败测试 `tests/py/test_ulp_shared.py`**

```python
from __future__ import annotations

import numpy as np
import pytest


def test_identical_arrays_have_zero_ulp_distance() -> None:
    from metrics.ulp import ulp_max

    values = np.array([1.0, -2.5, 0.0, 1e-30], dtype=np.float64)
    assert ulp_max(values, values.copy(), "float64") == 0


def test_one_ulp_step_is_reported_as_one() -> None:
    from metrics.ulp import ulp_max

    a = np.array([1.0], dtype=np.float32)
    b = np.nextafter(a, np.float32(2.0))
    assert ulp_max(a, b, "float32") == 1


def test_the_mapping_is_monotone_across_zero() -> None:
    from metrics.ulp import ulp_max

    negative = np.array([-0.0], dtype=np.float64)
    positive = np.array([0.0], dtype=np.float64)
    assert ulp_max(negative, positive, "float64") == 0

    a = np.array([-1.0], dtype=np.float64)
    b = np.array([1.0], dtype=np.float64)
    assert ulp_max(a, b, "float64") > 0


def test_the_regression_driver_uses_the_shared_implementation() -> None:
    import metrics.ulp
    from scripts.regression import mhd_gpu_fma_axis

    assert mhd_gpu_fma_axis.ulp_max is metrics.ulp.ulp_max
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_ulp_shared.py -q
```
Expected: FAIL — `ModuleNotFoundError: No module named 'metrics.ulp'`

- [ ] **Step 3: 实现 `scripts/metrics/ulp.py`（函数体逐字取自
      `scripts/regression/mhd_gpu_fma_axis.py:55-68`，一个字符都不改）**

```python
"""Bit-pattern distance in units in the last place.

Extracted verbatim from scripts/regression/mhd_gpu_fma_axis.py so the LLM fidelity path
and the solver GPU-contraction path report the same quantity. This is NOT the same metric
as matrix_summary_report._ulp_max, which is an eps-normalised relative deviation.
"""

from __future__ import annotations

import numpy as np


def ulp_max(a: np.ndarray, b: np.ndarray, dtype: str) -> int:
    """Largest cellwise distance in units in the last place.

    Sign-adjusted bit patterns of one IEEE type map to monotone integers; the
    reported value is the maximum absolute difference of those integers.
    """
    itype = np.int32 if dtype == "float32" else np.int64
    offset = np.iinfo(itype).min

    def to_ordered(x: np.ndarray) -> np.ndarray:
        bits = x.astype(dtype).view(itype).astype(np.int64)
        return np.where(bits < 0, offset - bits, bits)

    return int(np.max(np.abs(to_ordered(a) - to_ordered(b))))
```

- [ ] **Step 4: 改 `scripts/regression/mhd_gpu_fma_axis.py`**

删掉 `def ulp_max(...)` 整个定义（第 55–68 行），在 `from _mhd_harness import (...)` 之后加：

```python
from metrics.ulp import ulp_max  # noqa: E402
```
并把 `sys.path` 那一行里的路径补上 `ROOT / "scripts" / "metrics"`：

```python
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression", ROOT / "scripts" / "metrics"):
```

- [ ] **Step 5: 跑测试确认通过，并确认 GPU 轴的下游没被打破**

```bash
python -m pytest tests/py/test_ulp_shared.py tests/py/test_mhd_gpu_hardware_axis.py tests/py/test_matrix_summary_report.py -q
```
Expected: 全部 PASS。`matrix_summary_report` 的 `ulp_max` 值不变（它用的是自己的 `_ulp_max`）。

- [ ] **Step 6: 提交**

```bash
git add scripts/metrics/ulp.py scripts/regression/mhd_gpu_fma_axis.py tests/py/test_ulp_shared.py
git commit -m "refactor(metrics): share the bit-pattern ULP distance between solver and LLM paths" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 19: 噪声地板与保真度（ADR-9：地板先于任何跨配置判定）

**Files:**
- Modify: `scripts/aiinfra/backends/base.py`（`GenerationRequest` 加 `capture_logits`）
- Modify: `scripts/aiinfra/backends/{fake,torch_eager,vllm_offline}.py`
- Create: `scripts/aiinfra/fidelity.py`、`scripts/aiinfra/noise_floor.py`
- Test: `tests/py/test_aiinfra_noise_floor.py`（新建）

**Interfaces:**
- Produces:
  - `GenerationRequest.capture_logits: bool = False`
  - `GenerationResult.logits` — `capture_logits=True` 时为 `np.ndarray`，
    形状 `(vocab,)`，`float32`，内容是 **batch 位置 0 的第一个生成 token 的完整词表 logits**
  - `fidelity.compare_logits(a, b) -> {"ulp_max", "linf_abs", "l2", "kl_divergence"}`
  - `noise_floor.measure_floor(backend, config, repeats) -> dict`
  - `noise_floor.exceeds_floor(observed: Mapping, floor: Mapping) -> dict`

**为什么只取第一个 token 的 logits**：Qwen2.5 词表约 151k。`(batch=32, steps=256, vocab=151k)`
的 float32 张量是 ~6 TB，不可能留存。第一个生成位置的 `(vocab,)` 是 ~600 KB，
既能量化差异又能存。这是刻意的取舍，必须写进 `claim_boundary`。

**vLLM 的 logits**：离线 `LLM.generate` 只暴露 top-k logprobs，拿不到完整词表 logits。
`VllmOfflineBackend` 在 `capture_logits=True` 时抛
`WorkloadFailure("unsupported_capability", ...)`。所以**本地保真度与地板只在 `torch_eager`
上做**（ADR-3 说 eager 本来就是黄金参考）；vLLM 的保真度留到集群侧用 top-k logprob 路径补，
在结果里记为一个明确的能力缺口，不留空白。

- [ ] **Step 1: 写失败测试 `tests/py/test_aiinfra_noise_floor.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest


def _config(tmp_path: Path, **overrides):
    from scripts.aiinfra import config

    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 4,
        "repeats": 4,
        "batch_sizes": [1],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return config.load_workload_config(path)


def _backend(loaded):
    from scripts.aiinfra.backends import base

    return base.get_backend(
        loaded.backend,
        model={"id": "fake/tiny", "revision": "builtin", "dtype": loaded.dtype},
        options=loaded.options,
    )


def test_identical_logits_compare_to_zero() -> None:
    from scripts.aiinfra import fidelity

    values = np.array([0.5, -1.25, 3.0], dtype=np.float32)
    metrics = fidelity.compare_logits(values, values.copy())

    assert metrics["ulp_max"] == 0
    assert metrics["linf_abs"] == 0.0
    assert metrics["l2"] == 0.0
    assert metrics["kl_divergence"] == pytest.approx(0.0, abs=1e-12)


def test_one_ulp_difference_is_detected() -> None:
    from scripts.aiinfra import fidelity

    a = np.array([1.0], dtype=np.float32)
    b = np.nextafter(a, np.float32(2.0))

    assert fidelity.compare_logits(a, b)["ulp_max"] == 1


def test_a_deterministic_backend_has_a_zero_noise_floor(tmp_path: Path) -> None:
    from scripts.aiinfra import noise_floor

    loaded = _config(tmp_path)
    floor = noise_floor.measure_floor(_backend(loaded), loaded, repeats=4)

    assert floor["repeats"] == 4
    assert floor["pairs"] == 6
    assert floor["ulp_max"] == 0
    assert floor["linf_abs"] == 0.0


def test_a_difference_at_the_floor_is_not_called_a_difference() -> None:
    from scripts.aiinfra import noise_floor

    floor = {"ulp_max": 4, "linf_abs": 1e-6, "l2": 1e-5, "kl_divergence": 1e-9}
    observed = {"ulp_max": 4, "linf_abs": 1e-6, "l2": 1e-5, "kl_divergence": 1e-9}

    verdict = noise_floor.exceeds_floor(observed, floor)

    assert verdict["exceeds"] is False
    assert verdict["exceeded_metrics"] == []


def test_a_difference_above_the_floor_is_reported_with_the_metric_that_moved() -> None:
    from scripts.aiinfra import noise_floor

    floor = {"ulp_max": 4, "linf_abs": 1e-6, "l2": 1e-5, "kl_divergence": 1e-9}
    observed = {"ulp_max": 400, "linf_abs": 1e-6, "l2": 1e-5, "kl_divergence": 1e-9}

    verdict = noise_floor.exceeds_floor(observed, floor)

    assert verdict["exceeds"] is True
    assert verdict["exceeded_metrics"] == ["ulp_max"]


def test_capture_logits_is_unsupported_on_vllm(monkeypatch: pytest.MonkeyPatch) -> None:
    """vLLM's offline API exposes top-k logprobs, not full-vocabulary logits."""
    from scripts.aiinfra.backends import vllm_offline

    assert vllm_offline.SUPPORTS_FULL_LOGITS is False
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_noise_floor.py -q
```
Expected: FAIL — `ModuleNotFoundError: scripts.aiinfra.fidelity`

- [ ] **Step 3: 给 `GenerationRequest` 加 `capture_logits`**

`scripts/aiinfra/backends/base.py`：

```python
@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    batch_size: int
    max_new_tokens: int
    seed: int
    dtype: str
    capture_logits: bool = False
```

`scripts/aiinfra/backends/fake.py`：在 `generate` 返回前，把 `logits=None` 改为

```python
        logits = None
        if request.capture_logits:
            # A deterministic pseudo-logit vector over a small synthetic vocabulary, derived
            # from the same seed material as the text so both move together.
            import numpy as np

            state = np.frombuffer(
                hashlib.sha256(seed_material + b"|logits").digest(), dtype=np.uint32
            ).astype(np.float64)
            logits = ((state % 65536) / 65536.0).astype(np.float32)
```
并把返回改成 `logits=logits`。

`scripts/aiinfra/backends/torch_eager.py`：在 `generate` 里，`generate(...)` 之后加

```python
        logits = None
        if request.capture_logits:
            with torch.inference_mode():
                forward = self._model(**encoded)
            logits = (
                forward.logits[0, -1, :].detach().to(torch.float32).cpu().numpy().copy()
            )
```
并把返回改成 `logits=logits`。

`scripts/aiinfra/backends/vllm_offline.py`：模块级加

```python
SUPPORTS_FULL_LOGITS = False
```
并在 `generate` 开头加

```python
        if request.capture_logits:
            raise WorkloadFailure(
                "unsupported_capability",
                "vLLM's offline API exposes top-k logprobs, not full-vocabulary logits",
            )
```

`fake.py` 模块级也加 `SUPPORTS_FULL_LOGITS = True`，`torch_eager.py` 同。

- [ ] **Step 4: 实现 `scripts/aiinfra/fidelity.py`**

```python
"""Logit-level difference metrics. These explain the mechanism; they are not the headline.

ADR-8: the unique-output count is the headline because it is binary and falsifiable.
ULP / L-infinity / L2 / KL are continuous, so they only answer "by how much" once a
same-configuration noise floor (see noise_floor.py) has said "more than noise".
"""

from __future__ import annotations

from typing import Any

import numpy as np

from metrics.ulp import ulp_max


def _softmax(values: np.ndarray) -> np.ndarray:
    shifted = values.astype(np.float64) - float(np.max(values))
    exponentials = np.exp(shifted)
    return exponentials / float(np.sum(exponentials))


def compare_logits(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
    """Compare two full-vocabulary logit vectors of identical shape."""
    left = np.asarray(a, dtype=np.float32)
    right = np.asarray(b, dtype=np.float32)
    if left.shape != right.shape:
        raise ValueError(f"logit shape mismatch: {left.shape} vs {right.shape}")

    difference = left.astype(np.float64) - right.astype(np.float64)
    p = _softmax(left)
    q = _softmax(right)
    support = p > 0.0
    kl = float(np.sum(p[support] * np.log(p[support] / np.maximum(q[support], 1e-300))))
    return {
        "ulp_max": ulp_max(left, right, "float32"),
        "linf_abs": float(np.max(np.abs(difference))),
        "l2": float(np.sqrt(np.sum(difference * difference))),
        "kl_divergence": kl,
    }
```

- [ ] **Step 5: 实现 `scripts/aiinfra/noise_floor.py`**

```python
"""Same-configuration repeat noise floor.

ADR-9: no cross-configuration difference may be called a difference until it is shown to
exceed the spread of repeating one configuration on one device. The floor is the maximum
over all repeat pairs, so it is a conservative upper bound on "this is just noise".
"""

from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations
from typing import Any

import numpy as np

from scripts.aiinfra.backends.base import Backend, GenerationRequest, WorkloadFailure
from scripts.aiinfra.config import WorkloadConfig
from scripts.aiinfra.fidelity import compare_logits


METRICS = ("ulp_max", "linf_abs", "l2", "kl_divergence")


def measure_floor(backend: Backend, config: WorkloadConfig, repeats: int) -> dict[str, Any]:
    """Repeat one configuration `repeats` times and take the worst pairwise difference."""
    if repeats < 2:
        raise ValueError("a noise floor needs at least two repeats")
    batch_size = config.batch_sizes[0]
    captured: list[np.ndarray] = []
    for _repeat in range(repeats):
        result = backend.generate(
            GenerationRequest(
                prompt=config.prompt,
                batch_size=batch_size,
                max_new_tokens=config.max_new_tokens,
                seed=config.seed,
                dtype=config.dtype,
                capture_logits=True,
            )
        )
        if result.logits is None:
            raise WorkloadFailure(
                "unsupported_capability",
                f"backend {backend.describe()['name']} did not return logits",
            )
        captured.append(np.asarray(result.logits, dtype=np.float32))

    pairs = list(combinations(range(repeats), 2))
    floor = {metric: 0.0 for metric in METRICS}
    for left, right in pairs:
        metrics = compare_logits(captured[left], captured[right])
        for metric in METRICS:
            floor[metric] = max(floor[metric], float(metrics[metric]))
    floor["ulp_max"] = int(floor["ulp_max"])
    floor["repeats"] = repeats
    floor["pairs"] = len(pairs)
    floor["batch_size"] = batch_size
    return floor


def exceeds_floor(observed: Mapping[str, Any], floor: Mapping[str, Any]) -> dict[str, Any]:
    """Decide whether *observed* is outside same-configuration noise, metric by metric."""
    exceeded = [
        metric
        for metric in METRICS
        if metric in observed and float(observed[metric]) > float(floor[metric])
    ]
    return {
        "exceeds": bool(exceeded),
        "exceeded_metrics": exceeded,
        "observed": {metric: observed.get(metric) for metric in METRICS},
        "floor": {metric: floor.get(metric) for metric in METRICS},
    }
```

- [ ] **Step 6: 跑测试确认通过**

```bash
python -m pytest tests/py/test_aiinfra_noise_floor.py tests/py/test_aiinfra_determinism.py tests/py/test_ulp_shared.py -q
```
Expected: 全部 PASS

- [ ] **Step 7: 提交**

```bash
git add scripts/aiinfra tests/py/test_aiinfra_noise_floor.py
git commit -m "feat(aiinfra): measure the same-configuration logit noise floor before judging differences" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 20: 本地 E3 破坏矩阵与证据包

**Files:**
- Create: `scripts/aiinfra/breakage_matrix.py`
- Create: `configs/aiinfra/p1a/breakage_matrix_local.json`
- Create: `configs/aiinfra/smoke/determinism.json`（spec §8 第 4 条命令要用它）
- Modify: `scripts/aiinfra/determinism.py`（加 CLI）
- Create: `experiments/aiinfra/p1a_breakage_matrix_local/{summary.json,summary.md,manifest.json,figures/}`
- Test: `tests/py/test_aiinfra_breakage_matrix.py`

**Interfaces:**
- Consumes: `determinism.measure_cells`、`noise_floor.measure_floor`、`backends.base.get_backend`
- Produces:
  - `determinism.main(argv) -> int`，支持 `--config <path>`（spec §8）
  - `breakage_matrix.run_matrix(spec: dict) -> dict` —— **失败的格子记录下来并继续**，
    不像 `run_matrix.py` 那样在第一个失败上中止

**为什么不复用 `scripts/run_matrix.py`**：`run_one` 在任何失败的 run 上直接
`raise RuntimeError` 并中止整个矩阵。破坏矩阵里"大 batch OOM""vLLM 不支持某后端"
都是**预期会出现且必须记录**的格子。仓库里已有先例：
`scripts/regression/mhd_week18_resolution_ladder.py` 就是"记录不完整组与数值失败而不是丢掉它们"
的包专属驱动。本任务照这个形态做。见 §Review R-7。

**本地能覆盖的轴（其余留给集群，必须在 summary 里显式标为未覆盖）**

| 轴 | 本地 | 说明 |
|---|---|---|
| batch size | ✅ {1, 8, 32} | 8 GB 显存下 0.5B 足够 |
| backend | ✅ {torch_eager, vllm_offline} | vLLM 装不上则记 `unsupported_capability` |
| attention backend | ⚠️ 仅在 vLLM 可用时 | 通过 `VLLM_ATTENTION_BACKEND` 环境变量 |
| 并发度 | ✅ 仅离线批 | 在线服务化属步骤 4，不在本计划 |
| TP | ❌ | 本地只有 1 张卡 |
| 硬件 | ❌ | 只有 RTX 5070 Laptop 一张 |
| 精度 | ⚠️ {float16, bfloat16, float32} | fp8 需 5090/集群 |

- [ ] **Step 1: 写失败测试 `tests/py/test_aiinfra_breakage_matrix.py`**

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest


def _spec(tmp_path: Path) -> dict:
    return {
        "experiment": "pytest-breakage",
        "model": "fake-tiny",
        "prompt": "hello",
        "max_new_tokens": 4,
        "repeats": 3,
        "seed": 0,
        "decode": "greedy",
        "cells": [
            {"backend": "fake", "dtype": "float32", "batch_sizes": [1, 8], "options": {}},
            {
                "backend": "fake",
                "dtype": "float32",
                "batch_sizes": [1],
                "options": {"fault": "resource_exhausted"},
            },
            {"backend": "does-not-exist", "dtype": "float32", "batch_sizes": [1], "options": {}},
        ],
    }


def test_failing_cells_are_recorded_and_the_matrix_continues(tmp_path: Path) -> None:
    from scripts.aiinfra import breakage_matrix

    summary = breakage_matrix.run_matrix(_spec(tmp_path))

    assert len(summary["cells"]) == 3
    statuses = [cell["status"] for cell in summary["cells"]]
    assert statuses == ["success", "failed", "failed"]
    assert summary["cells"][1]["failure"]["category"] == "resource_exhausted"
    assert summary["cells"][2]["failure"]["category"] == "unsupported_capability"


def test_summary_counts_are_consistent(tmp_path: Path) -> None:
    from scripts.aiinfra import breakage_matrix

    summary = breakage_matrix.run_matrix(_spec(tmp_path))

    assert summary["completion"] == {"completed": 1, "expected": 3}
    assert summary["failure_categories"] == {
        "resource_exhausted": 1,
        "unsupported_capability": 1,
    }


def test_uncovered_axes_are_declared_explicitly(tmp_path: Path) -> None:
    from scripts.aiinfra import breakage_matrix

    summary = breakage_matrix.run_matrix(_spec(tmp_path))

    assert set(summary["axes_not_covered"]) >= {"tensor_parallel", "hardware", "fp8"}
```

- [ ] **Step 2: 跑测试确认失败**

```bash
python -m pytest tests/py/test_aiinfra_breakage_matrix.py -q
```
Expected: FAIL — `ModuleNotFoundError: scripts.aiinfra.breakage_matrix`

- [ ] **Step 3: 实现 `scripts/aiinfra/breakage_matrix.py`**

```python
#!/usr/bin/env python3
"""Breakage matrix driver: a failing cell is a recorded result, not an aborted matrix.

scripts/run_matrix.py raises on the first failed run, which is right for the solver but
wrong here: OOM at a large batch and an unavailable backend are cells this experiment
exists to record. This driver follows the shape of
scripts/regression/mhd_week18_resolution_ladder.py, which keeps incomplete groups instead
of dropping them.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.aiinfra import determinism, environment
from scripts.aiinfra.backends.base import WorkloadFailure, get_backend
from scripts.aiinfra.config import WorkloadConfig, load_model_pins, resolve_model


REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_PINS = REPO_ROOT / "configs" / "aiinfra" / "models.json"
AXES_NOT_COVERED_LOCALLY = (
    "tensor_parallel",
    "hardware",
    "fp8",
    "online_serving_concurrency",
    "multi_node",
)


def _config_for(spec: dict[str, Any], cell: dict[str, Any]) -> WorkloadConfig:
    return WorkloadConfig(
        workload="determinism",
        backend=str(cell["backend"]),
        model_key=str(spec["model"]),
        dtype=str(cell["dtype"]),
        prompt=str(spec["prompt"]),
        max_new_tokens=int(spec["max_new_tokens"]),
        repeats=int(spec["repeats"]),
        batch_sizes=tuple(int(size) for size in cell["batch_sizes"]),
        seed=int(spec["seed"]),
        decode=str(spec["decode"]),
        options=dict(cell.get("options", {})),
    )


def run_matrix(spec: dict[str, Any]) -> dict[str, Any]:
    """Run every cell, keep every outcome, and never abort on a cell failure."""
    pins = load_model_pins(MODEL_PINS)
    records: list[dict[str, Any]] = []
    for index, cell in enumerate(spec["cells"]):
        config = _config_for(spec, cell)
        label = f"{cell['backend']}/{cell['dtype']}/batch={list(config.batch_sizes)}"
        record: dict[str, Any] = {"index": index, "label": label, "axes": dict(cell)}
        try:
            model = resolve_model(config, pins)
            backend = get_backend(config.backend, model=model, options=config.options)
            record["backend"] = backend.describe()
            record["cells"] = determinism.measure_cells(backend, config)
            record["status"] = "success"
            record["failure"] = None
        except WorkloadFailure as exc:
            record["status"] = "failed"
            record["failure"] = {"category": exc.category, "message": str(exc)}
        except ValueError as exc:
            record["status"] = "failed"
            record["failure"] = {"category": "configuration_error", "message": str(exc)}
        records.append(record)

    completed = sum(1 for record in records if record["status"] == "success")
    categories = Counter(
        record["failure"]["category"] for record in records if record["failure"] is not None
    )
    return {
        "schema": {"name": "aiinfra.breakage-matrix", "version": 1},
        "experiment": spec["experiment"],
        "environment": environment.probe(),
        "cells": records,
        "completion": {"completed": completed, "expected": len(records)},
        "failure_categories": dict(categories),
        "axes_not_covered": list(AXES_NOT_COVERED_LOCALLY),
        "claim_boundary": (
            "One workstation GPU, one 0.5B model, one software stack, offline batching "
            "only. Cells marked unsupported_capability or resource_exhausted are recorded "
            "outcomes, not gaps. Tensor parallelism, a second architecture, FP8 and online "
            "serving are not covered locally and are listed in axes_not_covered."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    summary = run_matrix(spec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "completion": summary["completion"],
                "failure_categories": summary["failure_categories"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: 给 `determinism.py` 加 CLI（spec §8 第 4 条命令）**

在 `scripts/aiinfra/determinism.py` 末尾追加：

```python
def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys
    from pathlib import Path

    if __package__ in (None, ""):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from scripts.aiinfra.backends.base import WorkloadFailure, get_backend
    from scripts.aiinfra.config import load_model_pins, load_workload_config, resolve_model

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    config = load_workload_config(args.config)
    model = resolve_model(config, load_model_pins(repo_root / "configs" / "aiinfra" / "models.json"))
    try:
        backend = get_backend(config.backend, model=model, options=config.options)
        cells = measure_cells(backend, config)
    except WorkloadFailure as exc:
        json.dump({"status": "failed", "failure": {"category": exc.category, "message": str(exc)}}, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1
    json.dump({"status": "success", "backend": backend.describe(), "cells": cells}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

`configs/aiinfra/smoke/determinism.json`：与 `fake_workload_run.json` 相同，
只把 `repeats` 降到 3、`batch_sizes` 降到 `[1, 4]`，用作最快的冒烟。

- [ ] **Step 5: 写 `configs/aiinfra/p1a/breakage_matrix_local.json`**

```json
{
  "experiment": "aiinfra-p1a-breakage-matrix-local",
  "model": "qwen2.5-0.5b-instruct",
  "prompt": "Describe, step by step, how a numerical algorithm can produce different results on identical inputs when the batch size changes. Be specific about reduction order.",
  "max_new_tokens": 256,
  "repeats": 20,
  "seed": 0,
  "decode": "greedy",
  "cells": [
    {"backend": "torch_eager", "dtype": "float16", "batch_sizes": [1, 8, 32], "options": {"device": "cuda"}},
    {"backend": "torch_eager", "dtype": "bfloat16", "batch_sizes": [1, 8, 32], "options": {"device": "cuda"}},
    {"backend": "torch_eager", "dtype": "float32", "batch_sizes": [1, 8], "options": {"device": "cuda"}},
    {"backend": "vllm_offline", "dtype": "float16", "batch_sizes": [1, 8, 32], "options": {"enforce_eager": false, "gpu_memory_utilization": 0.8}},
    {"backend": "vllm_offline", "dtype": "float16", "batch_sizes": [1, 8, 32], "options": {"enforce_eager": true, "gpu_memory_utilization": 0.8}}
  ]
}
```

`repeats` 从 spike 的 50 降到 20，因为格子数从 3 涨到 15；这是刻意的取舍，
必须写进 `summary.md` 的方法说明（"20 repeats bound the count, they do not bound the tail"）。

- [ ] **Step 6: 跑测试确认通过，再跑真矩阵**

```bash
python -m pytest tests/py/test_aiinfra_breakage_matrix.py -q
python scripts/aiinfra/determinism.py --config configs/aiinfra/smoke/determinism.json
```
Expected: 测试全绿；冒烟打印 `"status": "success"` 与两格结果。

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && AIINFRA_CONTAINER_DIGEST=${DIGEST:-none} ~/aiinfra-venv/bin/python scripts/aiinfra/breakage_matrix.py --spec configs/aiinfra/p1a/breakage_matrix_local.json --out experiments/aiinfra/p1a_breakage_matrix_local/summary.json"
```
Expected: 打印 `completion` 与 `failure_categories`；**允许出现失败格子**。

- [ ] **Step 7: 先测地板，再解释矩阵**

```bash
wsl -d Ubuntu -- bash -lc "cd /mnt/c/Users/tangy/Desktop/testing/float-point && ~/aiinfra-venv/bin/python -c \"
import json, sys; sys.path.insert(0,'.')
from pathlib import Path
from scripts.aiinfra import noise_floor
from scripts.aiinfra.backends.base import get_backend
from scripts.aiinfra.config import load_model_pins, load_workload_config, resolve_model
cfg = load_workload_config(Path('configs/aiinfra/spike/spike_l0.json'))
model = resolve_model(cfg, load_model_pins(Path('configs/aiinfra/models.json')))
b = get_backend('torch_eager', model=model, options=cfg.options)
floor = noise_floor.measure_floor(b, cfg, repeats=10)
Path('experiments/aiinfra/p1a_breakage_matrix_local/noise_floor.json').write_text(json.dumps(floor, indent=2))
print(json.dumps(floor, indent=2))
\""
```
**这一步必须先于任何"跨配置存在差异"的说法**（ADR-9）。地板写进 `summary.md`，
每一条跨配置结论都要引用 `exceeds_floor` 的判定。

- [ ] **Step 8: 出图、写 `summary.md`、写 `manifest.json`、校验、提交**

图：横轴 batch size，纵轴唯一输出数，每个 backend/dtype 一条线；失败格子画成空心标记
并在图注里写明失败类别（**不要把失败格子从图里删掉**）。

`manifest.json` 与 Task 17 同形，`id` 用 `aiinfra-p1a-breakage-matrix-local`，
`report` 用 `aiinfra`，`pipeline` 六个阶段分别指向
`configs/aiinfra/p1a/breakage_matrix_local.json`、`scripts/aiinfra/prepare_assets.py`、
`scripts/aiinfra/breakage_matrix.py`、`scripts/aiinfra/noise_floor.py`、
`experiments/aiinfra/p1a_breakage_matrix_local/summary.json`、
`experiments/aiinfra/p1a_breakage_matrix_local/figures/breakage_matrix.png`。

```bash
python -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from scripts.harness.experiment_manifest import validate_manifest
print(validate_manifest(Path('experiments/aiinfra/p1a_breakage_matrix_local/manifest.json'), Path('.')))
"
git add scripts/aiinfra configs/aiinfra tests/py/test_aiinfra_breakage_matrix.py
git add -f experiments/aiinfra/p1a_breakage_matrix_local
git commit -m "feat(aiinfra): record the local breakage matrix with its noise floor and uncovered axes" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
Expected: 校验返回 `[]`。

---

### Task 21: 全量验收（spec §8 的五条命令逐条跑通）

**Files:**
- Modify: `docs/INDEX.md`（§7 状态、§3 规模数字）
- Modify: `docs/aiinfra/PLAN.md`（在步骤 0/1/2/3 旁标注完成状态与证据包路径）

- [ ] **Step 1: spec §8 第 1 条 —— 回归**

```bash
python -m pytest tests/py -q 2>&1 | tail -2
```
Expected: `0 failed`，`skipped` 仍为 **25**，`passed` 明显高于 463。

```bash
cmake --build build-double --target unit_tests && ./build-double/unit_tests -r compact
```
Expected: 全部通过。（若本机没配好 MSVC 环境，按 `docs/INDEX.md` §4.1 先加载 `VsDevCmd.bat`。）

- [ ] **Step 2: spec §8 第 2 条 —— 假负载**

```bash
python scripts/run_matrix.py configs/aiinfra/smoke/fake_workload.json | tail -20
```
Expected: `"status": "success"`

- [ ] **Step 3: spec §8 第 3 条 —— 环境探针**

```bash
python scripts/aiinfra/environment.py --json | head -20
```
Expected: 合法 JSON，且**没有**发生任何安装或下载。

- [ ] **Step 4: spec §8 第 4 条 —— 确定性冒烟**

```bash
python scripts/aiinfra/determinism.py --config configs/aiinfra/smoke/determinism.json
```
Expected: `"status": "success"`

- [ ] **Step 5: spec §8 第 5 条 —— 实验清单审计**

```bash
python scripts/audit_experiments.py --format markdown | head -30
```
Expected: 没有 `experiments/` 下的嵌套 build 目录。

- [ ] **Step 6: 端到端判据 —— 三个新证据包全部通过清单校验**

```bash
python - <<'PY'
import sys; sys.path.insert(0, ".")
from pathlib import Path
from scripts.harness.experiment_manifest import validate_manifest
for name in ("env_probe_local", "spike_determinism_0p5b", "p1a_breakage_matrix_local"):
    path = Path("experiments/aiinfra") / name / "manifest.json"
    print(name, validate_manifest(path, Path(".")))
PY
```
Expected: 三行都是 `[]`

- [ ] **Step 7: 更新文档并提交**

`docs/INDEX.md` §7：把步骤 1/2 标 **[delivered]**，把步骤 0 的结论一句话写进去并链到
`aiinfra/SPIKE_RESULT.md`，把步骤 3 标 **[delivered, local subset]** 并链到破坏矩阵包。
§3 的规模数字（pytest 模块数、证据包数）重新数一遍再写。

`docs/aiinfra/PLAN.md` §3 的表格里给步骤 0/1/2/3 加一列"状态 / 证据包"。

```bash
git add docs/INDEX.md docs/aiinfra/PLAN.md
git commit -m "docs: mark the locally executable steps delivered and link their evidence packets" -m "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Review — 计划对 spec 的核对结果

> 这一节是把计划拿回去对着 `PLAN.md` / `ADR.md` / 仓库现状重读一遍的产物。
> 每条都给了"我做了什么"，不只是"我发现了什么"。

### R-1 · 执行顺序：环境下载提前并行（相对 spec 的调整）

`PLAN.md` §3 把步骤 0（spike）排在步骤 1 之前，理由是 ADR-14："不要在现象未验证前投入平台建设"。
但步骤 0 的长尾是**下载与安装**（WSL 3.12 环境 + torch + 1 GB 权重，1–3 h 墙钟，纯等待），
而步骤 1 在 spike 的**三种结局下都需要** —— 三种结局改的是 headline 文案，不是 harness。

**做法**：Task 14（环境）与阶段 B（Task 1–8）并行启动，spike 本身（Task 15–17）仍在
建平台之前完成。ADR-14 的意图不受损。

### R-2 · 测试基线数字与实测不符

`PLAN.md` 步骤 1 Gate 与 §8 写的是 `465 passed, 23 skipped`。本工作树实测：

```
463 passed, 25 skipped in 23.88s
```

差的 2 个是 `tests/py/test_ssim_scalar.py` 的两个用例，因为本机没装 `scikit-image` 而 skip。
换句话说 465/23 是在装了 `scikit-image` 的机器上记的。

**做法**：所有门槛改用"**skipped 数量不变（25），passed 只增不减**"表述，
不写死绝对值。Task 0 Step 1–2 把这个基线连同 25 个 skip 的成因一起冻结进提交信息。

### R-3 · `artifact_kind` 加错了地方

spec 步骤 1 写"修改 `scripts/harness/contracts.py`：`RunSpec` 增加 `artifact_kind`"。
但 `RequiredArtifact.kind` 已经存在（`contracts.py:26`），`RunSpec.required_artifacts` 也已经
是 `tuple[RequiredArtifact, ...]`。真正缺的是**从 matrix JSON 传下去的通道** ——
`run_matrix.run_one` 把 `kind="hrsc_binary"` 写死了。

**做法**：Task 3 把字段加在 `MatrixRun` 上，`contracts.py` 只加
`FailureCategory.RESOURCE_EXHAUSTED`（Task 5）。这样避免在 `RunSpec` 上造一个与
`RequiredArtifact.kind` 语义重叠的第二个字段。

### R-4 · JSON 配置会被 cfg 覆写逻辑静默损坏（spec 未覆盖）

`materialise_run_config` 无条件把 `output_format=binary` / `output_file=...` 以
`key = value` 行的形式塞进 `run_dir/config.cfg`。LLM 负载的配置是 JSON，
被这套逻辑碰过就成了非法 JSON —— 而且**不会报错**，会等到负载脚本解析时才炸。

**做法**：Task 2 加可选 `config_filename`，非 `.cfg` 时逐字复制并对 `extra_cfg` fail-closed。
这是相对 spec 的一处小扩展，默认值保证 HRSC 路径逐字不变。

### R-5 · 工作树是脏的，会污染每一条新证据的 provenance（**最高优先级**）

`git status --porcelain` 当前 348 行：339 个删除 + 7 个修改 + `pytest.ini` 与 `docs/aiinfra/`
未跟踪，合计 `346 files changed, 227 insertions(+), 96478 deletions(-)`。
`runner.git_provenance` 把 `dirty` 写进**每一条** run record。在这个状态下跑出来的证据包，
provenance 全是 `dirty: true`。

另：`pytest.ini` 未跟踪意味着**新克隆和 CI 都拿不到 `--basetemp=.pytest_tmp`**，
而 `docs/INDEX.md` §8 明确记录过这台机器上默认 basetemp 会导致上百个 `WinError 5` setup error。

**做法**：Task 0 前置，提交工作树并把 `pytest.ini` 纳入版本控制，然后验证
`git_provenance(...)['dirty'] is False` 才开工。

### R-6 · spike 的三种结局会改矩阵口径，可能导致返工

`PLAN.md` §4 说 L2 不通过时"矩阵改报**复现率**而非二值"。如果 `determinism.py` 只报唯一输出数，
L2 不通过就要回头改测量代码与已产出的结果格式。

**做法**：Task 7 的 `measure_cells` 从第一天就**同时**报 `unique_output_count`（headline）
与 `reproduction_rate`（回退口径），并写进 `result_schema` 的必填字段。三种结局都不需要改代码。

### R-7 · `run_matrix.py` 在第一个失败的格子上中止，不能驱动破坏矩阵

`run_one` 末尾是 `raise RuntimeError(...)`，`run_matrix` 用列表推导顺序执行 —— 任何一格失败，
整个矩阵停在那里。而 E3 破坏矩阵里"大 batch OOM""vLLM 装不上"是**预期会出现且必须记录**的格子。

**做法**：
1. Task 8 的已提交冒烟矩阵只放会成功的格子；预期失败的格子由 pytest 直接驱动 `run_one`
   并检查落盘的 `metadata.json`（metadata 在 raise 之前已经写了，所以记录不会丢）。
2. Task 20 用包专属驱动 `scripts/aiinfra/breakage_matrix.py`，形态照抄仓库已有的
   `scripts/regression/mhd_week18_resolution_ladder.py`（"记录不完整组与数值失败而不是丢掉它们"）。

### R-8 · `PLAN.md` §1 的一句 headline 没有已提交证据支持

"恢复编译器默认值造成的位移，**比把工作精度砍半还大**"。逐条核对已提交的 summary：

| 想比较的量 | 实际能拿到的 | 问题 |
|---|---|---|
| fmad 造成的位移 | OT 256² fp32 ρ `L∞ = 2.074e-05`；fp64 `2.309e-14` | 有 |
| "精度砍半"造成的位移 | 只有 `week18/kh_solver_timing` 的 `Linf_rho_fp32_vs_fp64`（HLL `1.786e-06`） | **算例是 KH，不是 OT/Brio–Wu** |
| 用 ULP 比 | `matrix_summary_report` 对跨精度对返回 `None` | **跨精度 ULP 无定义** |

也就是说这个比较要么跨算例（混杂），要么跨精度（无定义）。`docs/INDEX.md` §9 记录过
同一类事故（一对没有 summary 支持的 OT GPU 加速比 `5.965×/6.353×` 被published 后又撤回）。

**做法**：Task 11 明确把这句话列为"不要写进 README 的一句话"，并写了一个测试
（`test_readme_does_not_repeat_the_unsupported_precision_comparison`）把它锁住。
README 只写四条**逐个来自单一 summary** 的事实。
**若想保留这个 headline，需要新增一个同算例的 fp32-vs-fp64 packet** —— 那是一个独立的小任务，
不在本计划范围内，建议单独排。

### R-9 · 步骤 2 的 CI 按字面实现不可行

spec 步骤 2："读 `precexp_aggregate.py` 输出的显著位数，与存档 baseline 比较……算例为 1D Brio–Wu，n=10"。
两个问题：

1. `precexp_aggregate.py` 的输入来自 Verificarlo VPREC 探索。已提交证据
   （`experiments/report2_w16_verificarlo_findings/`）记录 MCA 参考后端比原生慢 **≈417×**
   （24.0 vs 0.0575 s/step）。放进 per-push CI 不可行。
2. "n=10"有歧义：网格 `nx=10`，还是 MCA 10 个样本？

**做法**（Task 13，并把假设写在 workflow 注释里）：
- 阻塞门禁 = 两层的确定性检查（同机器位级重复 + 跨机器容差），算例取 `nx=10` 的 Brio–Wu，
  秒级完成。按"网格 10 格"这一读法实现。
- `precexp_aggregate` 的显著位数比较放进同一 workflow 的 `workflow_dispatch` 手动作业，
  它**不会在任何 push 上运行**，所以不会造成假绿。
- 跨机器那一层**必须用容差不能用位级**：参考是本机 MSVC 19.51，CI 是 GCC/Linux，
  位级门禁会 100% 假阳性。容差**实测再写死**（Task 13 Step 5），不许拍脑袋，
  并在参考 JSON 里写 `tolerance_basis` 说明它怎么来的。
- spec 要求的"假阳性 0"由 Task 13 Step 6 验证：注入 5% 扰动必须变红，
  未扰动连跑 3 次必须全绿。

### R-10 · 证据包清单校验有两处会挡住 `experiments/aiinfra/`

1. `experiment_manifest.py:104` 写死 `report != "report2"` → Task 9 放宽为集合。
2. `pipeline` 要求 **6 个阶段全部非空且指向现存的普通文件**。环境探针包没有图。
   → Task 14 让 `pipeline.plot` 指向 `summary.md`（人读的那份），而不是造一张没有意义的图。

另外核对了一处 spec 措辞：§8 说证据包要"带 lifecycle 状态、`claim_boundary`、SHA-256 产物清单"。
`claim_boundary` **不是** manifest 的字段（`TOP_LEVEL_FIELDS` 里没有），仓库现有 19 个包
一律把它放在 `summary.json` 里。本计划照现状放 `summary.json`，不去扩 manifest schema。

### R-11 · 两个 `ulp_max` 同名不同义，不要统一

- `scripts/regression/mhd_gpu_fma_axis.py:55` — 符号调整单调整数映射的**位模式距离**（int）
- `scripts/regression/matrix_summary_report.py:394` — `max|Δ| / (eps × max|left|)` 的
  **eps 归一化相对量**（float），且跨精度返回 `None`

spec 只要求提取前者。**做法**：Task 18 只提取前者到 `scripts/metrics/ulp.py`，
并在模块 docstring 里写明"这不是 `matrix_summary_report._ulp_max`"，
测试里断言 `mhd_gpu_fma_axis.ulp_max is metrics.ulp.ulp_max`，同时跑
`test_matrix_summary_report.py` 确认后者未被波及。

### R-12 · `experiments/` 全量被 gitignore

`.gitignore:24` 是 `experiments/`（整目录）。现有证据包都是 `git add -f` 进来的。

**做法**：Task 13/14/17/20 的提交步骤全部显式写了 `git add -f`，并且只加
manifest / summary / figures / session JSON —— **模型权重放 WSL 家目录 `~/models/`，
永不进树**。

### R-13 · 显存边界（8,151 MiB）已算进配置

0.5B fp16 权重约 1 GB。`batch=32 × 256 tokens` 的 KV cache 在 0.5B 上是几百 MB 量级，
安全。但 **fp32 权重就是 2 GB**，`batch=32` 的激活会明显吃紧。

**做法**：Task 20 的矩阵里 `float32` 只跑到 `batch=8`。真 OOM 也不是问题 ——
它会被记成 `resource_exhausted` 的格子，本来就是要记录的量。

### R-14 · vLLM 拿不到完整词表 logits

离线 `LLM.generate` 只暴露 top-k logprobs。完整 `(vocab,)` logits 只有 eager 路径有。

**做法**：Task 19 让 `VllmOfflineBackend` 在 `capture_logits=True` 时抛
`unsupported_capability`，本地噪声地板与保真度只在 `torch_eager` 上做（ADR-3 本来就把 eager
定为黄金参考），vLLM 的保真度作为**明确的能力缺口**记录，留给集群侧用 top-k logprob 路径补。

### R-15 · 只留第一个生成 token 的 logits，是刻意的取舍

Qwen2.5 词表约 151k。`(batch=32, steps=256, vocab=151k)` 的 float32 是 ~6 TB。
第一个生成位置的 `(vocab,)` 是 ~600 KB。

**做法**：Task 19 只捕获第一个位置，并把这个边界写进 `claim_boundary`。

### R-16 · 计时协议缺 warm-up（spec §6 明确要求）

spec 步骤 3 说"计时协议复用 `experiments/week18/kh_solver_timing` 的 warm-up + repeats +
median/IQR 形态"。初稿的 `measure_cells` 只有 repeats + median/IQR。

**做法**：已在 Task 7 补上 `WARMUP_CALLS = 1`，warm-up 的**延迟与 digest 都丢弃**，
与 `kh_solver_timing` 的 `warmups_per_group: 1` 对齐。丢 digest 是刻意的：
冷启动差异属于加载路径，不是推理不确定性 —— 这一点写进了函数 docstring。

---

## 自检清单（writing-plans 要求的三项）

**1. spec 覆盖**

| spec 条目 | 落在哪 | 状态 |
|---|---|---|
| 步骤 1 · `arguments` 数组 | Task 1 | ✅ |
| 步骤 1 · `artifact_kind` | Task 3（位置调整见 R-3） | ✅ |
| 步骤 1 · `RESOURCE_EXHAUSTED` | Task 5 | ✅ |
| 步骤 1 · `kind=workload completed/expected` | Task 5 | ✅ |
| 步骤 1 · `workload_result` 校验器 | Task 4 | ✅ |
| 步骤 1 · `scripts/aiinfra/{config,result_schema,environment,prepare_assets,backends/{base,fake}}` | Task 4/6/7/14 | ✅ |
| 步骤 1 · `configs/aiinfra/models.json` | Task 6（Qwen 条目在 Task 14 填真值） | ✅ |
| 步骤 1 · 新增 4 个 `tests/py/test_aiinfra_*.py` | Task 1/4/6/7 | ✅（另加了 4 个） |
| 步骤 1 · Gate 1–4 | Task 10 | ✅ |
| 步骤 2 · 根 README | Task 11 | ✅ |
| 步骤 2 · 数值回归 CI | Task 12–13（口径调整见 R-9） | ✅ |
| 步骤 0 · spike 配置与 L0/L1/L2 | Task 16 | ✅ |
| 步骤 0 · 三种结局预案 | Task 16 `outcome_plan` + Task 17 Step 5 | ✅ |
| 步骤 3 · `determinism/fidelity/noise_floor` | Task 7/19/20 | ✅ |
| 步骤 3 · `backends/{torch_eager,vllm_offline}` | Task 15 | ✅ |
| 步骤 3 · 复用 ULP、噪声地板判据、计时协议 | Task 18 / Task 19 / Task 7（R-16） | ✅ |
| 步骤 3 · E3 破坏矩阵 | Task 20（本地子集，未覆盖轴显式声明） | ✅ 部分 |
| 步骤 3 · E4 保真度与地板 | Task 19 + Task 20 Step 7 | ✅ |
| §8 五条验证命令 | Task 21 | ✅ |
| §8 端到端判据（manifest + lifecycle + claim_boundary + SHA-256） | Task 21 Step 6 | ⚠️ 见下 |

**唯一未覆盖项**：§8 端到端判据里的"**SHA-256 产物清单**"。仓库现有做法是包专属分析脚本
自己算（例如 `euler_openmp_thread_axis` 的 `implementation_sources` / `*_binary_sha256`），
manifest schema 里没有这个字段。本计划的三个 aiinfra 包记录了模型 revision、容器 digest、
git commit，但**没有对脚本与配置做 SHA-256 清单**。

**建议**：把它作为一个独立小任务排在 Task 21 之后 —— 在 `breakage_matrix.py` 与 `spike_run.py`
里加一个 `_source_hashes()`，对自身脚本 + 配置 + 判据文件算 SHA-256 写进 summary。
我没有把它塞进现有任务，因为它跨三个包、有自己的测试，够一个独立任务。

**2. 占位符扫描**：全文搜过 `TBD` / `TODO` / `implement later` / `add appropriate error handling` /
`similar to Task N` —— 无。唯一两处刻意留空：
- `configs/aiinfra/models.json` 的 Qwen `revision`（Task 14 Step 4 解析真值再填）；
- `numerical-regression.yml` 的 `verificarlo-precision-bits` job（依赖 ADR-13 的容器 digest，
  且被 `if: workflow_dispatch` 挡住，不会造成假绿）。
**这两处都是"不许编造事实"，不是"没想清楚"** —— 编一个假的 model sha 比没有 sha 更糟。

**3. 类型一致性**：跨任务核对过的接口 ——
`MatrixRun.{arguments, config_filename, artifact_kind}`（Task 1/2/3 → Task 8）·
`build_command(run, config)`（Task 1 → Task 1 Step 3）·
`result_schema.{SCHEMA, CELL_FIELDS, build_workload_result, validate_workload_result}`
（Task 4 → Task 7/8/17）· `WorkloadConfig` 全部 11 个字段（Task 6 → Task 7/20）·
`GenerationRequest.capture_logits`（Task 19 → Task 19 三个后端）·
`Backend.describe()` 的四个键（Task 7 → Task 4 的 `BACKEND_FIELDS`）·
`measure_cells` 返回的 8 个键 == `result_schema.CELL_FIELDS`（Task 7 → Task 4）·
`spike_evaluate.{evaluate, combine_sessions}`（Task 16 → Task 17）·
`metrics.ulp.ulp_max`（Task 18 → Task 19）。
一处修正：`Task 20` 的 `breakage_matrix` 直接构造 `WorkloadConfig`，所以 Task 6 的 dataclass
必须允许按关键字构造全部字段 —— 已确认 `@dataclass(frozen=True)` 满足。

---

## 风险与依赖

| 风险 | 触发点 | 预案 |
|---|---|---|
| WSL 里 torch 不支持 `sm_120` | Task 14 Step 3 | 停在那里查驱动；实在不行退到 CPU 后端跑通代码路径，GPU 结论标为未取得 |
| vLLM 装不上 `sm_120` | Task 14 Step 2 | spike 退化为 eager-only，vLLM 格记 `unsupported_capability`。**不是失败** |
| 容器在 `sm_120` 上跑不通 | Task 14 Step 1 | 触发 ADR-13 第二分支：软件栈升为显式轴，写进 `ENVIRONMENT.md`，此后所有跨平面比较带标注 |
| HRSC 在 GCC/Linux 上编译不过 | Task 13 Step 5 | 把编译错误记录下来，把该 job 降为 `continue-on-error` 并注明原因，**不删掉假装没这回事** |
| spike 落到 L0/L1/L2 不通过 | Task 17 | 四种 headline 文案已在 Task 17 Step 5 预写；Task 17 Step 9 强制停下来交给人 |
| 8 GB 显存不够 | Task 17 / Task 20 | fp32 只到 batch=8；OOM 记为 `resource_exhausted` 格子 |
| 本机跑 spike 时被别的进程抢显存 | Task 17 Step 2 | 跑前 `nvidia-smi` 快照存进 `summary.md`，与集群共租户纪律一致（ADR-10） |

**本计划不依赖**：`csc-mphil-gpu` 权限、lovelace、集群探针、A30、5090、7B 模型、nvcc、
云 GPU。任意时点中断，已完成的任务都是完整可交付的资产。

---

## 验证方式（整份计划完成后的一次性检查）

```bash
# 1. 回归：现有 HRSC 路径未被破坏
python -m pytest tests/py -q                      # 0 failed, skipped 仍为 25
./build-double/unit_tests -r compact

# 2. 加性泛化：假负载走通新路径
python scripts/run_matrix.py configs/aiinfra/smoke/fake_workload.json

# 3. 环境探针（只读，不装包不下载）
python scripts/aiinfra/environment.py --json

# 4. 确定性冒烟（本地 0.5B）
python scripts/aiinfra/determinism.py --config configs/aiinfra/smoke/determinism.json

# 5. 实验清单审计
python scripts/audit_experiments.py --format markdown

# 6. 三个新证据包都通过清单校验
python -c "
import sys; sys.path.insert(0, '.')
from pathlib import Path
from scripts.harness.experiment_manifest import validate_manifest
for name in ('env_probe_local', 'spike_determinism_0p5b', 'p1a_breakage_matrix_local'):
    print(name, validate_manifest(Path('experiments/aiinfra')/name/'manifest.json', Path('.')))
"

# 7. 工作树干净，provenance 不脏
git status --porcelain
```

---

*Plan written 2026-08-25. Spec: `docs/aiinfra/PLAN.md` (design review passed 2026-08-24).*
