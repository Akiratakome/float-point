# 科学计算代码指南：编程实践与外部库管理

本文档基于剑桥大学科学计算 MPhil 项目的指导方针，详细总结了在编写科学计算代码时应遵循的良好编程实践，以及如何正确使用外部库和版本控制工具。

一、 良好的编程实践 (Programming in Practice)良好的编程习惯可以极大地减少 Bug，提升代码的可读性和可维护性。以下是核心要求与具体示例：

1. 避免使用“魔术数字” (Avoid Magic Numbers)“魔术数字”是指在代码中突然出现、缺乏明确说明的任意常数。这会给代码的升级（如从 2D 扩展到 3D）和精度维护带来极大困难。

❌ 错误示例（使用魔术数字）：// 难以理解 1.0/2.0 代表什么，且精度不可控
double scaleFactor = pow(cellSize, 1.0/2.0); 

// 如果凭借记忆随手写下圆周率，每次精度可能都不同
double one = pow(sin(3.14159/2), 2) + pow(cos(3.1415927/2), 2);


✅ 正确示例（集中管理常数）：应该创建专门的文件（如 constants.H 和 constants.C）来声明和定义这些常量。constants.H 声明:extern const double pi;
extern const unsigned int dimn;
constants.C 定义://! 使用统一高精度的 pi 值
const double pi = 3.14159265358979;
//! 模拟的维度
const unsigned int dimn = 2;
然后在主代码中使用：double scaleFactor = pow(cellSize, 1.0/dimn); 


2. 坚持统一的命名规范 (Naming Conventions)存在许多命名风格，关键在于选择一种并严格遵守。讲义中推荐的个人风格示例：

变量 (Variables):camelCaseNames (小驼峰命名法)
全局/常量 (Global/Constant): CapitalizedCamel (大驼峰命名法)
类名 (Class names): CapitalizedNames (大驼峰命名法)
类成员变量 (Class member data): m_classData (带前缀 m_)
函数 (Functions): myCamelFunction() (小驼峰命名法)
宏定义 (Macros): DIMENSION (全大写)


3. 拒绝硬编码，使用配置文件 (Settings File)不要将文件名或关键参数（如计算域的边界）硬编码到源代码中。你应该将代码设计为可以从配置文件中读取参数，这样在进行不同参数的模拟时就无需重新编译代码。


❌ 错误示例（硬编码）：const double domainMin = -1.0;
const double domainMax = +1.0;
✅ 正确示例（使用 libconfig 库读取配置）：settings.txt (配置文件):CFD: {
  domainMin = -1.0;
  domainMax = +1.0;
};
main.cpp (C++ 读取代码):#include <libconfig.h++>
libconfig::Config cfg;
cfg.readFile("settings.txt");
const auto& cfd_section = cfg.lookup("CFD");
double domainMin, domainMax;
cfd_section.lookupValue("domainMin", domainMin);
cfd_section.lookupValue("domainMax", domainMax);


4. 编写有意义的注释 (Commenting)注释不应该用来解释代码正在做什么（代码本身就应该足够清晰），而应该解释为什么这么做（例如背后的算法逻辑或为了修复某个特定的边界情况）。如果注释与代码不匹配，两者都会被视为错误。

❌ 极差的注释（毫无意义）：// 检查 "5" 是否在 vector 中 （解释了显而易见的事情）
if(v[0] == 5)

// 循环遍历 v 的所有元素 （多余的解释）
for(size_t i=0; i<v.size(); i++)
✅ 优秀的注释（解释算法和逻辑）：// 计算二阶有限差分更新
for(size_t i=1; i < v.size()-1 ; i++){
    w[i] = v[i] + (f(v[i+1]) - f(v[i-1])) * dt/dx;
}

/* 对矩阵 A 执行高斯消元法，并确保所有全零行都在底部。
   如果不这样做，findEigenvaluesFast() 中的算法将无法正确运行。*/


5. 代码模块化 (Modularisation)人类大脑一次只能处理有限的信息。在开始编码前，思考如何将代码分解成易于管理的模块。如果在编写过程中发现自己在反复编写相似的代码，务必将其提取成一个独立的函数。这不仅方便调试，也方便后续使用更高效的库函数进行替换。


二、 外部库的使用与版本控制 (Libraries & Version Control)1. 积极且谨慎地使用外部库 (Libraries)强烈建议使用外部库来减轻工作量、减少 Bug 并可能提升代码运行效率。推荐库示例： 

* 配置读取：libconfig++线性代数/数学运算：Armadillo, Eigen, BLAS / LAPACK通用工具库：Boost选用原则： 尽量不要使用超过两年未更新的库。版本说明： 如果你需要特定版本的库，务必为自己和评估人员（Assessors）做好记录，尤其是当该版本修复或引入了特定的 Bug 时。

开源协议 (Licensing)： 尽管在读研期间可能影响不大，但如果未来打算将研究商业化，必须了解开源库的协议限制（如 GPLv2, GPLv3, LGPL, MIT, BSD 等）。即便你是免费分发代码，某些协议（尤其是 GPL 系列）也会严格限制你在商业闭源项目中的使用方式。


* 版本控制最佳实践 (Version Control)在开发过程中，必须使用版本控制工具（如 Git 或 Subversion）。开发时的使用示例：将配置文件纳入版本控制，并使用脚本进行夜间自动化测试。如果发现新版本的代码坏了，使用 git bisect（二分查找）等手动或自动化流程来精确追踪错误是哪一次提交引入的。提交作业/项目时的规定（极重要）：只提交最终代码。 过去常有学生提交包含整个 Git 历史（.git 文件夹）的压缩包。这不仅会导致下载文件过于庞大，还会暴露你所有过去的提交记录和草稿信息。不要提交编译产物。 仓库和提交包中绝对不应该包含可执行文件（Executables）、目标文件（.o / Object files）或生成的 PDF 文件。