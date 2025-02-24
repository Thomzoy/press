from pathlib import Path
import fsspec
import requests


def download_pdfs():
    r = requests.get("https://api.github.com/repos/Thomzoy/press/git/refs/heads/gh-pages")
    sha = r.json()["object"]["sha"]

    destination = Path("./Journaux_existing")
    destination.mkdir(exist_ok=True, parents=True)
    fs = fsspec.filesystem("github", org="Thomzoy", repo="press", sha=sha)
    fs.get(fs.ls("Journaux/"), destination.as_posix(), recursive=True)

if __name__ == "__main__":
    download_pdfs()
