# 第 18 周导师会议汇报

> 生成日期：2026 年 7 月 24 日。本文档严格沿用第 14 周导师会议稿的讲述形式。
> 所有数值均已与所列出的 `summary.json` 核对。当前证据状态以
> `docs/experiment_logs/report2_evidence_map.md` 为准。
>
> 本周完成第 16/17 周证据收尾，并新增 **100 次本机求解器执行**：72 次鲁棒性
> 运行、4 次与 CSC smoke 完全同配置的确定性对照，以及 24 次 KH 计时执行
> （4 次 warm-up 加 20 次正式计时）。CSC 原生 Verificarlo 管线还完成了
> HLL/HLLD、p53/p24 共 16 个缩小案例样本网格。完整 256^2、t=1.0、N=30
> Kelvin-Helmholtz MCA 仍是独立 CSC 任务。

---

## 一句话总结

核心结果仍然是：**精度是目前观察到的主导误差轴**。CSC 原生 Verificarlo
smoke 现在提供了独立随机证据：HLL/HLLD 的四个字段中，p24 spread 是 p53 的
2.71e8-4.24e8 倍；完全同配置的本机 FP32/FP64 差异与 p24 spread 的比值为
0.20-2.18，处于同一数量级。GPU 重复计时、硬件/线程 0 ULP 结果和 CFL
非单调性继续作为鲁棒性支撑。新增五重复 KH 计时表明，FP32 对 HLL
和 HLLD 分别加速 1.181 倍和 1.154 倍，而 HLLD 比 HLL 慢 14.7%-17.3%。

---

## 我们实际完成的工作

1. **用重复测量补全硬件轴。** 对经过验证的 HLL CPU/GPU 矩阵进行五次重复，
   覆盖 Brio-Wu 与 Orszag-Tang 的 float 和 double。报告现在使用中位数和
   四分位距，不再依赖单次 wall time。
2. **增加二维线程复现性实验。** 使用 `OMP_NUM_THREADS = 1, 2, 4, 8`，
   分别以 float 和 double 运行 Orszag-Tang 与 Kelvin-Helmholtz，并与同案例、
   同精度的单线程结果比较。
3. **增加 Kelvin-Helmholtz CFL 梯度。** HLL 与 HLLD 分别在
   CFL = 0.2、0.4、0.6、0.8 下以 float 和 double 运行。这在不修改标准
   `kh.cfg` 的情况下，将时间步敏感性与精度比较分开。
4. **整合第 16 周 Kelvin-Helmholtz 证据。** HLL 与 HLLD 均已有完整的
   24 变体确定性矩阵，并通过 256^2 相对 512^2 的验证门。
5. **保留意外的时间发散结果。** 固定窗口拟合没有观察到原计划的
   Orszag-Tang 大于 Brio-Wu 的排序。该结果作为有边界的负结果报告，不予删除。
6. **验证 CSC 原生 Verificarlo 路径。** CSC 没有 Docker 或 Apptainer，
   因此直接使用已安装的 Verificarlo 2.4.0 与 clang 18.1.3。HLL/HLLD x
   p53/p24 四个 block 均完成 N=4 样本。
7. **运行完全匹配的本机交叉验证。** 以 CSC 的 64^2、t=0.05 配置，在本机
   运行 HLL/HLLD 的 FP64 与 FP32。四次运行均以 15 步完成并保持有限正状态。
8. **量化 MCA 成本并纠正执行模型。** 短测中 quad MCA 为 24.0 s/step，
   native 为 0.0575 s/step，即 417 倍开销。30 个样本由 32 个 worker 并发，
   p53 与 p24 分开提交，以便在 6 小时上限下保留余量。
9. **视觉复核后重新生成图。** 零 ULP 明确标注；新增 MCA 图分别表达噪声层、
   确定性对照与执行成本，避免混用口径。
10. **增加受控 KH 运行时间比较。** HLL/HLLD x FP64/FP32 固定为
   256^2、t=1.0、CFL=0.4、单 OpenMP 线程。每组一次 warm-up 后正式
   测量五次，全部重复输出均为 0 ULP。

