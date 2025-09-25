# tests/test_repo.py

import os
import pandas as pd
import pytest
from github import Github
import vcr
from datetime import datetime, timedelta
from src.repo_miner import fetch_commits

# --- Dummy GitHub API objects for unit tests ---

class DummyAuthor:
    def __init__(self, name, email, date):
        self.name = name
        self.email = email
        self.date = date

class DummyCommitCommit:
    def __init__(self, author, message):
        self.author = author
        self.message = message

class DummyCommit:
    def __init__(self, sha, author, email, date, message):
        self.sha = sha
        self.author = DummyAuthor(author, email, date)
        self.commit = DummyCommitCommit(DummyAuthor(author, email, date), message)

class DummyRepo:
    def __init__(self, commits):
        self._commits = commits

    def get_commits(self):
        return self._commits

class DummyGithub:
    def __init__(self, token):
        assert token == "fake-token"
    def get_repo(self, repo_name):
        return self._repo

# Global dummy instance
gh_instance = DummyGithub("fake-token")

# --- Monkeypatch for unit tests only ---
@pytest.fixture(autouse=True)
def patch_env_and_github(monkeypatch, request):
    if "use_real_github" not in request.keywords:
        monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
        monkeypatch.setattr("src.repo_miner.Github", lambda token: gh_instance)

# --- Unit Tests ---

def test_fetch_commits_basic():
    now = datetime.now()
    commits = [
        DummyCommit("sha1", "Alice", "a@example.com", now, "Initial commit\nDetails"),
        DummyCommit("sha2", "Bob", "b@example.com", now - timedelta(days=1), "Bug fix")
    ]
    gh_instance._repo = DummyRepo(commits)
    df = fetch_commits("any/repo")
    assert list(df.columns) == ["sha", "author", "email", "date", "message"]
    assert len(df) == 2
    assert df.iloc[0]["message"] == "Initial commit"

def test_fetch_commits_limit():
    now = datetime.now()
    commits = []


    for i in range(10):
        commits.append(DummyCommit(f"sha{i}", f"Author{i}", f"example{i}@asdfs.com", now - timedelta(days=i), f"Commit {i}"))

    gh_instance._repo = DummyRepo(commits)
    fetch = fetch_commits("any/repo", max_commits=3)
    assert len(fetch) == 3
    expected_shas = ["sha0", "sha1", "sha2"]
    actual_shas = fetch["sha"].tolist()
    assert actual_shas == expected_shas
    

def test_fetch_commits_empty():
    gh_instance._repo = DummyRepo([])
    fetch = fetch_commits("any/repo")
    assert isinstance(fetch, pd.DataFrame)
    assert fetch.empty

# --- Integration Test with vcrpy ---

my_vcr = vcr.VCR(
    cassette_library_dir="tests/cassettes",
    record_mode="once",
    match_on=["method", "uri"]
)

@pytest.mark.use_real_github
@my_vcr.use_cassette("octocat_hello_world_commits.yaml")
def test_fetch_commits_octocat_basic(monkeypatch):
    token = os.getenv("GITHUB_TOKEN")
    assert token, "GITHUB_TOKEN must be set to run this test"
    monkeypatch.setattr("src.repo_miner.Github", Github)

    df = fetch_commits("octocat/Hello-World", max_commits=5)
    assert not df.empty
    assert set(["sha", "author", "email", "date", "message"]).issubset(df.columns)
    assert df["email"].iloc[0] == "octocat@github.com"

@pytest.mark.use_real_github
@my_vcr.use_cassette("octocat_hello_world_zero.yaml")
def test_fetch_commits_octocat_zero(monkeypatch):
    monkeypatch.setattr("src.repo_miner.Github", Github)

    token = os.getenv("GITHUB_TOKEN")
    assert token, "GITHUB_TOKEN must be set"

    df = fetch_commits("octocat/Hello-World", max_commits=0)

    assert len(df.index) == 0
    assert len(df.columns) == 0
    assert df.empty