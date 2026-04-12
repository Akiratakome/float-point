# Week 1 基础设施总结报告 — 答辩准备 Q&A

## 一、项目总体架构

### Q1: 为什么选择从零编写独立求解器，而不是基于 AMReX 等成熟框架？

本项目的核心研究目标是"浮点精度和硬件对 HRSC 格式的影响"。如果使用 AMReX，精度相关的行为会被框架内部的类型转换、内存管理和通信层所掩盖，难以做到逐比特级别的精度控制和对比。独立编写求解器可以：

- **完全控制浮点类型**：从常数字面量到中间计算，每一步都模板化于 `<Real>`，确保不会有隐式的 `double→float` 截断。
- **最小化外部依赖**：集群部署时只需编译器和 CMake，无需安装第三方库。
- **精确测量精度差异**：同一份代码用 `float`、`double`、`long double` 实例化后，差异完全来自浮点精度本身，而非框架行为。

**追问应对**：如果被问"这样做工作量是否太大"，可以回答：项目范围限定在二维欧拉方程，网格为均匀结构化网格，不需要 AMR 或复杂几何，因此独立实现的工作量是可控的。

---

### Q2: 为什么选择 C++17 而不是 C++20 或更新标准？

- **集群兼容性**：Cambridge CSC 集群的编译器版本通常支持 C++17，但 C++20 的 `concepts`、`ranges` 等特性在较旧的 GCC/NVCC 上支持不完整。
- **CUDA 兼容性**：NVCC 对 C++17 的支持已经很成熟，但对 C++20 的支持仍在逐步完善中。
- **C++17 已足够**：`if constexpr`、结构化绑定、`std::optional` 等特性已满足本项目的模板元编程需求。

---

## 二、精度泛型设计

### Q3: 为什么从第一天就模板化 `<Real>`，而不是先用 `double` 写完再泛化？

这是本项目最关键的设计决策之一。

**技术原因**：
- 后期泛化的成本极高。浮点字面量 `1.0`（默认 `double`）散布在整个代码中，逐一替换容易遗漏，且遗漏会导致 `-Wconversion` 警告甚至静默精度损失。
- 模板化从一开始就强制所有常量使用 `static_cast<Real>()`，确保精度一致性。

**工程原因**：
- 本项目的研究目标就是对比不同精度，如果基础设施不是精度泛型的，后续实验就无法进行。
- 早期模板化的额外工作量很小（主要是 `static_cast` 和模板参数传递），但后期重构的代价极大。

**示例**：`Constants<Real>` 中的 `gamma` 定义为 `static_cast<Real>(1.4)` 而非 `1.4`，避免了 `float` 实例化时的隐式截断。

---

### Q4: `static_cast<Real>()` 包裹每个字面量是否过于繁琐？为什么不用 `Real(1.4)` 的函数式转换？

`Real(1.4)` 是 C 风格转换的语法糖，在 C++ 中不推荐使用，原因：
- `static_cast` 的意图更明确，表示"我知道这是一个精度转换"。
- 编译器和静态分析工具对 `static_cast` 的检查更严格。
- `-Wconversion` 等编译警告能更好地配合 `static_cast` 工作。

---

### Q5: 为什么 `Constants` 用 `struct` + `static constexpr` 而不是 `namespace` + `constexpr` 变量？

```cpp
template<typename Real>
struct Constants {
    static constexpr Real gamma = static_cast<Real>(1.4);
};
```

用 `struct` 模板化可以让常量随 `Real` 类型变化。如果用 `namespace`，则需要为每种精度分别定义常量，或使用函数返回值，不如 `struct` 模板直观。

---

## 三、数据结构设计

### Q6: `Vec<Real,N>` 为什么是纯聚合体（aggregate），不定义构造函数？

```cpp
template<typename Real, int N>
struct Vec {
    Real data[N];  // 无构造函数
};
```

**关键原因**：
- **GPU 兼容性**：聚合体可以用花括号初始化 `Vec<double,4>{1.0, 0.0, 0.0, 2.5}`，在 `__device__` 函数中也能正常工作。
- **Trivially copyable**：无构造函数意味着编译器可以用 `memcpy` 优化拷贝，这对 GPU 数据传输至关重要。
- **简单可靠**：没有构造函数就没有构造函数相关的 bug。

