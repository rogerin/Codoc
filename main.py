import sys
import os
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict
from dotenv import load_dotenv

from modules.git_fetcher import fetch_repository
from modules.file_classifier import classify_files
from modules.commit_reader import read_commits
from modules.code_analyzer import analyze_code
from modules.documentation_builder import build_documentation
from modules.github_manager import create_pull_request


def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print("Uso: python main.py <url-do-repositorio-github>")
        sys.exit(1)

    repo_url = sys.argv[1]
    
    try:
        print("[1] Clonando repositório...")
        repo_path = fetch_repository(repo_url)
        print(f"Repositório clonado em: {repo_path}")
    except Exception as e:
        print(f"Erro ao clonar o repositório: {e}")
        sys.exit(1)

    print("\n[2] Classificando arquivos...")
    classification = classify_files(repo_path)
    for category, files in classification.items():
        print(f"- {category}: {len(files)} arquivos")

    print("\n[3] Lendo commits...")
    commits = read_commits(repo_path)
    print(f"- Encontrados {sum(len(c) for c in commits.values())} commits de {len(commits)} autores.")

    print("\n[4] Analisando o código...")
    code_analysis = defaultdict(dict)
    # Define as categorias de arquivos que contêm código que deve ser analisado
    categories_to_analyze = ["backend", "frontend", "teste", "api"]
    
    files_to_analyze = []
    for category in categories_to_analyze:
        if category in classification:
            files_to_analyze.extend(classification[category])

    if not files_to_analyze:
        print("- Nenhum arquivo de código encontrado para análise nas categorias relevantes.")
    else:
        for filepath in files_to_analyze:
            analysis = analyze_code(filepath)
            # Adiciona a análise apenas se não houver erro e se algo útil foi de fato encontrado
            if analysis and not analysis.get("error"):
                if analysis.get("functions") or analysis.get("classes") or analysis.get("constants") or analysis.get("endpoints"):
                    code_analysis[filepath] = analysis

        print(f"- Análise de código concluída para {len(code_analysis)} arquivos.")

    print("\n[5] Gerando documentação...")
    doc_path = build_documentation(repo_path, classification, commits, code_analysis)
    if doc_path:
        print(f"- Documentação gerada em: {doc_path}")
        # print("\n[6] Criando Pull Request...")
        # pr_url = create_pull_request(repo_path)
        # if pr_url:
        #     print(f"- Pull Request criado com sucesso: {pr_url}")
        # else:
        #     print("- Falha ao criar o Pull Request. Verifique o log e se o 'gh' CLI está autenticado.")
    else:
        print("- Falha ao gerar a documentação. O Pull Request não será criado.")


if __name__ == "__main__":
    main()