---

## 图应该如何阅读、它们说明了什么

每张图先给出**一句话结论**，随后说明**如何阅读**以及结论边界。

### A - 哪个实验轴影响最大？ `experiments/week17/paper_figures/fig_w17_axis_synthesis.png`

- **一句话：****精度仍然是目前观察到的主导轴**；编译器选择是次要因素，而
  已覆盖的硬件轴改变性能但不改变保存下来的数值结果。
- **如何阅读：**该图对第 17 周综合包收集到的最大密度差异进行排序。在现有
  证据中，double 的最大 \(L_\infty(\rho)\) 差异为
  \(8.84\times10^{-12}\)，float 最大达到 \(3.12\times10^{-3}\)。
  最大 fast-math 变化为 \(6.45\times10^{-7}\)，`<=` 与 `<` 分支的最大
  变化为 \(4.93\times10^{-7}\)。
- **它说明什么：**尺度差异并非来自单一案例。当前证据中，改变数值精度所产生
  的差异显著大于编译选项或分支实现差异，因此可以作为 Report 2 的核心结论。
- **边界：**这只是对已提交 W15-W18 证据包的有界排序，不是适用于所有 HRSC
  方法、编译器或硬件的普遍定理，也不会提升 evidence map 中 provisional 行。
- **权威数据：**`experiments/week17/report2_synthesis/summary.json`。

### B - GPU 结果是否可复现，加速是否可靠？ `experiments/week18/supplemental/hardware_repeats/figures/hardware_repeats.png`

- **一句话：**已覆盖的 CPU 与 GPU HLL 解仍然保持 **0 ULP 位级一致**；
  五次重复确认只有二维大问题具有显著 GPU 收益。
- **如何阅读：**面板 (a) 给出 CPU wall time 中位数除以 GPU wall time
  中位数；误差棒表示五个配对加速比的四分位范围。虚线 1 表示速度相同。
  面板 (b) 给出同精度最大 ULP 距离，并明确标出每一个零值。
- **具体结果：**Orszag-Tang 的 double 中位加速为 **6.17 倍**，float 为
  **5.92 倍**；对应 CPU/GPU 中位时间分别为 27.51/4.46 s 与
  20.97/3.54 s。Brio-Wu 在 double 和 float 下只有 0.51 倍和 0.49 倍，
  说明一维小问题中 kernel 启动和传输开销占主导，GPU 反而更慢。
- **它说明什么：**硬件结论现在由重复计时而非单次运行支持。对于较大的二维
  工作负载，硬件是强性能轴；但在已覆盖的 HLL 路径中，它不是精度分离轴。
- **边界：**不覆盖 GPU 上的 HLLD、GPU 上的 Kelvin-Helmholtz、GPU MCA、
  多种 GPU 型号或广泛性能矩阵。
- **权威数据：**`experiments/week18/supplemental/hardware_repeats/summary.json`。

### C - OpenMP 线程数会改变解吗？ `experiments/week18/supplemental/thread_repro/figures/thread_repro.png`

- **一句话：****不会。**全部 16 个二维比较在 1、2、4、8 线程下均位级一致。
- **如何阅读：**面板 (a) 是四乘四网格：Orszag-Tang 与 Kelvin-Helmholtz，
  每个案例包含 double 和 float，并比较四种线程数。每个单元格均为
  `0 ULP`。面板 (b) 给出相对单线程的 wall time。
- **具体结果：**所有运行均以相同步数完成并保持有限正状态；最大 ULP 距离和
  最大绝对差异均严格为零。运行时间始终位于单线程基准约 3.5% 以内，因此
  当前构建没有表现出有意义的线程扩展。
- **它说明什么：**已测试的 OpenMP 循环结构没有在保存字段中引入线程顺序
  变化。这一证据独立于 CPU/GPU 比较，进一步加强复现性论证。
- **边界：**这是单台工作站、已覆盖 HLL 案例的 OpenMP 结果，不能证明 MPI
  reduction 顺序可复现；近乎不变的计时也不作为 OpenMP 性能结果。
