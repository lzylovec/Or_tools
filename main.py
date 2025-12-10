import re
import sys
from openai import OpenAI

# Initialize the client as per user instruction
client = OpenAI(
    base_url='https://api-inference.modelscope.cn/v1',
    api_key='ms-2d143f6e-cad4-45fe-a19f-3ba1d458028c', # ModelScope Token
)

def get_ortools_code(problem_description, model_id):
    """
    Sends the problem description to the LLM and retrieves the OR-Tools Python code.
    """
    
    system_prompt = """你是 Google OR-Tools 专家。
你的任务是把自然语言的优化问题翻译为可执行的 Python 代码，使用 Google OR-Tools。

For Linear Programming (LP) or Mixed Integer Programming (MIP) problems (like "maximize 3x+4y..." or "knapsack problem"):
- Use `from ortools.linear_solver import pywraplp`
- Create solver: `solver = pywraplp.Solver.CreateSolver('GLOP')` (for LP/Continuous) or `solver = pywraplp.Solver.CreateSolver('SCIP')` (for MIP/Integer/Binary).
- Define variables: 
    - Continuous: `x = solver.NumVar(0, solver.infinity(), 'x')`
    - Integer: `x = solver.IntVar(0, 10, 'x')`
    - Binary (0 or 1): `x = solver.BoolVar('x')`
- Add constraints: `solver.Add(2*x + 3*y <= 10)`
- Objective: `solver.Maximize(3*x + 4*y)`
- Solve: `status = solver.Solve()`
- Check status: `if status == pywraplp.Solver.OPTIMAL:`
- Print solution: `print('Objective value =', solver.Objective().Value())`; `print('x =', x.solution_value())`

Common Patterns:
- "Select items to maximize value within capacity" (Knapsack): Use MIP (SCIP). Constraint `sum(w[i]*x[i]) <= C`.
- "Assignment problem" (workers to tasks): Use MIP (SCIP) or CP.
- "Distinct values", "Not equal", "Sudoku", "Scheduling", "Logic Puzzle": MUST use CP (`cp_model`). `pywraplp` DOES NOT support `!=`.

For Constraint Programming (CP) problems (like logic puzzles, scheduling):
- Use `from ortools.sat.python import cp_model`
- Create model: `model = cp_model.CpModel()`
- Define vars: `x = model.NewIntVar(0, 10, 'x')`
- Add constraints: `model.Add(x != y)`
- Solve: `solver = cp_model.CpSolver(); status = solver.Solve(model)`
- Check status: `if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:`
- Print solution: `print('x =', solver.Value(x))` (Print ALL variables)

 规则：
 - 只输出被 ```python 包裹的代码块。
 - 代码块外不要有任何解释文字。
 - 假设所有输入数据均在脚本中硬编码。
 - 明确打印目标值（如适用）和所有变量取值。
"""

    extra_body = {
        "enable_thinking": True
    }

    print("正在思考...")
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': problem_description
            }
        ],
        stream=True,
        extra_body=extra_body
    )

    full_content = ""
    done_thinking = False
    
    for chunk in response:
        # Check for reasoning content (thinking)
        if hasattr(chunk.choices[0].delta, 'reasoning_content'):
            thinking_chunk = chunk.choices[0].delta.reasoning_content
            if thinking_chunk:
                print(thinking_chunk, end='', flush=True)
        
        # Check for actual content
        if hasattr(chunk.choices[0].delta, 'content'):
            answer_chunk = chunk.choices[0].delta.content
            if answer_chunk:
                if not done_thinking:
                    print('\n\n === 最终答案 ===\n')
                    done_thinking = True
                print(answer_chunk, end='', flush=True)
                full_content += answer_chunk
                
    print("\n")
    return full_content

