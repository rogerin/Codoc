import os
from collections import defaultdict

# Mapeamento mais detalhado de arquivos e extensões
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

def classify_files(repo_path):
    """
    Classifica os arquivos em um repositório com base em seus nomes, extensões e diretórios.
    """
    classification = defaultdict(list)
    
    # Mapeia todos os arquivos para evitar duplicação
    classified_files = set()

    for root, dirs, files in os.walk(repo_path):
        # Ignora o diretório .git
        if ".git" in dirs:
            dirs.remove(".git")

        for file in files:
            filepath = os.path.join(root, file)
            
            if filepath in classified_files:
                continue

            # 1. Classificação por nome de arquivo exato
            for category, patterns in EXT_MAP.items():
                if file in patterns:
                    classification[category].append(filepath)
                    classified_files.add(filepath)
                    break
            if filepath in classified_files:
                continue

            # 2. Classificação por extensão
            ext = f"*{os.path.splitext(file)[1]}"
            for category, patterns in EXT_MAP.items():
                if ext in patterns:
                    classification[category].append(filepath)
                    classified_files.add(filepath)
                    break
            if filepath in classified_files:
                continue

            # 3. Classificação por diretório
            for category, patterns in EXT_MAP.items():
                for pattern in patterns:
                    if pattern.endswith("/") and pattern in filepath:
                        classification[category].append(filepath)
                        classified_files.add(filepath)
                        break
                if filepath in classified_files:
                    break
            if filepath in classified_files:
                continue

            # 4. Arquivos não classificados
            classification["outros"].append(filepath)
            classified_files.add(filepath)

    return classification