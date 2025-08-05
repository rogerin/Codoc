# --- Orquestrador de Documentação de Projeto --- #
#
# Este arquivo unifica todo o código do projeto em um único local.
#

import sys
import os
import subprocess
import shutil
import time
import json
import re
import ast
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict
from dotenv import load_dotenv
from git import Repo
import requests

class ProjectOrchestrator:
    """Encapsula todo o fluxo de trabalho de análise e documentação de um projeto."""

    def __init__(self, repo_url):
        if not repo_url:
            raise ValueError("A URL do repositório não pode ser vazia.")
        self.repo_url = repo_url
        self.repo_path = None
        self.classification = None
        self.commits = None
        self.code_analysis = defaultdict(dict)
        self.ANALYSIS_CACHE = {}

    # --- Etapa 1: Fetch do Repositório ---
    def fetch_repository(self, base_path=".repos"):
        print("[1] Clonando repositório...")
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        repo_name = urlparse(self.repo_url).path.strip("/").replace(".git", "").replace("/", "_")
        self.repo_path = os.path.join(base_path, repo_name)
        if os.path.exists(self.repo_path):
            print(f"[fetcher] Repositório já existe. Apagando para clonar novamente.")
            shutil.rmtree(self.repo_path)
        print(f"[fetcher] Clonando {self.repo_url} para {self.repo_path}...")
        Repo.clone_from(self.repo_url, self.repo_path)
        print(f"Repositório clonado em: {self.repo_path}")

    # --- Etapa 2: Classificação de Arquivos ---
    def classify_files(self):
        print("\n[2] Classificando arquivos...")
        EXT_MAP = {
            "documentacao": ["*.md", "*.txt", "LICENSE", "CONTRIBUTING"],
            "build": ["Dockerfile", "Makefile", "*.sh", "*.bat"],
            "configuracao": ["*.json", "*.xml", "*.yml", "*.yaml", "*.toml", "*.ini", "*.cfg"],
            "dependencias": ["package.json", "requirements.txt", "pom.xml", "build.gradle", "Gemfile"],
            "frontend": ["*.js", "*.jsx", "*.ts", "*.tsx", "*.vue", "*.html", "*.css", "*.scss"],
            "backend": ["*.py", "*.rb", "*.java", "*.go", "*.rs", "*.php", "*.cs", "*.js", "*.ts"],
            "teste": ["*.test.js", "*.spec.ts", "*.test.py", "*.spec.rb", "tests/", "specs/"],
            "infra": ["*.tf", "*.tfvars", "ansible/", "puppet/"],
            "api": ["*.proto", "*.graphql", "swagger.yaml", "openapi.json"],
            "notebooks": ["*.ipynb"],
            "dados": ["*.sql", "*.csv", "*.parquet"],
        }
        self.classification = defaultdict(list)
        classified_files = set()
        for root, dirs, files in os.walk(self.repo_path):
            if ".git" in dirs:
                dirs.remove(".git")
            for file in files:
                filepath = os.path.join(root, file)
                if filepath in classified_files:
                    continue
                # Lógica de classificação
                for category, patterns in EXT_MAP.items():
                    if file in patterns or f"*{os.path.splitext(file)[1]}" in patterns or any(p.endswith("/") and p in filepath for p in patterns):
                        self.classification[category].append(filepath)
                        classified_files.add(filepath)
                        break
                if filepath not in classified_files:
                    self.classification["outros"].append(filepath)
        for category, files in self.classification.items():
            if files:
                print(f"- {category}: {len(files)} arquivos")

    # --- (Outras etapas como placeholders) ---
    def read_commits(self):
        print("\n[3] Lendo commits... (TODO)")
        self.commits = {}

    def analyze_codebase(self):
        print("\n[4] Analisando o código...")
        categories_to_analyze = ["backend", "frontend", "teste", "api"]
        files_to_analyze = []
        for category in categories_to_analyze:
            if category in self.classification:
                files_to_analyze.extend(self.classification[category])
        if not files_to_analyze:
            print("- Nenhum arquivo de código encontrado para análise.")
            return

        for filepath in files_to_analyze:
            analysis = self._analyze_single_file(filepath)
            if analysis and not analysis.get("error"):
                if analysis.get("functions") or analysis.get("classes") or analysis.get("constants") or analysis.get("endpoints"):
                    self.code_analysis[filepath] = analysis
        print(f"- Análise de código concluída para {len(self.code_analysis)} arquivos.")

    def _analyze_single_file(self, filepath):
        if filepath in self.ANALYSIS_CACHE:
            return self.ANALYSIS_CACHE[filepath]

        _, extension = os.path.splitext(filepath)
        analysis = {"imports": [], "functions": [], "classes": [], "constants": [], "endpoints": [], "error": None}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if extension == ".py":
                analysis.update(self._analyze_python(content))
            elif extension in [".js", ".jsx", ".ts", ".tsx"]:
                analysis.update(self._analyze_js(content))
            elif extension == ".java":
                analysis.update(self._analyze_java(content))
            elif extension in [".md", ".txt", ".html", ".css"]:
                self.ANALYSIS_CACHE[filepath] = analysis
                return analysis

            for pattern in self._get_api_patterns():
                for match in pattern.finditer(content):
                    analysis["endpoints"].append({"method": match.group(1).upper(), "path": match.group(2)})

        except Exception as e:
            analysis["error"] = f"Falha ao analisar o arquivo: {e}"

        self.ANALYSIS_CACHE[filepath] = analysis
        return analysis

    def _get_api_patterns(self):
        return [
            re.compile(r"@(?:app|router)\.(get|post|put|delete|patch)\([\'\"](.*?)['\"]"),
            re.compile(r"(?:app|router)\.(get|post|put|delete|patch)\([\'\"](.*?)['\"],")
        ]

    def _analyze_python(self, content):
        tree = ast.parse(content)
        analysis = {"imports": [], "functions": [], "classes": [], "constants": []}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.isupper():
                analysis["constants"].append({"name": node.targets[0].id, "value": ast.get_source_segment(content, node.value)})
            elif isinstance(node, ast.FunctionDef):
                analysis["functions"].append({"name": node.name, "args": [arg.arg for arg in node.args.args], "docstring": ast.get_docstring(node) or "", "code_block": ast.get_source_segment(content, node)})
        return analysis

    def _analyze_js(self, content):
        patterns = {
            "imports": re.compile(r"import(?:\s+.*?\s+from)?\s+['\"](.*?)['\"]"),
            "functions": re.compile(r"(?:function|const|let)\s+([\w\$]+)\s*=\s*(?:\([^)]*\)|async\s*\([^)]*\))\s*=>|function\s+([\w\$]+)\s*\(([^)]*)\)"),
            "classes": re.compile(r"class\s+([\w\$]+)"),
            "constants": re.compile(r"const\s+([A-Z_][A-Z0-9_]*)\s*=")
        }
        return self._analyze_generic_with_regex(content, patterns)

    def _analyze_java(self, content):
        patterns = {
            "imports": re.compile(r"import\s+(.*?);"),
            "classes": re.compile(r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)"),
            "functions": re.compile(r"(?:public|private|protected)?\s*(?:static|final|abstract)?\s*\w+(?:<.*?>)?\s+(\w+)\s*\(([^)]*)\)"),
            "constants": re.compile(r"(?:public|private|protected)?\s*static final\s+\w+\s+([A-Z_][A-Z0-9_]*)\s*=")
        }
        return self._analyze_generic_with_regex(content, patterns)

    def _analyze_generic_with_regex(self, content, patterns):
        analysis = {"imports": [], "functions": [], "classes": [], "constants": []}
        for key, pattern in patterns.items():
            for match in pattern.finditer(content):
                if key == "functions":
                    func_name = match.group(1) or match.group(2)
                    args_str = match.group(3) or ""
                    args = [arg.strip() for arg in args_str.split(",") if arg.strip()]
                    analysis[key].append({"name": func_name, "args": args, "docstring": "", "code_block": match.group(0)})
                else:
                    name = next((g for g in match.groups() if g is not None), None)
                    if name:
                        analysis[key].append({"name": name, "code_block": match.group(0)})
        return analysis

    # --- Etapa 5: Geração de Documentação ---
    def build_documentation(self):
        print("\n[5] Gerando documentação...")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[doc_builder] Chave da API não encontrada.")
            return None

        prompt = self._build_killer_prompt()
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        system_message = ("Você é um arquiteto de soluções e redator técnico de elite, com a rara habilidade de analisar sistemas complexos e produzir documentação cristalina. "
                          "Sua análise é incisiva, precisa e antecipa as necessidades do leitor. Você segue padrões de documentação rigorosos como o 'Diátaxis' e o 'arc42'. "
                          "Seu público são outros engenheiros de software; a clareza e a precisão técnica são imperativas. Use Markdown e formatação Mermaid para diagramas quando aplicável.")

        payload = {
            "model": "gpt-4o",
            "messages": [{"role": "system", "content": system_message}, {"role": "user", "content": prompt}],
            "temperature": 0.4
        }

        print("[doc_builder] Gerando documentação com o prompt de elite...")
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            response_data = response.json()
            doc_content = response_data["choices"][0]["message"]["content"]
            token_usage = response_data.get("usage", {})
            print(f"[doc_builder] Total de tokens usados: {token_usage.get('total_tokens', 'N/A')}")
            doc_filepath = os.path.join(self.repo_path, "README_GERADO.md")
            with open(doc_filepath, "w", encoding="utf-8") as f:
                f.write(doc_content)
            return doc_filepath
        except Exception as e:
            print(f"[doc_builder] Erro na chamada da API: {e}")
            return None

    def _build_killer_prompt(self):
        repo_name = os.path.basename(self.repo_path.strip("/"))
        prompt = f"# Análise e Documentação Técnica do Projeto: {repo_name}\n\n## 1. Análise Arquitetural (Framework Diátaxis - Visão Geral)\n\nCom base em toda a informação fornecida (estrutura de arquivos, código-fonte, commits), sintetize a arquitetura do projeto. Descreva o **propósito fundamental**, o **domínio do problema** que ele resolve, e os **principais componentes de software** e suas interações. Se possível, gere um diagrama de componentes simples usando Mermaid.\n\n## 2. Guia de Iniciação Rápida (Tutorial)\n\nCrie um guia passo a passo para um novo desenvolvedor configurar e executar este projeto localmente. Baseie-se nos arquivos de dependência (ex: `package.json`, `requirements.txt`) e de build.\n\n## 3. Referência Técnica Detalhada (How-to Guides & Reference)\n\n### 3.1. Estrutura do Projeto\n\n(Aqui você descreve a estrutura de arquivos que já estava sendo feita)\n\n### 3.2. Análise do Código-Fonte\n\nPara cada arquivo analisado, gere a documentação técnica seguindo o formato rigoroso abaixo:\n\n"

        for filepath, analysis in self.code_analysis.items():
            rel_path = os.path.relpath(filepath, self.repo_path)
            prompt += f"#### Arquivo: `{rel_path}`\n\n"

            if analysis.get("constants"):
                prompt += "##### Constantes e Variáveis Globais\n| Nome | Valor/Inicialização | Descrição |\n|---|---|---|\n"
                for const in analysis["constants"]:
                    prompt += f"| `{const['name']}` | `{const.get('value', 'N/A')}` | (Inferir o propósito da constante) |\n"
                prompt += "\n"

            if analysis.get("functions"):
                prompt += "##### Funções\n"
                for func in analysis["functions"]:
                    prompt += f"- **Função: `{func['name']}`**\n"
                    prompt += f"  - **Descrição:** (Analise o bloco de código e a docstring `{func.get('docstring', 'N/A')}` para criar uma descrição técnica precisa.)\n"
                    prompt += f"  - **Parâmetros:**\n    | Nome | Descrição |\n    |---|---|\n"
                    if func['args']:
                        for arg in func['args']:
                            prompt += f"    | `{arg}` | (Descreva o parâmetro) |\n"
                    else:
                        prompt += "    | N/A | - |\n"
                    prompt += f"  - **Retorno:** (Analise o bloco de código para determinar o que é retornado.)\n"
                    prompt += f"  - **Bloco de Código:**\n```python\n{func.get('code_block', 'N/A')}\n```\n"

            if analysis.get("endpoints"):
                prompt += "##### Endpoints de API\n| Método | Rota | Propósito Esperado |\n|---|---|---|\n"
                for ep in analysis["endpoints"]:
                    prompt += f"| `{ep['method']}` | `{ep['path']}` | (Inferir o propósito do endpoint) |\n"
                prompt += "\n"

        prompt += "## 4. Análise do Histórico de Desenvolvimento (Explanation)\n\nCom base nos commits, resuma a evolução do projeto, destacando as principais features adicionadas e as correções mais relevantes.\n\n"

        if not self.commits:
            prompt += "Nenhum commit encontrado no histórico.\n\n"
        else:
            commit_count = 0
            for author, commit_list in self.commits.items():
                if commit_count >= 15:
                    break
                prompt += f"### Commits de {author}\n"
                for commit in commit_list[:5]:
                    if commit_count >= 15:
                        break
                    prompt += f"- `[{commit['hash'][:7]}]` {commit['message']}\n"
                    commit_count += 1
                prompt += "\n"

        prompt += "---\n*Documentação gerada por um especialista em análise de sistemas. Revise para garantir 100% de precisão.*"
        return prompt

    # --- Etapa 6: Criação de Pull Request ---
    def create_pull_request(self):
        print("\n[6] Criando Pull Request...")
        # 0. Verifica se o gh CLI está instalado
        if subprocess.run(["command", "-v", "gh"], capture_output=True).returncode != 0:
            print("[gh_manager] Erro: O GitHub CLI ('gh') não está instalado ou não foi encontrado no PATH.")
            return None

        # 1. Define nomes e mensagens
        branch_name = f"gemini-docs-{int(time.time())}"
        commit_message = "docs: Add auto-generated project documentation"
        pr_title = "[AI] Documentação Automática do Projeto"
        pr_body = ("Este Pull Request foi gerado automaticamente por um agente de IA.\n\n"
                   "Ele contém uma documentação inicial do projeto, criada a partir da análise estática "
                   "do código-fonte, estrutura de arquivos e histórico de commits.\n\n"
                   "**Por favor, revise cuidadosamente antes de fazer o merge.**")

        # 2. Configura o usuário do Git para o commit
        self._run_command(["git", "config", "user.name", "Gemini Documentation Agent"])
        self._run_command(["git", "config", "user.email", "gemini-agent@google.com"])

        # 3. Cria um novo branch
        success, _ = self._run_command(["git", "checkout", "-b", branch_name])
        if not success: return None

        # 4. Adiciona e commita o arquivo de documentação
        success, _ = self._run_command(["git", "add", "README_GERADO.md"])
        if not success: return None

        success, _ = self._run_command(["git", "commit", "-m", commit_message])
        if not success: return None

        # 5. Faz o push do novo branch
        success, _ = self._run_command(["git", "push", "-u", "origin", branch_name])
        if not success: return None

        # 6. Cria o Pull Request usando o gh CLI
        print("[gh_manager] Criando o Pull Request...")
        success, output = self._run_command(["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--fill"])
        if not success:
            return None

        pr_url = output.strip()
        print(f"[gh_manager] Pull Request criado com sucesso: {pr_url}")
        return pr_url

    def _run_command(self, command):
        """Helper para executar comandos no shell dentro do repo_path."""
        print(f"[gh_manager] Executando: {' '.join(command)}")
        result = subprocess.run(command, cwd=self.repo_path, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[gh_manager] Erro: {result.stderr}")
            return False, result.stderr
        return True, result.stdout

    def run(self):
        try:
            self.fetch_repository()
            self.classify_files()
            self.read_commits()
            self.analyze_codebase()
            doc_path = self.build_documentation()
            if doc_path:
                print(f"- Documentação gerada em: {doc_path}")
                pr_url = self.create_pull_request()
                if pr_url:
                    print(f"- Pull Request criado com sucesso: {pr_url}")
                else:
                    print("- Falha ao criar o Pull Request.")
            else:
                print("- Falha ao gerar a documentação.")
        except Exception as e:
            print(f"\nOcorreu um erro fatal: {e}")
            sys.exit(1)

def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print("Uso: python orquestrador.py <url-do-repositorio-github>")
        sys.exit(1)
    repo_url = sys.argv[1]
    orchestrator = ProjectOrchestrator(repo_url)
    orchestrator.run()

if __name__ == "__main__":
    main()
