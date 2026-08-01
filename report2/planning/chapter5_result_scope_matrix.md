# Chapter 5 non-ranking result-scope matrix

本表是 C5.1/C5.11 的写作资产，不是 effect-size ranking。它回答每个变化轴究竟测了什么、
是否改变保存状态、是否有可报告的重复 timing，以及结论在哪个 scope 内成立。若将本表放入
正文，应把 MCA evidence-status table 移到 Appendix，避免 Chapter 5 超出“五图一表”的版面锁。

| 变化轴 | 保存输出结果 | 重复 timing | 当前证据状态 | matched scope | 正文允许的结论 |
|---|---|---|---|---|---|
| fp32 对 fp64 | 非零、case/config-dependent density discrepancy | 有，KH CPU 与 repeated CPU/GPU packets | report-grade bounded | named case、solver、grid、CFL、end time、build | 精度改变可影响保存状态和本机 wall time；不等于 fp32 accuracy/adequacy |
| O2-default 对 Ofast-fast | 从零到非零，依 case/precision 而变；该 pair 同时改变多个 recorded semantics | 无可作性能结论的 repeated pair | report-grade composite output sensitivity | 16-row Euler--MHD matched matrix | composite build response 依配置而变；不把差异归因于单一 transformation |
| `/Ox` 对 `/O2` | 四个 HLL/HLLD、fp64/fp32 Brio--Wu density discrepancies 均为零 | 无 | report-grade direct output sensitivity | MSVC 19.51、Brio--Wu、N=800、t=0.1、CFL=0.4、单线程 | covered rows 中 optimisation 轴未改变 density；不作 compiler-wide 或 performance 结论 |
| `/fp:fast` 对 compiler-default math | 四组 density discrepancies 均非零，fp64 为 $10^{-15}$ 量级、fp32 为 $10^{-6}$ 量级 | 无 | report-grade direct output sensitivity | 与上一行相同，固定 `/O2` 和 `<=` | covered rows 对 fast-math 轴有非零 density response；不解释为 accuracy 或 portability |
| `<` 对 `<=` branch rule | HLL 两组为零；HLLD fp64/fp32 非零 | 无 | report-grade direct output sensitivity | 与上一行相同，固定 `/O2` 和 compiler-default math | branch response 依 solver/precision 配置而变；不形成通用 branch-rule ranking |
| HLL 对 HLLD | 数值方法不同，输出差异不能称为 reproducibility drift | 有，KH CPU 五次 measured repeats | report-grade timing；输出比较受 CFL/scope 限制 | KH 256^2、t=1.0、CFL=0.4、单线程、本机 | 报告 matched timing cost；不构造 accuracy--cost Pareto 或通用 solver ranking |
| CPU 对 GPU | covered HLL pairs 为 0 ULP | 有，Brio--Wu/OT 各五次 | report-grade bounded | HLL、Brio--Wu/OT、fp64/fp32、tested workstation | covered path 的同精度正确性与 workload-dependent speed-up；不外推 HLLD/KH |
| OpenMP 1/2/4/8 threads | covered OT/KH outputs 为 0 ULP | 无 scaling protocol | report-grade reproducibility | named CPU cases/builds/workstation | covered scheduling change 未改变输出；不声称 OpenMP scaling 或 MPI reproducibility |
| CFL 0.2/0.4/0.6/0.8 | fp32--fp64 discrepancy 非零且 non-monotonic | 无 | report-grade sensitivity | KH、named solvers/builds/grid/end time | CFL 是 sensitivity axis；不是 formal temporal convergence |
| resolution 128/256/512 | 8/8 self-refinement groups 与 12/12 precision cells 完整 | 无 matched repeated timing | report-grade bounded diagnostic | OT/KH、HLL/HLLD，各自固定 precision/CFL | 描述 self-refinement 与 precision-separation trend；不声称 asymptotic order 或 accuracy |
| simulation time | Brio--Wu discrepancy 的固定窗 fit 较一致；OT fit quality 近零 | 无 | negative-result | fixed samples/windows、named cases | 报告 engineering fit 和未观察到的预设 contrast；不称 Lyapunov/physical rate |
| MCA p53/p24 | stochastic spread；p24 不是 IEEE fp32 | 无 performance study | Brio--Wu report-grade；OT/KH reduced-scope provisional/validation | 每行明确 grid、end time、N、solver、runner | 同 scope Brio--Wu 可作 bounded stochastic observation；OT/KH 不跨 scope 合并或排序 |

## 使用规则

1. “输出未改变”只写为 covered configuration 的 zero result，不改写成硬件或线程普遍独立性。
2. solver change 是 method variation；device/thread/build change 才回答 implementation reproducibility 的不同侧面。
3. 没有 repeated timing protocol 的轴不报告 performance ordering。
4. 不对不同 metric、case、grid 或 end time 做归一化总分，也不复用
   `experiments/week17/report2_synthesis/figures/axis_ranking.png`。
5. 每个正文结论仍须回到 `docs/experiment_logs/report2_evidence_map.md` 的 authority 与 excluded claims。
