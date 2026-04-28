# Week 4 Phase B / Phase C 手动验证清单

**日期**: 2026-04-28
**作用**: 在干净 checkout 上完整复现 Phase B（PrecisionConfig + BC）和 Phase C（float 全回归 + Verificarlo real-float）的产出，并逐项确认代码运行正常。
**适用前提**: WSL Linux toolchain（gcc/g++ ≥ 10，cmake ≥ 3.16，ninja，python ≥ 3.10，`numpy` `matplotlib` `scikit-image`）；不支持 MSVC（需要 GCC/Clang 才能展开 `#pragma omp` 与 `std::filesystem`）。
**约定**: 所有命令从 repo 根目录 `c:/Users/tangy/Desktop/floatpoint`（或 WSL 等价 `/mnt/c/Users/tangy/Desktop/floatpoint`）执行。

---

## 0. 一次性环境检查

| 检查项 | 命令 | 期望 |
|---|---|---|
| Git 分支 | `git rev-parse --abbrev-ref HEAD` | `week4-implementation` |
| Python 依赖 | `python -c "import numpy, matplotlib, skimage; print('ok')"` | `ok` |
| C++ 编译器 | `c++ --version` | gcc ≥ 10 或 clang ≥ 12 |
| Verificarlo（仅 Phase C2 需要） | `command -v verificarlo-c++` | 非空（WSL Docker 镜像） |

---

## 1. Phase B 验证（PrecisionConfig + 边界条件）

### 1.1 验收：两套精度 build 都成功

```bash
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double

cmake -B build-float  -G Ninja -DFLOAT_PRECISION=float  -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-float
```

**期望**:
- 两次 cmake 配置末尾打印 `-- HRSC precision: double` 和 `-- HRSC precision: float`
- 两个目录下都生成 `hrsc(.exe)`、`unit_tests(.exe)`、`libhrsc_euler.a`

### 1.2 验收：单元测试在两精度下都全绿

```bash
./build-double/unit_tests -r compact   # Windows: build-double\unit_tests.exe
./build-float/unit_tests  -r compact
```

**期望**: `Passed all 115 test cases with 3660 assertions.`（双精度与单精度数字一致）

### 1.3 验收：B2/B3 边界条件单测覆盖完整

```bash
./build-double/unit_tests "[boundary]"
```

**期望**: `All tests passed (572 assertions in 10 test cases)`，包括：

- `Outflow BC` × 4（X-ghost / Y-ghost / 1D 模式 / 角落）
- `Periodic BC` × 2（2D 双向 / 1D ny=1 无泄漏）
- `Reflective BC` × 2（X 法向 momentum 翻转 / Y 法向 momentum 翻转）
- `Reflective BC empty flip_indices`（pure-mirror 退化）
- `Reflective BC multi-index flip list (MHD-shaped)`（{1,5} flip 列表，验证 BC 对物理 agnostic）
- `Per-axis BC mix: X=periodic, Y=reflective`（dispatcher 混合模式）

### 1.4 验收：分离编译已生效

```bash
nm build-double/libhrsc_euler.a 2>/dev/null | grep -c "EulerSolver<double>::step"
nm build-float/libhrsc_euler.a  2>/dev/null | grep -c "EulerSolver<float>::step"
```

**期望**: 两个数都 ≥ 1（symbol 来自 `template class EulerSolver<...>;` explicit instantiation）。

### 1.5 验收：1D Sod 端到端 + float / double 数值合理性

```bash
./build-double/hrsc tests/cases/toro_1d/sod.cfg | tail -5
./build-float/hrsc  tests/cases/toro_1d/sod.cfg | tail -5
```

**期望**:
- 两个输出都以 `Finished: <N> steps, t = 0.2` 结尾（stderr）
- Stdout 末尾的 `x = 0.9975, rho = 0.125` 系列在 double 下与 Week 3 bit-identical（重要：B1 时间累加器改 `TimeReal=double` 不应回归 double 路径）
- float 路径在 ULP 量级偏移内（rho ≈ 0.125, p ≈ 0.1，u ≈ 0）

### 1.6 验收：BoundaryType 配置参数解析