- **权威数据：**`experiments/week18/supplemental/thread_repro/summary.json`。

### D - 改变 CFL 会改变精度结论吗？ `experiments/week18/supplemental/kh_cfl/figures/kh_cfl.png`

- **一句话：**CFL 会改变 fp32/fp64 差异的大小，但响应是**非单调的**；
  减小 CFL 并不会自动减小浮点漂移。
- **如何阅读：**面板 (a) 显示 HLL 和 HLLD 在四个 CFL 下最终
  \(L_\infty(\rho)\) 的 fp32/fp64 差异。面板 (b) 显示 fp64 步数；
  HLL 和 HLLD 的步数重合，依次为 2296、1148、766、574。
- **具体结果：**HLL 在整个梯度中为 **8.91e-7** 至 **4.68e-6**；
  HLLD 为 **3.16e-6** 至 **7.20e-6**。全部 16 次运行均完成并保持有限
  正状态。在标准 CFL 0.4 下，HLL 与 HLLD 的差异分别为
  \(1.79\times10^{-6}\) 与 \(3.23\times10^{-6}\)。
- **它说明什么：**时间步选择会调制累积浮点差异；在本案例所有被测 CFL 下，
  更复杂的 HLLD 波扇差异均大于 HLL。非单调曲线反驳了“更多时间步总会改善
  精度一致性”的简单说法。
- **边界：**单一网格、单一终止时间上的四个 CFL 不能建立时间收敛阶，也不能
  建立一般性的 HLL 与 HLLD 精度排名。
- **权威数据：**`experiments/week18/supplemental/kh_cfl/summary.json`。

### E - Kelvin-Helmholtz 现在是否已成为完整精度案例？ `experiments/week17/paper_figures/fig_w16_kh_precision_mca_boundary.png`

- **一句话：**Kelvin-Helmholtz 的确定性矩阵已经完整，缩小版 MCA 显示预期的
  p24/p53 分离，但完整 **256^2、t=1.0、N=30 MCA 仍不作结论**。
- **如何阅读：**确定性面板将 HLL 和 HLLD 的全部 24 个 CPU 构建变体与同网格
  fp64 参考比较。HLL 的 double 约为 \(2.00\times10^{-15}\)，HLLD 的
  double 约为 \(9.99\times10^{-15}\)；HLL 的 float 位于
  \(1.79\)-\(1.82\times10^{-6}\)，HLLD 位于
  \(3.23\)-\(4.32\times10^{-6}\)。
- **MCA smoke 结果：**在 64^2、t=0.05、N=30 的缩小问题中，HLL 密度 spread
  从 p53 的 \(8.86\times10^{-16}\) 增至 p24 的
  \(8.28\times10^{-8}\)；HLLD 从 \(9.03\times10^{-16}\) 增至
  \(2.75\times10^{-7}\)。
- **验证背景：**独立的 256^2 相对 512^2 门通过，指标为
  \(L_1(\rho)=1.836\times10^{-3}\)、质量相对误差为零、
  \(\mathrm{div}B_{\max}=6.714\times10^{-4}\)。
- **边界：**缩小版 MCA 只能证明工具链可行性和噪声层分离方向，不能替代完整
  尺度、完整终止时间的随机实验。
- **权威数据：**`experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json`、
  `experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json` 和
  `experiments/week16/kelvin_helmholtz_precision/validation/summary.json`。

### F - 混沌二维案例的发散是否更快？ `experiments/week15/mhd_temporal_divergence/figures/temporal_divergence.png`

- **一句话：****没有观察到原计划的对比。**在固定拟合窗口内，Brio-Wu 的
  fp32/fp64 拟合增长率远大于 Orszag-Tang。
- **如何阅读：**曲线显示密度漂移随时间变化；拟合线使用预先规定的窗口：
  Brio-Wu 为 [0.01, 0.1]，Orszag-Tang 为 [0.1, 0.5]。共有 15 个
  Brio-Wu 配对样本和 25 个 Orszag-Tang 配对样本，由 80 次具有完整 provenance
  的运行生成。
