from git import Repo
from collections import defaultdict

def read_commits(repo_path):
    """
    Lê o histórico de commits de um repositório e agrupa por autor.
    """
    repo = Repo(repo_path)
    commits_by_author = defaultdict(list)

    for commit in repo.iter_commits():
        author = commit.author.name
        commit_data = {
            "hash": commit.hexsha,
            "message": commit.message.strip(),
            "date": commit.committed_datetime.isoformat(),
        }
        commits_by_author[author].append(commit_data)

    return dict(commits_by_author)