**追问应对**：如果被问"没有构造函数，初始化不方便吗"，可以回答：C++17 的聚合初始化已经足够方便，且编译器会对未初始化的成员进行零初始化。

---

### Q7: 为什么选择 AoS（Array of Structures）而非 SoA（Structure of Arrays）内存布局？

内存索引公式：`((j+ng)*nx_total + (i+ng)) * NVars + var`

**选择 AoS 的原因**：
- **Riemann 求解器的访问模式**：HRSC 格式在每个面上需要同时访问一个单元的所有守恒量（密度、动量x、动量y、能量）。AoS 布局下，这 4 个变量在内存中连续存储，可以一次缓存行读取。
- **代码简洁性**：用 `Vec<Real,4>` 表示一个单元的状态向量，语义清晰，操作方便。
- **GPU 合并访问**：虽然 SoA 通常更有利于 GPU 的合并访问（coalesced access），但对于 Riemann 求解器这种每线程需要完整状态向量的场景，AoS 的性能损失可以接受，且代码复杂度大大降低。

**追问应对**：如果被问"SoA 在 GPU 上不是更快吗"，可以回答：
1. 本项目的主要研究目标是精度对比，不是极致性能优化。
2. 对于 NVars=4 的小向量，AoS 和 SoA 的性能差异不大。
3. 如果未来需要优化，可以在 View 层面做转换，不需要改变上层代码。

---

### Q8: Grid 的 Container-View 分离模式是什么？为什么这样设计？

```
Grid2D<Real, NVars>          // 拥有数据（std::vector）
  └→ GridView<Real, NVars>   // 指针视图（可拷贝到 GPU）
```

**核心问题**：`std::vector` 无法在 GPU `__device__` 函数中使用（涉及堆分配和虚函数表）。

**解决方案**：
- `Grid2D` 持有 `std::vector`，负责内存分配和管理，仅在 host 端使用。
- `GridView` 是一个轻量级结构体，持有裸指针 `Real*` 和网格元数据（nx, ny, ng, dx, dy），是 **trivially copyable** 的。
- 将 `GridView` 按值传递给 CUDA kernel，GPU 代码通过指针访问数据。

**类比**：类似 `std::string` 和 `std::string_view` 的关系，或者 `std::vector` 和 `std::span` 的关系。

---

### Q9: `GridViewBase` 的 `Ptr` 模板参数是什么设计？

```cpp
template<typename Real, int NVars, typename Ptr>
struct GridViewBase { ... };

using GridView      = GridViewBase<Real, NVars, Real*>;
using ConstGridView = GridViewBase<Real, NVars, const Real*>;
```

通过模板参数 `Ptr` 区分可变和不可变视图：
- `GridView`（`Ptr = Real*`）：可读写，用于写入计算结果。
- `ConstGridView`（`Ptr = const Real*`）：只读，用于读取输入数据。

这样只需一份代码就能同时支持 const 和 non-const 两种访问模式，避免了代码重复。

---

### Q10: `view()` 方法有什么需要注意的陷阱？

`GridView` 在调用 `view()` 时按值捕获 `dx`、`dy`。如果在调用 `view()` 之后修改了 `Grid2D` 的 `dx`/`dy`，已有的 `GridView` 不会反映这一变化。

**规则**：必须先设置好 `dx`/`dy`，再调用 `view()`。代码中已添加注释说明此行为。

---

## 四、测试框架

### Q11: 为什么选择 Catch2 v2 单头文件版本，而不是 Google Test 或 Catch2 v3？

**vs Google Test**：
- Google Test 需要编译静态库并链接，增加了集群部署的复杂性。
- Catch2 v2 单头文件可以直接 `#include`，无需额外的构建步骤。

**vs Catch2 v3**：
- Catch2 v3 改为多文件库，需要通过 CMake FetchContent 或包管理器安装。
- 单头文件版本在集群环境中更方便——直接将 `catch.hpp` 放入仓库即可。

**核心优势**：
- **零依赖部署**：仓库自包含，`git clone` + `cmake` 即可构建和测试。
- **模板测试支持**：`TEMPLATE_TEST_CASE` 可以用一套测试代码同时测试 `float` 和 `double`，完美契合精度泛型设计。

