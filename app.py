import streamlit as st
import sys
import io
import pandas as pd
import altair as alt
from main import get_ortools_code, extract_code, get_ortools_code_strict, summarize_result, get_ortools_code_stream

def sanitize_code(code: str) -> str:
    if ('from ortools.sat.python import cp_model' in code) or ('cp_model.' in code):
        import re as _re
        m = _re.search(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*cp_model\.CpModel\(\)", code)
        model_var = m.group(1) if m else 'model'
        if 'CpSolver' not in code:
            if m:
                insert_pos = m.end()
                code = code[:insert_pos] + "\nsolver = cp_model.CpSolver()" + code[insert_pos:]
            else:
                m2 = _re.search(r"from ortools\.sat\.python import cp_model", code)
                insert_pos = m2.end() if m2 else 0
                code = code[:insert_pos] + "\nsolver = cp_model.CpSolver()" + code[insert_pos:]
        code = _re.sub(rf"\b{model_var}\.Solve\(\s*\)", f"solver.Solve({model_var})", code)
        code = _re.sub(r"\bsolver\.Solve\(\s*\)", f"solver.Solve({model_var})", code)
        code = code.replace('solver.Objective().Value()', 'solver.ObjectiveValue()')
        code = code.replace('solver.Objective().value()', 'solver.ObjectiveValue()')
        code = _re.sub(r"([A-Za-z_][A-Za-z0-9_]*)\.solution_value\(\)", r"solver.Value(\1)", code)
    return code

def parse_exec_output(text: str):
    import re
    obj = None
    m = re.search(r"Objective\s*value\s*[:=]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text, re.IGNORECASE)
    if m:
        obj = m.group(1)
    vars = []
    for name, val in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", text):
        vars.append({"变量": name, "值": float(val)})
    return {"objective": obj, "variables": vars}

# --- 现代化灵动风格 CSS ---
st.set_page_config(page_title="AI+OR-Tools 优化求解器", layout="wide", page_icon="✨")

st.markdown("""
<style>
    /* 引入更现代的英文字体，中文优先使用系统默认 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

    :root {
        --primary-color: #2563EB;
        --background-color: #FFFFFF;
        --secondary-bg: #F8FAFC;
        --text-color: #0F172A;
        --border-color: #E2E8F0;
    }

    /* 全局字体优化 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
        color: var(--text-color);
        -webkit-font-smoothing: antialiased;
    }
    
    /* 标题样式 */
    h1 {
        color: #1E293B;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1.5rem !important;
    }
    
    h2, h3 {
        color: #334155;
        font-weight: 700;
        letter-spacing: -0.01em;
    }

    /* 侧边栏优化 */
    section[data-testid="stSidebar"] {
        background-color: #F8FAFC;
        border-right: 1px solid var(--border-color);
    }
    
    /* 按钮样式重置 */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        border: 1px solid transparent;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease-in-out;
    }
    
    .stButton > button:hover {
        background-color: #1D4ED8;
        border-color: transparent;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        color: white;
    }
    
    .stButton > button:focus {
        color: white;
        border-color: transparent;
        box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
    }

    /* 文本框优化 */
    .stTextArea textarea {
        border: 1px solid var(--border-color);
        border-radius: 8px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    
    .stTextArea textarea:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* 现代卡片容器 */
    .modern-card {
        background-color: white;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    
    /* 代码块优化 */
    code {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9em;
    }
    
    .stCode {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Expander 样式 */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* 提示框微调 */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 8px;
        padding: 0.75rem 1rem;
        border: none;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stInfo { background-color: #EFF6FF; color: #1D4ED8; border-left: 4px solid #3B82F6; }
    .stSuccess { background-color: #F0FDF4; color: #15803D; border-left: 4px solid #22C55E; }
    .stWarning { background-color: #FFFBEB; color: #B45309; border-left: 4px solid #F59E0B; }
    .stError { background-color: #FEF2F2; color: #B91C1C; border-left: 4px solid #EF4444; }

    /* 图表容器 */
    [data-testid="stVegaLiteChart"] {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
</style>
""", unsafe_allow_html=True)


st.title("✨ AI+OR-Tools 智能求解平台")
st.markdown("""
<div class="modern-card">
    <p style="font-size: 1.1em; line-height: 1.7; color: #475569; margin: 0;">
    🚀 <strong>新一代智能优化引擎</strong><br>
    融合 <strong>Google OR-Tools</strong> 强大算力与 <strong>LLM</strong> 语义理解。<br>
    从自然语言到最优解，仅需一步。支持 LP、MIP、CP 等多种复杂场景。
    </p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ 模型配置")
model_options = {
    "DeepSeek-V3.2 (推荐)": "deepseek-ai/DeepSeek-V3.2",
    "Qwen3-0.6B (快速)": "Qwen/Qwen3-0.6B",
}
selected_model_label = st.sidebar.selectbox("选择推理模型：", list(model_options.keys()))
selected_model_id = model_options[selected_model_label]

st.sidebar.markdown("---")
st.sidebar.header("📚 案例库")
example_options = {
    "自定义输入": "",
    "生产计划 (线性规划)": "最大化 3x + 4y，约束：x + 2y <= 14，3x - y >= 0，x - y <= 2，x >= 0，y >= 0。",
    "资源分配 (背包问题)": "有 4 个物品，重量 [2, 3, 4, 5]，价值 [3, 4, 5, 6]，背包容量 5，选择哪些物品使总价值最大？",
    "人员调度 (指派问题)": "把 3 位工人分配到 3 个任务。成本矩阵：[[90, 80, 75], [35, 85, 55], [125, 95, 90]]，使总成本最小。",
    "逻辑推理 (三位数谜题)": "在 1 到 9 之间找三个互不相同的数字 X、Y、Z，使得 X + Y = Z，并且 Z 最大。"
}

selected_example = st.sidebar.radio("加载标准案例：", list(example_options.keys()))

if selected_example == "自定义输入":
    default_text = ""
else:
    default_text = example_options[selected_example]

# 主界面布局
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 问题描述")
    problem_description = st.text_area(
        "请输入您的优化问题（支持中文自然语言）：", 
        value=default_text, 
        height=300,
        help="请尽可能清晰地描述目标函数、决策变量及约束条件。"
    )
    
    solve_btn = st.button("🚀 开始计算求解", type="primary", use_container_width=True)

if solve_btn:
    if not problem_description.strip():
        st.warning("⚠️ 请先输入问题描述。")
    else:
        with st.spinner("⏳ 正在构建数学模型并求解..."):
            try:
                # 1. Stream Generate Code with realtime thinking output（置于左栏，默认展开）
                thinking_container = col1.expander("👁️ 查看推理过程 (Thinking Process)", expanded=True)
                reasoning_placeholder = thinking_container.empty()
                if 'thinking_buf' not in st.session_state:
                    st.session_state['thinking_buf'] = ""
                st.session_state['thinking_buf'] = "正在思考...\n\n"

                def on_reasoning(chunk: str):
                    st.session_state['thinking_buf'] += chunk
                    reasoning_placeholder.text(st.session_state['thinking_buf'])

                def on_content(chunk: str):
                    # optionally show partial final answer in expander as well
                    pass

                llm_output = get_ortools_code_stream(
                    problem_description,
                    selected_model_id,
                    on_reasoning=on_reasoning,
                    on_content=on_content,
                )

                # 2. Extract Code
                code = extract_code(llm_output)
                final_code = None
                
                if code:
                    final_code = sanitize_code(code)
                else:
                    # Retry logic
                    llm_output_retry = get_ortools_code_strict(problem_description, selected_model_id)
                    code_retry = extract_code(llm_output_retry)
                    if code_retry:
                        final_code = sanitize_code(code_retry)
                    if not final_code:
                        with thinking_container:
                            st.error("首次生成失败，已尝试重试但仍未生成有效代码。")
                            st.text(llm_output_retry)

                # Execute and Show Results in Column 2
                with col2:
                    if final_code:
                        st.subheader("💻 数学模型 (Python代码)")
                        st.code(final_code, language="python")
                        
                        st.subheader("📊 计算结果分析")
                        
                        # Execute
                        exec_output = io.StringIO()
                        original_stdout = sys.stdout
                        sys.stdout = exec_output
                        try:
                            exec_globals = {}
                            exec(final_code, exec_globals)
                            result_output = exec_output.getvalue()
                            
                            # Parse structured result
                            parsed = parse_exec_output(result_output)
                            
                            # Display Summary
                            st.markdown("##### 🧠 结论摘要")
                            summary = summarize_result(problem_description, result_output, selected_model_id)
                            st.info(summary)
                            
                            # Display Metrics
                            if parsed["objective"]:
                                st.metric("最优目标值 (Objective Value)", parsed["objective"])
                            
                            # Display Variables Table & Chart
                            if parsed["variables"]:
                                df_vars = pd.DataFrame(parsed["variables"])
                                
                                tab1, tab2 = st.tabs(["📋 变量数据表", "📈 变量分布图"])
                                with tab1:
                                    st.dataframe(df_vars, use_container_width=True, hide_index=True)
                                with tab2:
                                    # Scientific Chart using Altair
                                    chart = alt.Chart(df_vars).mark_bar().encode(
                                        x=alt.X('变量', sort=None, title='决策变量'),
                                        y=alt.Y('值', title='数值结果'),
                                        color=alt.Color('变量', legend=None),
                                        tooltip=['变量', '值']
                                    ).properties(
                                        title='决策变量结果分布'
                                    ).interactive()
                                    st.altair_chart(chart, use_container_width=True)
                            
                            with st.expander("查看原始输出日志"):
                                st.text(result_output)
                                
                        except Exception as e:
                            st.error(f"❌ 运行时错误：{e}")
                            st.text(exec_output.getvalue())
                        finally:
                            sys.stdout = original_stdout
                    else:
                        st.error("❌ 未能生成有效的数学模型代码，请检查问题描述是否清晰。")

            except Exception as e:
                sys.stdout = original_stdout
                st.error(f"发生系统错误：{e}")
