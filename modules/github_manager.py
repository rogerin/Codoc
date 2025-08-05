import os
import time
import subprocess

def run_command(command, cwd):
    """Executa um comando no shell e retorna o sucesso, stdout e stderr."""
    print(f"[gh_manager] Executando: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[gh_manager] Erro: {result.stderr}")
        return False, result.stderr
    return True, result.stdout

def create_pull_request(repo_path):
    """
    Cria um novo branch, commita a documentação e abre um Pull Request.
    """
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
    run_command(["git", "config", "user.name", "Gemini Documentation Agent"], cwd=repo_path)
    run_command(["git", "config", "user.email", "gemini-agent@google.com"], cwd=repo_path)

    # 3. Cria um novo branch
    success, _ = run_command(["git", "checkout", "-b", branch_name], cwd=repo_path)
    if not success: return None

    # 4. Adiciona e commita o arquivo de documentação
    success, _ = run_command(["git", "add", "README_GERADO.md"], cwd=repo_path)
    if not success: return None

    success, _ = run_command(["git", "commit", "-m", commit_message], cwd=repo_path)
    if not success: return None

    # 5. Faz o push do novo branch
    success, _ = run_command(["git", "push", "-u", "origin", branch_name], cwd=repo_path)
    if not success: return None

    # 6. Cria o Pull Request usando o gh CLI
    print("[gh_manager] Criando o Pull Request...")
    success, output = run_command(["gh", "pr", "create", "--title", pr_title, "--body", pr_body, "--fill"], cwd=repo_path)
    if not success:
        return None

    pr_url = output.strip()
    print(f"[gh_manager] Pull Request criado com sucesso: {pr_url}")
    return pr_url