def get_ortools_code_stream(problem_description, model_id, on_reasoning=None, on_content=None):
    """
    Stream OR-Tools code generation with real-time callbacks.
    on_reasoning(chunk: str) and on_content(chunk: str) will be called as data arrives.
    Returns the final concatenated assistant content for downstream code extraction.
    """
    system_prompt = """你是 Google OR-Tools 专家。
你的任务是把自然语言的优化问题翻译为可执行的 Python 代码，使用 Google OR-Tools。

For Linear Programming (LP) or Mixed Integer Programming (MIP) problems (like "maximize 3x+4y..." or "knapsack problem"):
- Use `from ortools.linear_solver import pywraplp`
- Create solver: `solver = pywraplp.Solver.CreateSolver('GLOP')` (for LP/Continuous) or `solver = pywraplp.Solver.CreateSolver('SCIP')` (for MIP/Integer/Binary).
- Define variables: 
    - Continuous: `x = solver.NumVar(0, solver.infinity(), 'x')`
    - Integer: `x = solver.IntVar(0, 10, 'x')`
    - Binary (0 or 1): `x = solver.BoolVar('x')`
- Add constraints: `solver.Add(2*x + 3*y <= 10)`
- Objective: `solver.Maximize(3*x + 4*y)`
- Solve: `status = solver.Solve()`
- Check status: `if status == pywraplp.Solver.OPTIMAL:`
- Print solution: `print('Objective value =', solver.Objective().Value())`; `print('x =', x.solution_value())`

Common Patterns:
- "Select items to maximize value within capacity" (Knapsack): Use MIP (SCIP). Constraint `sum(w[i]*x[i]) <= C`.
- "Assignment problem" (workers to tasks): Use MIP (SCIP) or CP.
- "Distinct values", "Not equal", "Sudoku", "Scheduling", "Logic Puzzle": MUST use CP (`cp_model`). `pywraplp` DOES NOT support `!=`.

For Constraint Programming (CP) problems (like logic puzzles, scheduling):
- Use `from ortools.sat.python import cp_model`
- Create model: `model = cp_model.CpModel()`
- Define vars: `x = model.NewIntVar(0, 10, 'x')`
- Add constraints: `model.Add(x != y)`
- Solve: `solver = cp_model.CpSolver(); status = solver.Solve(model)`
- Check status: `if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:`
- Print solution: `print('x =', solver.Value(x))` (Print ALL variables)

 规则：
 - 只输出被 ```python 包裹的代码块。
 - 代码块外不要有任何解释文字。
 - 假设所有输入数据均在脚本中硬编码。
 - 明确打印目标值（如适用）和所有变量取值。
"""

    extra_body = {"enable_thinking": True}
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": problem_description},
        ],
        stream=True,
        extra_body=extra_body,
    )

    full_content = ""
    for chunk in response:
        # Real-time reasoning
        if hasattr(chunk.choices[0].delta, 'reasoning_content'):
            rc = chunk.choices[0].delta.reasoning_content
            if rc and on_reasoning:
                on_reasoning(rc)
        # Real-time content
        if hasattr(chunk.choices[0].delta, 'content'):
            c = chunk.choices[0].delta.content
            if c:
                if on_content:
                    on_content(c)
                full_content += c
    return full_content

def extract_code(llm_output):
    """
    Extracts Python code from markdown code blocks.
    """
    patterns = [
        r"```\s*python\s*(.*?)```",
        r"```\s*py\s*(.*?)```",
        r"```\s*(.*?)```"
    ]
    for p in patterns:
        m = re.findall(p, llm_output, re.DOTALL | re.IGNORECASE)
        if m:
            blocks = sorted(m, key=lambda x: len(x), reverse=True)
            code = blocks[0].strip()
            return code
    return None

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

def get_ortools_code_strict(problem_description, model_id):
    system_prompt = """只输出 OR-Tools 可执行 Python 代码，并用 ```python 包裹。不要任何解释。
线性/整数规划：使用 pywraplp（GLOP/SCIP）；离散约束：使用 cp_model。打印目标值与所有变量。"""
    extra_body = {"enable_thinking": False}
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': problem_description}
        ],
        stream=True,
        extra_body=extra_body
    )
    full = ""
    for c in response:
        if hasattr(c.choices[0].delta, 'content'):
            s = c.choices[0].delta.content
            if s:
                full += s
    return full

DEFAULT_MODEL = 'deepseek-ai/DeepSeek-V3.2'

def main():
    if len(sys.argv) > 1:
        problem = " ".join(sys.argv[1:])
    else:
        # Default example problem
        problem = "最大化 3x + 4y，约束：x + 2y <= 14，3x - y >= 0，x - y <= 2，x >= 0，y >= 0。"
        print(f"未提供问题，使用默认示例：\n{problem}\n")
        print("用法：python main.py <你的优化问题描述>")

    print("-" * 50)
    print(f"问题：{problem}")
    print("-" * 50)

    llm_output = get_ortools_code(problem, DEFAULT_MODEL)
    
    code = extract_code(llm_output)
    
    if code:
        code = sanitize_code(code)
        print("-" * 50)
        print("正在执行生成的 OR-Tools 代码：")
        print("-" * 50)
        
        # Execute the code
        try:
            exec_globals = {}
            exec(code, exec_globals)
        except Exception as e:
            print(f"运行代码出错：{e}")
    else:
        print("未从响应中找到有效的 Python 代码块。")

    if __name__ == "__main__":
        main()
def summarize_result(problem_description, exec_output, model_id):
    system_prompt = "你是优化问题的中文解释助手。根据给定的自然语言问题与求解器输出，生成简洁结论，包括：是否找到可行/最优解、若有目标值则给出目标值、列出主要变量的取值，并用一两句话说明含义。"
    extra_body = {"enable_thinking": False}
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"问题：\n{problem_description}\n\n求解器输出：\n{exec_output}\n\n请用中文给出简洁结论。"},
        ],
        stream=True,
        extra_body=extra_body,
    )
    full = ""
    for c in response:
        if hasattr(c.choices[0].delta, 'content'):
            s = c.choices[0].delta.content
            if s:
                full += s
    return full
