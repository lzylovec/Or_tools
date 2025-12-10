# AI + OR-Tools 智能优化求解平台

这是一个基于 **Google OR-Tools** 优化引擎与 **大语言模型 (LLM)** 技术的智能求解平台。旨在让用户通过自然语言描述数学规划问题，AI 自动生成求解代码、执行计算并呈现可视化的最优方案。

## 🌟 核心功能

*   **自然语言建模**：无需学习复杂的 OR-Tools API，直接用中文描述你的优化问题（如生产计划、资源分配、逻辑谜题等）。
*   **多模型支持**：集成 **DeepSeek-V3.2**（推荐，推理能力强）与 **Qwen3-0.6B**（速度快），支持实时流式输出推理过程。
*   **智能代码生成与修复**：
    *   自动识别问题类型（线性规划 LP、混合整数规划 MIP、约束编程 CP）。
    *   内置代码清洗与 API 自动纠错机制，确保生成的代码可执行。
*   **结构化结果分析**：
    *   **自然语言结论**：AI 自动总结求解结果，给出通俗易懂的建议。
    *   **数据可视化**：自动提取决策变量，生成数据表格与交互式柱状图。
    *   **实时推理流**：透明展示 AI 从理解问题到构建模型的思考全过程。
*   **现代化界面**：基于 Streamlit 构建的响应式 Web 界面，采用现代 Indigo 风格设计，操作流畅。

## 📚 支持的问题类型

平台支持广泛的运筹学问题求解：

1.  **线性规划 (Linear Programming, LP)**
    *   示例：生产组合优化、营养配餐、成本最小化。
2.  **混合整数规划 (Mixed Integer Programming, MIP)**
    *   示例：背包问题、工厂选址、投资组合。
3.  **约束编程 (Constraint Programming, CP)**
    *   示例：排班调度、数独/逻辑谜题、N皇后问题、指派问题。

## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。

```bash
# 克隆项目（假设在当前目录）
git clone <repository-url>
cd Or_tools

# 安装依赖
pip install -r requirements.txt
```

*注意：`requirements.txt` 应包含 `openai`, `ortools`, `streamlit`, `pandas`, `altair`。*

### 2. 配置 API Key

打开 `main.py`，确保已配置兼容 OpenAI 格式的 API Key（本项目默认配置了 ModelScope 的 DeepSeek 接口）。

```python
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='YOUR_API_KEY', 
)
```

### 3. 启动应用

使用 Streamlit 启动 Web 服务：

```bash
python -m streamlit run app.py
```

访问浏览器地址：`http://localhost:8501`

## 📂 项目结构

*   `app.py`: Streamlit Web 应用入口，负责界面交互、结果展示与图表绘制。
*   `main.py`: 核心逻辑层，封装了 LLM 调用、Prompt 管理、代码提取与清洗功能。
*   `.streamlit/config.toml`: 界面主题配置文件，定义了现代化的配色方案。

## 💡 使用示例

**场景：背包问题**
> "有 4 个物品，重量 [2, 3, 4, 5]，价值 [3, 4, 5, 6]，背包容量 5，选择哪些物品使总价值最大？"

**AI 处理流程：**
1.  **思考**：识别为 MIP 问题，确定变量 $x_i \in \{0,1\}$，约束 $\sum w_i x_i \le 5$，目标 $\max \sum v_i x_i$。
2.  **代码**：生成调用 `pywraplp.Solver.CreateSolver('SCIP')` 的 Python 代码。
3.  **求解**：运行代码，得出最优解（如选择物品 2，总价值 7）。
4.  **展示**：页面显示“最优目标值：7”，并用图表列出被选中的物品。

---
*Powered by DeepSeek & Google OR-Tools*