---

### Q12: 浮点数测试中如何处理精度容差？

使用 Catch2 的 `Approx` 进行浮点比较：

```cpp
REQUIRE(result == Approx(expected).epsilon(tol));
```

其中 `tol` 根据精度类型设定：
- `float`：`1e-5`
- `double`：`1e-12`

这个容差是 `Approx` 的相对容差（relative epsilon），即允许的相对误差。对于绝对值接近零的结果，`Approx` 还有一个 `margin` 参数可以控制绝对容差。

---

## 五、各模块设计决策

### Q13: Config 解析器为什么基于 `std::istream&` 而非文件路径？

```cpp
Config(std::istream& is);  // 而非 Config(const std::string& filename);
```

**测试友好**：单元测试可以用 `std::istringstream` 构造输入，不需要创建临时文件。

```cpp
std::istringstream iss("gamma = 1.4\nnx = 100");
Config cfg(iss);
```

**灵活性**：同一个解析器既能读文件（`std::ifstream`），也能读字符串、网络流等任何 `std::istream` 子类。

---

### Q14: EOS 函数为什么操作 `Vec<Real,4>` 而非散装的 `rho, u, v, p` 参数？

```cpp
template<typename Real>
HD_FUNC Real pressure(const Vec<Real,4>& U);
```

**原因**：
- **语义一致**：守恒量和原始量都是 4 维状态向量，用 `Vec<Real,4>` 表示在概念上是统一的。
- **接口简洁**：一个参数代替四个参数，函数签名更短，调用更方便。
- **与 Riemann 求解器对接**：Riemann 求解器的输入输出都是状态向量，直接传递 `Vec` 避免了反复打包/解包。
- **EulerVar 枚举**：`enum EulerVar { RHO=0, MX=1, MY=2, E=3 }` 提供有意义的下标访问。

---

### Q15: EOS 中的 debug assert 为什么用 `numeric_limits<Real>::min()` 而非硬编码阈值？

```cpp
assert(rho > std::numeric_limits<Real>::min());
```

**问题**：如果用 `assert(rho > 1e-14)`，对 `float` 来说 `1e-14` 远小于 `float` 的精度范围（`float` 的最小正规数约为 `1.17e-38`），这个断言几乎永远不会触发。对 `long double` 来说，`1e-14` 又可能过于严格。

**解决方案**：`numeric_limits<Real>::min()` 返回该类型的最小正规化浮点数，对每种精度都是有意义的阈值。

---

### Q16: 边界条件为什么设计为 host-only 的编排函数？

```cpp
// 仅在 host 端调用，内部循环设置 ghost cell
template<typename Real, int NVars>
void apply_outflow_bc(GridView<Real,NVars> view);
```

**原因**：
- **Week 1 范围限定**：GPU kernel 版本的边界条件是后续任务，当前先确保正确性。
- **编排 vs 计算分离**：边界条件的逻辑是"哪些 ghost cell 从哪些 interior cell 拷贝"，这是编排逻辑，不是计算密集型操作，放在 host 端合理。
- **后续 GPU 化路径清晰**：将来只需将循环体替换为 CUDA kernel，接口（接收 `GridView`）不变。

---

### Q17: Outflow 边界条件的 ghost cell 角点如何处理？

这是一个容易被忽略的细节。二维网格的四个角上的 ghost cell 同时属于 x 方向和 y 方向的 ghost 区域。

**策略**：
1. **x 方向 pass**：遍历所有行（包括 ghost 行），使用 clamped j 值：`j_clamped = clamp(j, 0, ny-1)`。这样即使 j 在 ghost 范围内，也能从最近的 interior 行获取值。角点在此步骤获得初始值。
2. **y 方向 pass**：仅遍历 interior 列。角点不会被 y-pass 覆盖，保留 x-pass 写入的值。

**结果**：角点最终持有来自 x 方向最近 interior cell 的值，物理上是合理的（外流边界的零梯度条件）。

---

## 六、构建系统

### Q18: 为什么用 CMake INTERFACE library 而非直接设置 include 路径？

