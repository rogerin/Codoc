import ast
import os
import re

# --- Padrões de Regex para Diferentes Linguagens ---

# JavaScript (funções, classes, imports, constantes)
JS_PATTERNS = {
    "imports": re.compile(r"import(?:\s+.*?\s+from)?\s+['\"](.*?)['\"]"),
    "functions": re.compile(r"(?:function|const|let)\s+([\w\$]+)\s*=\s*(?:\([^)]*\)|async\s*\([^)]*\))\s*=>|function\s+([\w\$]+)\s*\(([^)]*)\)"),
    "classes": re.compile(r"class\s+([\w\$]+)"),
    "constants": re.compile(r"const\s+([A-Z_][A-Z0-9_]*)\s*=")
}

# Java (classes, métodos, imports, constantes)
JAVA_PATTERNS = {
    "imports": re.compile(r"import\s+(.*?);"),
    "classes": re.compile(r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)"),
    "functions": re.compile(r"(?:public|private|protected)?\s*(?:static|final|abstract)?\s*\w+(?:<.*?>)?\s+(\w+)\s*\(([^)]*)\)"),
    "constants": re.compile(r"(?:public|private|protected)?\s*static final\s+\w+\s+([A-Z_][A-Z0-9_]*)\s*=")
}

# API Endpoints (genérico para vários frameworks)
API_PATTERNS = [
    re.compile(r"@(?:app|router)\.(get|post|put|delete|patch)\(['\"](.*?)['\"]"),  # Flask/FastAPI
    re.compile(r"(?:app|router)\.(get|post|put|delete|patch)\(['\"](.*?)['\"]")  # Express.js
]

# --- Analisadores Específicos por Linguagem ---

def analyze_python_file(content):
    tree = ast.parse(content)
    analysis = {"imports": [], "functions": [], "classes": [], "constants": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper():
            analysis["constants"].append({"name": node.targets[0].id, "value": ast.get_source_segment(content, node.value)})
        elif isinstance(node, ast.FunctionDef):
            analysis["functions"].append({"name": node.name, "args": [arg.arg for arg in node.args.args], "docstring": ast.get_docstring(node) or "", "code_block": ast.get_source_segment(content, node)})
    return analysis

def analyze_generic_with_regex(content, patterns):
    analysis = {"imports": [], "functions": [], "classes": [], "constants": []}
    for key, pattern in patterns.items():
        for match in pattern.finditer(content):
            if key == "functions":
                # Tratamento especial para funções para extrair argumentos
                func_name = match.group(1) or match.group(2)
                args_str = match.group(3) or ""
                args = [arg.strip() for arg in args_str.split(",") if arg.strip()]
                analysis[key].append({
                    "name": func_name,
                    "args": args,
                    "docstring": "", # Regex não consegue extrair docstrings de forma confiável
                    "code_block": match.group(0)
                })
            else:
                name = next((g for g in match.groups() if g is not None), None)
                if name:
                    analysis[key].append({"name": name, "code_block": match.group(0)})
    return analysis

# --- Função Principal de Despacho (Dispatcher) ---

ANALYSIS_CACHE = {}

def analyze_code(filepath):
    if filepath in ANALYSIS_CACHE:
        return ANALYSIS_CACHE[filepath]

    _, extension = os.path.splitext(filepath)
    
    analysis = {
        "imports": [], "functions": [], "classes": [],
        "constants": [], "endpoints": [], "error": None
    }

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if extension == ".py":
            analysis.update(analyze_python_file(content))
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            analysis.update(analyze_generic_with_regex(content, JS_PATTERNS))
        elif extension == ".java":
            analysis.update(analyze_generic_with_regex(content, JAVA_PATTERNS))
        elif extension in [".md", ".txt", ".html", ".css"]:
            ANALYSIS_CACHE[filepath] = analysis
            return analysis

        for pattern in API_PATTERNS:
            for match in pattern.finditer(content):
                analysis["endpoints"].append({
                    "method": match.group(1).upper(),
                    "path": match.group(2)
                })

    except Exception as e:
        analysis["error"] = f"Falha ao analisar o arquivo: {e}"

    ANALYSIS_CACHE[filepath] = analysis
    return analysis
