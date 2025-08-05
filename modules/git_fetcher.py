from git import Repo
import os
import shutil
from urllib.parse import urlparse

def fetch_repository(repo_url, base_path=".repos"):
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    repo_name = urlparse(repo_url).path.strip("/").replace(".git", "").replace("/", "_")
    repo_path = os.path.join(base_path, repo_name)

    if os.path.exists(repo_path):
        print(f"[git_fetcher] Repositório já existe. Apagando para clonar novamente.")
        shutil.rmtree(repo_path)

    print(f"[git_fetcher] Clonando {repo_url} para {repo_path}...")
    Repo.clone_from(repo_url, repo_path)
    return repo_path