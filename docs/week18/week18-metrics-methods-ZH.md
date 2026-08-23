# 第 18 周指标定义与解释依据

> 本附录定义第 18 周导师汇报使用的全部数值和性能指标。目的有两个：让每个数字都可以复算；避免某个指标被用于支持超出其定义范围的结论。

## 1. 记号与 primitive fields

每个 MHD 网格单元保存 conserved state：

\[
U=(\rho,\rho v_x,\rho v_y,\rho v_z,B_x,B_y,B_z,E,\psi).
\]

报告比较更容易物理解读的 primitive fields：

\[
v_x=(\rho v_x)/\rho,
\qquad
p=(\gamma-1)\left[E-\tfrac12\rho(v_x^2+v_y^2+v_z^2)-\tfrac12(B_x^2+B_y^2+B_z^2)\right].
\]

`rho` 和 `By` 直接取 conserved component 0 和 5。转换实现在 `scripts/metrics/mhd_fields.py`。与只比较总能量相比，密度、速度、磁场和压力都有直接物理含义。

## 2. 确定性 FP32 与 FP64 差异

对同一网格、同一终止时间上的字段 `q`，逐网格定义：

\[
d_j=q^{FP32}_j-q^{FP64}_j.
\]

FP64 是项目基线，不是精确解。

标准离散统计量为：

\[
L_{1,mean}=\frac{1}{N_c}\sum_j |d_j|,
\qquad
L_{2,RMS}=\sqrt{\frac{1}{N_c}\sum_j d_j^2},
\qquad
L_\infty=\max_j |d_j|.
\]

- `L1_mean` 回答典型网格单元的绝对差异有多大。
- `L2_RMS` 对中等偏大的误差赋予更高权重，同时仍是全局统计量。
- `Linf` 回答整个区域中最坏的局部差异有多大。

新的 CSC 交叉验证图和 KH 计时图使用 `Linf`。激波和剪切层中的局部极值很重要，而且该指标不随求和网格数量变化。`mhd_kh_2d.py` 与 `mhd_orszag_tang_2d.py` 的 256/512 工程门在 fine grid block-average 后使用上述 mean/RMS 定义。

历史确定性 precision packet 调用 `scripts/metrics/mhd_fields.py::field_norms`，其 `L1/L2` 使用仓库早期的 `sum*dx` 约定。这些值只适用于生成时的同网格比较，不能与 mean-normalised 的跨分辨率指标混用。因此跨 packet 的报告主结论优先使用 `Linf`。

## 3. ULP 距离与位级复现性

ULP 是 unit in the last place。对 dtype 相同的两个数组，先把 IEEE bit pattern 映射为保持数值顺序的整数，再逐点计算整数距离：

\[
ULP_{max}=\max_j |I(a_j)-I(b_j)|.
\]

`scripts/regression/mhd_gpu_hardware_axis.py::max_ulp_distance` 的符号位变换保证负数到正数之间仍保持正确顺序。

- `0 ULP` 表示每个保存的浮点值都逐 bit 相同。
- 非零 ULP 表示该数值局部指数尺度上的表示距离，不是物理误差范数。

ULP 用于同精度 CPU/GPU、线程数和重复运行比较。FP32 与 FP64 格式不同，因此二者之间不用 ULP。

## 4. MCA spread 与 SNR

对字段 `q` 的 `n` 个 Verificarlo 样本，先逐网格计算样本均值和无偏样本标准差：

\[
\mu_j=\frac{1}{n}\sum_{s=1}^{n}q_{s,j},
\qquad
\sigma_j=\sqrt{\frac{1}{n-1}\sum_{s=1}^{n}(q_{s,j}-\mu_j)^2}.
\]

报告中的 MCA spread 定义为：

\[
spread_q=\max_j \sigma_j.
\]

它表示区域中最敏感位置的随机舍入变化。对激波和剪切层使用最大值是保守选择，因为空间平均可能掩盖很小但敏感的区域。

CSC smoke 的 SNR 定义为：

\[
SNR_q=\frac{mean_j(|\mu_j|)}{mean_j(\sigma_j)}.
\]

只有分母严格为零时才使用 `sqrt(eps_float64)`。SNR 越大，说明字段幅值相对 MCA 波动越大。这是数值 signal-to-noise ratio，不是观测噪声或物理湍流 SNR。

密度均值 spread 为：

\[
\max_s mean_j(\rho_{s,j})-\min_s mean_j(\rho_{s,j}),
\]

用于检查随机算术是否改变全域平均密度。

这些计算位于 `scripts/metrics/mhd_fields.py`，逐网格标准差在 `scripts/metrics/snr_metric.py` 中使用 `ddof=1`。CSC smoke 只有 N=4，足以验证方向和工具链，但不足以给出窄置信区间。

## 5. 精度与求解器比值

p24/p53 放大倍数定义为：

\[
A_q=spread_q^{p24}/spread_q^{p53},
\qquad
D_q=\log_{10}(A_q).
\]