- **具体结果：**Brio-Wu 的 L1 拟合率为 **30.615**，Orszag-Tang 只有
  **0.0293**。Orszag-Tang 在固定窗口内的 \(L_\infty\) 拟合率为负，
  即 \(-0.0422\)。
- **它说明什么：**视觉上混沌的二维案例并不自动具有更大的短窗口精度发散率。
  这是有价值的负结果，因为它阻止报告将形态复杂性直接解释成未被证据支持的
  精度敏感性。
- **边界：**这些是确定性 fp32 相对 fp64 扰动的 Lyapunov-like 工程拟合，
  不是正式最大 Lyapunov 指数或物理不稳定增长率；拟合质量也没有独立门控。
- **权威数据：**`experiments/week15/mhd_temporal_divergence/summary.json`。

### G - 最终哪些证据门已经关闭？ `experiments/week17/paper_figures/fig_w17_gates_and_boundaries.png`

- **一句话：**硬件门、OT/KH 512 网格门、综合门和三个第 18 周鲁棒性门均通过；
  图中唯一明确的核心缺口是完整 Kelvin-Helmholtz MCA。
- **如何阅读：**正向 gate 标记表示具有完整机器可读行并通过检查的证据包；
  boundary 标记表示仍被排除的结论。
- **它说明什么：**OT 和 KH 的 256^2 相对 512^2 工程门都已通过，第 17 周
  综合包具有全部必需来源；新增的第 18 周综合补充门在 72/72 次运行成功后通过。
- **边界：**两个分辨率不能建立渐近收敛。完整 256^2、t=1.0、N=30 KH MCA
  在 CSC summary 同时给出 HLL/HLLD 的 p53、p24 completed 之前仍不作结论。
- **权威数据：**`experiments/week18/supplemental/summary.json` 和
  `experiments/week17/report2_synthesis/summary.json`。

### H - CSC 随机结果是否与确定性精度差异一致？ `experiments/week18/csc_findings_synthesis/figures/csc_mca_precision_triangulation.png`

- **一句话：****在缩小且完全匹配的案例上，一致。**p24 与 p53 相差
  8.43-8.63 个十进制数量级，本机 FP32/FP64 差异与 CSC p24 spread 处于
  同一数量级。
- **如何阅读：**面板 (a) 比较 HLL/HLLD 在密度、x 速度、横向磁场和压力上的
  p24 spread；面板 (b) 给出 p24/p53 放大倍数的十进制对数；面板 (c) 将本机
  确定性 FP32/FP64 Linf 与 CSC p24 MCA spread 对照，虚线表示两者相等。
- **具体结果：**p24/p53 比值为 **2.71e8-4.24e8**。HLLD 相对 HLL 的 p24
  spread 在 rho、vx、By、p 上分别为 3.00、4.10、1.94、1.46 倍。八个
  确定性/p24 比值位于 **0.20-2.18**，全部在一个十进制数量级内。
- **它说明什么：**两种独立方法对精度影响尺度给出一致证据；在该缩小配置的
  每个字段中，HLLD 的 MCA 敏感性都高于 HLL。
- **边界：**这是 64^2、t=0.05、MCA N=4。它验证 CSC 原生管线和求解器差异
  的方向，不能替代完整 KH 随机结论，也不能建立一般性的 HLLD 排名。
- **权威数据：**`experiments/week18/csc_findings_synthesis/summary.json` 与
  `experiments/report2_w16_verificarlo_findings/smoke_validation_64sq/`。

### I - CSC 长时间运行是否意味着求解器卡死？ `experiments/week18/csc_findings_synthesis/figures/csc_mca_cost_feasibility.png`

- **一句话：****不是。**进程持续执行 MCA 算术；长时间来自插桩开销，不是
  时间步崩塌、I/O 或锁等待。
- **如何阅读：**面板 (a) 比较 native IEEE、quad MCA、MCA-int MCA 与
  MCA-int random rounding 的每步时间；面板 (b) 给出并发 N=30 precision
  block 在专用节点上的 2.5-3.0 小时规划范围，并说明为什么 p53/p24 分开提交。