`bc` 是 shortcut，`bc_x`/`bc_y` 单独 override；缺省 = `outflow`。临时 cfg 测试可加在任何现有 1D cfg：

```ini
bc_x = periodic
bc_y = outflow
```

跑 `./build-double/hrsc tests/cases/toro_1d/sod.cfg`，应**正常完成**（即使物理上 sod + 周期没意义，也只验证 dispatcher 不 crash）。

---

## 2. Phase C1 验证（float 全回归：1D Toro + 2D LW Config 3）

### 2.1 1D Toro 6 case 回归

**前提**: Phase B 验收通过（`build-double` 与 `build-float` 都已 build）。

```bash
bash scripts/float_regression_1d.sh
```

脚本步骤（用于人工对照）：
1. `mkdir -p experiments/week4/float_regression/1d`
2. 对 `sod toro2 toro3 toro4 toro5 stationary_contact` 各跑 `convergence_*.cfg`，分别用 `build-double/hrsc` 和 `build-float/hrsc`，输出到 `<test>_double.csv` / `<test>_float.csv`
3. 调 `python scripts/float_regression_report.py --mode 1d --input experiments/week4/float_regression/1d`

**期望产出**:
```
experiments/week4/float_regression/1d/
├── sod_double.csv    sod_float.csv
├── toro2_double.csv  toro2_float.csv
├── toro3_double.csv  toro3_float.csv
├── toro4_double.csv  toro4_float.csv
├── toro5_double.csv  toro5_float.csv
├── stationary_contact_double.csv  stationary_contact_float.csv
├── summary.md
└── summary.json
```

**手动检查**:
- 每份 CSV 至少 5 行（resolutions = 50, 100, 200, 400, 800），列序固定为 `# N dx L1_rho L2_rho Linf_rho L1_u L2_u Linf_u L1_p L2_p Linf_p`
- `summary.md` 表里每行 ratio（`L1_*_ratio` 等 = float/double）应 ≈ 1.0；显著大于 1.0（如 > 5）说明 float 路径在该 case 出现明显精度损失，需要看具体 N 是哪一档先 diverge
- 收敛律检查（任一 case，看 N=400 vs N=800 行，L1_rho 比应介于 1.5 ~ 2.0 之间，激波 first-order 极限）

### 2.2 2D LW Config 3 回归

**警告**: ref800 在双精度下 ≈ 20–40 分钟单核（800² × ~2000 步）。

```bash
bash scripts/float_regression_2d.sh
```

脚本步骤：
1. `mkdir -p experiments/week4/float_regression/2d`
2. 跑 `config3_ref800.cfg`（double，CFL=0.4 提稳）→ `reference_800.bin`
3. 对 `res in {200, 400}` 各跑 double + float，每次跑完 `cp candidate_${res}.bin {double|float}_${res}.bin`
4. 调 `python scripts/float_regression_report.py --mode 2d --input experiments/week4/float_regression/2d`

**期望产出**:
```
experiments/week4/float_regression/2d/
├── reference_800.bin           # ~25.6 MB（800×800×4 vars × 8B + 64B header）
├── double_200.bin   float_200.bin   candidate_200.bin
├── double_400.bin   float_400.bin   candidate_400.bin
├── phase_error_heatmaps/<label>/<label>_diff_{rho,u,v,p}.png   # 16 PNG
├── summary.md
└── summary.json
```

**手动检查**:
- `summary.md` 表 4 行（double_200 / float_200 / double_400 / float_400），列：`L1_rho L2_rho Linf_rho ssim_rho delta_x_shock delta_y_shock`
- 验收预期（合规即 OK，不要求 perfectly match）：
  - `ssim_rho` 全部 ≥ 0.95（视场结构与降采样 ref 接近）
  - `delta_x_shock` 与 `delta_y_shock` 在 dx 量级（200² → ≤ 0.005，400² → ≤ 0.0025）
  - L1_rho 随 N 翻倍约减半（first-order 收敛）
- `double_200_diff_rho.png` 与 `float_200_diff_rho.png` 视觉对比：差值热图应在 ±0.02 以内的 RdBu 色带；若 float 出现集中亮斑（远离激波线），警示精度损失局部化
- 视觉一致性：可在 Python REPL 用 `read_binary("…/reference_800.bin")[1][..., 0]` 取 rho 画 imshow，应与 Liska & Wendroff 2003 Fig 3 Config 3 视觉对应（中心区域形成准对称 4-shock 结构）