`Aq` 是噪声放大倍数，`Dq` 表示两种 spread 相差多少个十进制数量级。它不能直接等同于物理解“损失了同样数量的有效数字”。

HLLD/HLL p24 比值为：

\[
R_q=spread_{q,HLLD}^{p24}/spread_{q,HLL}^{p24}.
\]

案例、网格、终止时间、backend、虚拟精度和样本数均相同时，该比值隔离 solver path 敏感性；它只支持有边界的求解器比较。

确定性/MCA 交叉验证比值为：

\[
T_q=L_\infty(q_{FP32}-q_{FP64})/spread_q^{p24}.
\]

接近 1 表示两种独立方法识别出相同数值尺度。由于确定性舍入差异和随机样本 spread 是不同估计量，不要求严格相等。

## 6. 运行时间统计

harness 从求解器进程启动计时，直到进程完成并写出所需 binary output。它是一次完整实验的 end-to-end wall time，不是只测 kernel 的微基准。

每个 solver/precision 组先做一次不计入统计的 warm-up，再保留五个正式时间 `t1...t5`：

\[
t_{med}=median(t_i),
\qquad
IQR=Q_{75}(t_i)-Q_{25}(t_i).
\]

图中的非对称误差棒直接从 Q25 画到 Q75。使用中位数和 IQR，是因为 wall time 会受操作系统调度影响而偏斜，五个样本不足以支持正态分布假设。

性能比值为：

\[
S_{FP32}=t_{med,FP64}/t_{med,FP32},
\qquad
C_{HLLD}=t_{med,HLLD}/t_{med,HLL}.
\]

第一个比值大于 1 表示 FP32 更快；第二个大于 1 表示 HLLD 成本更高。CPU/GPU 加速采用相同逻辑，即 `CPU median/GPU median`。

所有计时比较必须固定案例、网格、终止时间、CFL、线程数和输出语义。KH 计时固定 `OMP_NUM_THREADS=1`、`256^2`、`t=1.0`、CFL=0.4。单台工作站五次重复不能推出另一台 CPU 上的性能。

## 7. 求解器诊断与门禁

### 物理状态门

只有全部 conserved values 有限并且

\[
\min_j \rho_j>0,
\qquad
\min_j p_j>0
\]

时，该运行才可用于比较。它用于检测 NaN/Inf、负密度和负压力。通过只表示输出物理可接受，不证明精度。

### 步数

`steps` 是 CFL 控制下到达 `t_end` 所需的时间步数。精度或求解器比较中步数相同，可以排除“运行步数不同”这一混杂因素；步数本身不是误差指标。

### 磁场散度

代码在内部网格使用中心差分：

\[
(\nabla\cdot B)_{i,j}=\frac{B_{x,i+1,j}-B_{x,i-1,j}}{2\Delta x}+\frac{B_{y,i,j+1}-B_{y,i,j-1}}{2\Delta y}.
\]

`divB_mean` 是绝对值的内部网格均值，`divB_max` 是内部最大值，实现在 `src/utils/error_norms.hpp`。它检查离散无散约束，不是 FP32/FP64 误差。

### 相对质量误差

对周期边界验证案例：

\[
mass_{rel}=|M(t)-M(0)|/|M(0)|.
\]

它检查守恒性；很小的质量误差不代表逐点解一定准确。

### Gate pass

门禁是以下条件的逻辑与：矩阵完整、进程成功退出、物理状态通过、必要诊断存在、满足实验预先规定阈值。通过表示 evidence packet 满足自己的验收合同，不表示所有潜在科学结论都成立。

## 8. 时间发散拟合

对预先固定窗口内的正 FP32/FP64 error samples，用最小二乘拟合：

\[
\log e(t)=a+\lambda t.
\]

因此 `lambda` 是有边界的 Lyapunov-like 工程斜率，不是正式 maximal Lyapunov exponent，因为扰动方式、范数、时间窗口和非线性阶段都由本数值实验固定。

## 9. 指标使用规则

| 问题 | 主指标 | 选择原因 |
|---|---|---|
| 两个同精度输出是否完全相同？ | max ULP | 精确比较浮点表示 |
| FP32/FP64 最坏局部变化多大？ | Linf | 保守局部上界 |
| 同网格典型差异多大？ | mean L1 / RMS L2 | 全域误差幅值 |
| 计算对随机舍入多敏感？ | MCA spread 与 SNR | 先逐网格统计样本变化，再做空间聚合 |
| 是否更快？ | wall time 中位数、IQR、speed-up | 稳健的重复 end-to-end 计时 |
| MHD 状态是否可接受？ | finite、rho_min、p_min | 必要物理 sanity check |
| 磁场散度是否受控？ | divB_mean、divB_max | 离散无散约束诊断 |
| 是否已建立完整科学结论？ | experiment gate 加 claim boundary | 防止 smoke/validation 被过度提升 |