- **具体结果：**短测依次为 0.0575、24.0、11.43、6.25 s/step。MCA-int
  不支持所需的 p24 虚拟精度，因此为保持受控比较，p53 与 p24 都使用 quad。
- **边界：**登录节点计时用于衡量后端成本且受资源争用影响；2.5-3.0 小时是
  专用计算节点观测到的规划范围，不作为一般 Verificarlo 性能基准。
- **权威数据：**`experiments/report2_w16_verificarlo_findings/README_findings.md`
  及其原始计时日志。

### J - 精度与求解器选择的运行时间成本是多少？ `experiments/week18/kh_solver_timing/figures/kh_solver_precision_timing.png`

- **一句话：**FP32 带来幅度不大但可重复的 CPU 收益；在该 KH 配置中，
  HLLD 始终更慢，并且 FP32/FP64 密度差异更大。
- **如何阅读：**面板 (a) 是五次 end-to-end wall time 的中位数，误差棒从
  Q25 画到 Q75；面板 (b) 是无量纲 speed/cost ratio，虚线 1 表示没有差异；
  面板 (c) 将 FP32 中位时间与同求解器最大密度差异放在同一 accuracy-cost 图中。
- **测量结果：**HLL 的 FP64 为 **34.484 s（IQR 0.103 s）**，FP32 为
  **29.196 s（IQR 0.801 s）**；HLLD 分别为 **39.542 s（IQR 0.197 s）**
  与 **34.254 s（IQR 0.158 s）**。FP32 对 HLL/HLLD 分别加速 1.181/1.154
  倍；HLLD 在 FP64/FP32 下成本分别是 HLL 的 1.147/1.173 倍。
- **精度-成本解释：**FP32/FP64 密度 Linf 在 HLL 为 1.786e-6，HLLD 为
  3.230e-6。因此本次有边界比较中，HLL 更快且更接近自己的 FP64 基线；这不
  构成一般性的求解器排名。
- **为什么使用中位数/IQR：**wall time 会受操作系统调度影响而偏斜，五个样本
  不足以假设正态分布。中位数能抵抗单次慢运行，IQR 在不删除数据的情况下给出
  中间 50% 的离散范围。
- **边界：**计时包含进程启动、求解器执行和最终 binary output，回答“完成一次
  实验需要多久”，而不是 kernel-only throughput。单台工作站和一个 KH 配置
  不能建立跨机器性能可移植性。
- **权威数据：**`experiments/week18/kh_solver_timing/summary.json`。

## 每个报告指标如何计算

完整公式、实现路径、选择依据和解释边界见
`docs/week18/week18-metrics-methods-ZH.md`。简要阅读规则如下：

1. **Primitive fields：**从 conserved total energy 中减去动能与磁能后重建压力，
   使 rho、vx、By、p 成为可物理解读的比较字段。
2. **FP32/FP64 差异：**先做同网格逐点差。`L1_mean` 是平均绝对差，`L2_RMS`
   是均方根，`Linf` 是最大单元绝对差。FP64 是项目基线，不是精确解。
3. **ULP：**把 dtype 相同的 IEEE 值映射为有序整数并取最大整数距离。`0 ULP`
   表示逐 bit 相同；ULP 不是物理范数，也不用于不同 FP32/FP64 格式之间。
4. **MCA spread：**先在每个网格单元计算无偏样本标准差，再取空间最大值。
   per-cell-first 顺序避免空间平均抵消局部随机敏感性。
5. **MCA SNR：**样本均值场的平均绝对值除以逐网格样本标准差的平均值。它表示
   数值信号相对随机算术变化，不是物理湍流噪声。
6. **p24/p53 与 HLLD/HLL 比值：**其他设置完全固定时比较同类 spread；其
   log10 表示十进制数量级差，但不能自动解释为物理解损失的有效数字数。
7. **Wall time：**排除一次 warm-up，保留全部五次正式运行，报告中位数和
   `IQR=Q75-Q25`。FP32 speed-up 为 `median(FP64)/median(FP32)`；固定精度
   下 HLLD cost 为 `median(HLLD)/median(HLL)`。