### 2.3 Phase C1 单元测试（SSIM 函数）

```bash
pytest tests/py/test_ssim_scalar.py -v
```

**期望**: 全绿；测试覆盖 `_ssim_scalar` 在 identical 输入返回 1.0、scikit-image 不可用时 fallback 到 NaN。

---

## 3. Phase C2 验证（Verificarlo real-float 编译 vs VPREC p24 模拟）

**前提**: Verificarlo 已 build（WSL + Docker 路径见 `docs/week3/verificarlo_setup.md`）。

### 3.1 单模式跑通（real-float）

```bash
./scripts/verificarlo_run.sh --real-float -t sod -n 5
```

**期望产出目录**: `experiments/verificarlo/runs_real_float_p24_mca/sod/run_001.txt … run_005.txt` + `reference_ieee.txt`。
**手动检查**: 每份 `run_*.txt` 列数为 5（x, rho, u, p, e），cell 数与 `tests/cases/toro_1d/sod.cfg` 中 `nx` 一致。

### 3.2 对比模式（real-float vs VPREC p24）

```bash
./scripts/verificarlo_run.sh --compare-float -t "sod stationary_contact" -n 30
python scripts/plot_real_vs_vprec.py \
    experiments/verificarlo/runs_compare_p24_mca/real_float \
    experiments/verificarlo/runs_compare_p24_mca/vprec_p24 \
    --tests sod stationary_contact
```

**期望产出**:
```
docs/week4/figures/real_float_vs_vprec/
├── sod_real_vs_vprec_sigdigits.png
├── stationary_contact_real_vs_vprec_sigdigits.png
└── real_vs_vprec_summary.json
```

**手动检查**:
- 两条曲线（`real_float` vs `vprec_p24`）应 substantially overlap（VPREC 是 valid float simulator，差异应小）
- summary JSON 中 `min_sig_digits` 在两种模式相对差应 < 1（绝对差异是衡量"VPREC 偏差"的核心数字）

---

## 4. 出问题时的常见排查

| 症状 | 可能原因 | 排查指令 |
|---|---|---|
| `Cannot open file for writing: <path>` | 父目录不存在（旧 build 未带 auto-create） | `cmake --build <dir>` 重 build；本仓库当前 commit 已修 |
| `unit_tests` 偶发 1-2 case fail（非 boundary）| OpenMP 线程相关 reduction 噪声 | `OMP_NUM_THREADS=1 ./build-*/unit_tests` 复跑 |
| 2D ref 跑超 60 分钟 | CFL 太松 / nx 太大 | 改 `config3_ref800.cfg` 的 `nx=ny=600`，CFL 保持 0.4 |
| `summary.md` 表里 ratio 出现 `inf` | double 该 norm 为 0（精确解恰好命中） | 信息正常，看其他列 |
| `skimage` 缺失 | `pip install scikit-image` 或在 `summary.md` 上方接受 WARN fallback |

---

## 5. 完整验收：一键产出（约 60–90 分钟，含 800² 参考）

```bash
# Step 1: builds（约 2 分钟）
cmake -B build-double -G Ninja -DFLOAT_PRECISION=double -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake -B build-float  -G Ninja -DFLOAT_PRECISION=float  -DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=ON
cmake --build build-double && cmake --build build-float

# Step 2: tests（约 30 秒）
./build-double/unit_tests -r compact && ./build-float/unit_tests -r compact

# Step 3: Phase C1 1D（约 1–2 分钟，6 case × 5 resolutions × 2 builds）
bash scripts/float_regression_1d.sh

# Step 4: Phase C1 2D（约 30–45 分钟，800² ref + 4 候选）
bash scripts/float_regression_2d.sh

# Step 5: 检查产出
ls experiments/week4/float_regression/1d/summary.md
ls experiments/week4/float_regression/2d/summary.md
```

完成后将 `experiments/week4/float_regression/{1d,2d}/summary.{md,json}` 与 `phase_error_heatmaps/` 一并提交（受 `.gitignore` 保护的中间 binary 不进 git）。