```cmake
add_library(hrsc_core INTERFACE)
target_include_directories(hrsc_core INTERFACE ${CMAKE_SOURCE_DIR}/src)
```

**INTERFACE library 的优势**：
- **传递性**：任何 `target_link_libraries(X hrsc_core)` 的目标自动继承 include 路径、编译选项等。
- **可扩展性**：后续添加 CUDA 编译选项、链接库等，只需修改 `hrsc_core` 的属性，所有依赖目标自动更新。
- **现代 CMake 实践**：避免了全局的 `include_directories()` 污染。

---

### Q19: 为什么开启 `-Wall -Wextra -Wpedantic` 编译警告？

对于精度研究项目，编译警告至关重要：
- `-Wconversion`（包含在 `-Wall` 中的部分场景下）：捕获隐式精度转换，如 `double→float`。
- `-Wextra`：捕获未使用参数等可能的逻辑错误。
- `-Wpedantic`：确保代码严格符合 C++ 标准，提高跨编译器可移植性。

这些警告帮助确保精度泛型代码在不同 `Real` 类型实例化时不会引入意外的精度损失。

---

## 七、项目管理与方法论

### Q20: 为什么采用 header-only 设计？

**原因**：
- **模板代码必须在头文件中**：C++ 模板的实例化需要在编译时看到完整定义。由于本项目几乎所有代码都模板化于 `<Real>`，将实现放在 `.cpp` 文件中需要显式实例化，增加维护负担。
- **简化构建**：无需编译 `.cpp` 文件并链接，减少构建配置复杂度。
- **代码量可控**：项目规模不大（二维欧拉方程），header-only 不会导致编译时间爆炸。

**追问应对**：如果被问"header-only 不会导致编译变慢吗"，可以回答：对于本项目的规模（~2000 行核心代码），编译时间的增加可以忽略。如果未来成为问题，可以对非模板代码提取 `.cpp` 文件。

---

### Q21: `HD_FUNC` 宏的设计意图是什么？

```cpp
#ifdef __CUDACC__
#define HD_FUNC __host__ __device__
#else
#define HD_FUNC
#endif
```

- 当用 NVCC 编译时，`HD_FUNC` 展开为 `__host__ __device__`，使函数可在 CPU 和 GPU 上运行。
- 当用普通 C++ 编译器编译时，`HD_FUNC` 展开为空，不影响代码。
- 这使得同一份代码无需修改即可在纯 CPU 和 CUDA 环境下编译。

---

### Q22: `namespace hrsc` 的作用是什么？

所有项目代码都包裹在 `namespace hrsc` 中：
- 避免与标准库或第三方库的名称冲突。
- 明确标识项目代码的边界。
- 当需要在测试或脚本中使用时，可以通过 `using namespace hrsc` 或显式限定访问。

---

## 八、测试策略

### Q23: 如何确保测试真正验证了物理正确性而非仅仅"代码能跑"？

**具体措施**：
- **EOS 测试**：使用手工计算的精确值验证 `pressure()`、`sound_speed()`、`cons_to_prim()`、`prim_to_cons()` 的往返一致性（round-trip: prim→cons→prim）。
- **边界条件测试**：构造已知的 interior 场，应用 BC 后检查 ghost cell 的值是否精确等于预期的 interior cell 值（非"不等于零"的弱断言）。
- **Vec 运算测试**：验证 `dot()`、`norm_sq()` 等运算的数学正确性。
- **Config 测试**：验证类型转换、错误处理、边界情况。

**测试规模**：Week 1 共 51 个测试用例，788 个断言。

---

### Q24: `TEMPLATE_TEST_CASE` 如何同时测试多种精度？

```cpp
TEMPLATE_TEST_CASE("pressure is correct", "[eos]", float, double) {
    using Real = TestType;
    // 同一套测试逻辑，分别用 float 和 double 实例化
}
```

Catch2 v2 的 `TEMPLATE_TEST_CASE` 宏会为模板参数列表中的每种类型生成独立的测试用例。这样一套测试代码自动覆盖所有精度类型，确保精度泛型代码在各精度下都正确。

---

*本报告基于 Week 1（2026-03-30 至 2026-04-05）的设计与实现工作。*