8. **物理状态门：**所有值有限、最小密度为正、由 conserved state 重建的压力
   为正。通过只表示该运行可用于分析，不证明精度。
9. **divB：**内部网格中心差分磁场散度的平均绝对值与最大绝对值。它检查离散
   无散约束，不是 precision error。
10. **Gate pass：**矩阵完整、成功执行、物理检查、诊断和预设阈值的逻辑与；
    它永远不能扩大单独写明的 claim boundary。

---

## 可以向导师说明什么（以及不能说明什么）

**可以说明：**

- 在当前 Report 2 证据包中，精度是主导数值轴；编译选项和分支变化是次要因素。
- 对已覆盖的 HLL Brio-Wu 与 Orszag-Tang，CPU 和 GPU 在同精度下位级一致。
  五次重复给出二维 fp64 6.17 倍、fp32 5.92 倍的稳健中位加速。
- Orszag-Tang 与 Kelvin-Helmholtz 在两种精度和 1/2/4/8 OpenMP 线程下均
  位级一致。
- Kelvin-Helmholtz 的 fp32/fp64 差异在 CFL 0.2-0.8 范围内有限且较小，
  但呈非单调变化；在这个有边界实验中，HLLD 在每个 CFL 下都大于 HLL。
- 时间发散实验给出了有效负结果：没有观察到计划中的 Orszag-Tang 大于
  Brio-Wu 排序。
- OT 与 KH 的 256^2 相对 512^2 门可作为工程敏感性检查并已通过。
- CSC 原生 Verificarlo smoke 的四个 p53/p24 block 均完成；p24/p53
  spread 相差 8.43-8.63 个数量级，且匹配的确定性运行支持同一误差尺度。
- KH 256^2 五重复 CPU 计时给出 FP32 加速 1.181 倍（HLL）和 1.154 倍
  （HLLD）；HLLD 比 HLL 慢 14.7%-17.3%。20 次正式重复在各自
  solver/precision 组内全部为 0 ULP。

**不能说明：**

- 不声称正式 Lyapunov 指数、物理不稳定增长率、时间收敛阶或空间渐近收敛。
- 不声称 HLLD 在一般情况下精度更差或稳定性更差。
- 不把当前工作站和已覆盖 HLL 案例推广为一般 GPU 结论。
- 不声称 MPI 可复现。
- 不作完整 Kelvin-Helmholtz MCA 噪声层结论：完整
  **256^2、t=1.0、N=30 在 CSC 完成前仍不作结论**。

---

## 当前问题、影响与处理决定

| 问题 | 当前证据 | 对 Report 2 的影响 | 处理决定 |
|---|---|---|---|
| 完整 KH MCA 尚未完成 | CSC 已完成 64^2、t=0.05、N=4 native-Verificarlo smoke；尚未取得完整 256^2、t=1.0、N=30 四 block packet | 不能提升完整 KH 随机噪声结论 | 取回 HLL/HLLD x p53/p24 全部 summary，仅在 combined gate 通过后提升结果 |
| MCA 运行成本很高 | 短测中 quad MCA 为 24.0 s/step，native 为 0.0575 s/step，约 417 倍开销 | 完整矩阵不能按普通 solver sweep 串行执行 | 使用 32 workers 并发 30 个样本，并将 p53/p24 拆成独立 Slurm 任务以满足 6 小时限制 |
| 更快 backend 不支持 p24 | `mca_int` 拒绝 binary64 virtual precision 24 | p24 用 quad、p53 用 MCA-int 会混入 backend 差异 | p53/p24 均使用 quad；MCA-int 只保留给单独的 p53-only 研究 |
| N=4 统计强度不足 | p24/p53 分离很大且方向一致，但 CSC smoke 每个 block 只有四个样本 | 可支持方向与工具链有效性，不能支持窄置信区间或强 solver 排名 | smoke 只作为 validation；N=30 返回后增加 bootstrap/置信区间 |
| OT/HLLD 存在未解决的高分辨率稳定性边界 | 探索性 OT/HLLD/FP64 512^2 在 CFL 0.4 和 0.2 均出现负压力 | 该探索性 HLLD 分辨率阶梯不能作为收敛证据 | 不放入 KH 主结论；在作任何 HLLD 稳定性结论前，单独研究 failure time 与 positivity |
| FP64 不是精确解 | FP32 差异相对项目 FP64 baseline 计算 | precision sensitivity 不能称为绝对物理误差 | 全文统一使用“相对 FP64 baseline 的差异”，排除精确解声明 |
| 两个分辨率不足以证明渐近收敛 | 已提交 OT/KH gate 只比较 256^2 与 512^2 | 只能作为工程敏感性检查 | 不从这两个点报告正式收敛阶 |
| 历史 L1 口径不同 | 部分 deterministic packet 使用 `sum*dx`；新 256/512 gate 使用 mean-normalised L1/RMS | 不同 packet family 的 L1 不能直接合并 | 明确标注计算口径，跨 packet 主结论使用同网格 Linf |
| 性能证据范围较窄 | KH 计时只覆盖一台工作站、CPU、单线程、一个网格/案例；FP32 加速为 1.154-1.181 倍 | 不能建立跨机器 CPU/GPU 可移植性能 | 作为有边界 end-to-end 计时报告；多机器和 HLLD/KH GPU 计时列为 future work |
| 原计划时间发散排序没有出现 | 固定窗口拟合没有观察到 OT 比 Brio-Wu 增长更快 | 原假设不受支持 | 保留为负结果，不修改窗口或删除实验 |
| CSC 代码与证据仍需整合 | native runner、timeout、backend、partial-summary 修改保存在 CSC diff/findings 包，本地 worktree 存在重叠改动 | 直接应用补丁可能丢失本地或远端工作 | 逐文件整合，运行完整测试，再有意识地合并代码与证据 packet |

对汇报最重要的结论是：**确定性、计时、硬件、线程、CFL 和缩小版 CSC
smoke 可以在各自边界内汇报；完整 KH MCA 与 OT/HLLD 高分辨率稳定性结论
目前不能提升。**

---

## 下一步

1. **监控并取回已提交的完整 CSC 作业链。**作业 16440-16442 分别执行四个
   HLL/HLLD x p53/p24 block、packet 生成和 W17 综合。原生 runner 每个 block
   并发 30 个样本，不应重新提交已过时的 Apptainer 流程。
2. **仅在完整 gate 通过后提升 KH。**两个求解器都必须具有 completed 的
   p53 与 p24 N=30 block，才能更新 W17 综合和论文措辞；N=4 smoke 必须继续
   明确标为缩小范围证据。
3. **N=30 原始样本返回后增加不确定性。**为 spread、SNR 和 HLLD/HLL 比值
   报告置信区间或 bootstrap 区间；N=4 不足以支持强统计排名。
4. **优先综合，不再扩张低收益本机扫描。**匹配确定性实验已经完成。继续增加
   CFL、线程或一般分辨率扫描的报告价值，低于关闭完整 MCA 门并更新精度-成本
   Pareto 论述。
5. **保留负结果。**按实际测量报告固定窗口时间拟合，并将正式指数估计和 MPI
   顺序影响放入 future work。

---

## 参考文献

- Brio, M., and Wu, C. C. (1988). *Journal of Computational Physics*, 75,
  400. DOI `10.1016/0021-9991(88)90120-9`。
- Orszag, S. A., and Tang, C.-M. (1979). *Journal of Fluid Mechanics*, 90,
  129。
- Dedner, A., et al. (2002). *Journal of Computational Physics*, 175, 645。
  DOI `10.1006/jcph.2001.6961`。
- Miyoshi, T., and Kusano, K. (2005). *Journal of Computational Physics*,
  208, 315。HLLD 近似 Riemann 求解器。
- McNally, C. P., Lyra, W., and Passy, J.-C. (2012). *The Astrophysical
  Journal Supplement Series*, 201, 18。Kelvin-Helmholtz benchmark 与复现性背景。
- Denis, C., Castro, P., and Petit, E. (2016). Verificarlo：用于评估浮点精度的
  Monte Carlo Arithmetic 工具。

