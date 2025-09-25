import os
import argparse
import pandas as pd
from github import Github

def fetch_commits(repo_name: str, max_commits: int = None) -> pd.DataFrame:
    """
    Fetch up to `max_commits` from the specified GitHub repository.
    Returns a DataFrame with columns: sha, author, email, date, message.
    """
    # 1) Read GitHub token from environment
    # TODO
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN not found in environment variables.")

    # 2) Initialize GitHub client and get the repo
    # TODO
    git = Github(token)
    repo = git.get_repo(repo_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    # TODO
    commits = []
    i = 0
    for commit in repo.get_commits():
        if max_commits is not None and i >= max_commits:
            break

        author = commit.author
        commit_data = commit.commit

    # 4) Normalize each commit into a record dict
    # TODO
    
        record = {
            "sha": commit.sha,
            "author": author.name if author else None,
            "email": author.email if author else None,
            "date": commit_data.author.date.isoformat(),
            "message": commit_data.message.split('\n')[0]
        }
        commits.append(record)
        i += 1

    # 5) Build DataFrame from records
    # TODO
    return pd.DataFrame(commits)
    

def main():
    """
    Parse command-line arguments and dispatch to sub-commands.
    """
    parser = argparse.ArgumentParser(
        prog="repo_miner",
        description="Fetch GitHub commits/issues and summarize them"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub-command: fetch-commits
    c1 = subparsers.add_parser("fetch-commits", help="Fetch commits and save to CSV")
    c1.add_argument("--repo", required=True, help="Repository in owner/repo format")
    c1.add_argument("--max",  type=int, dest="max_commits",
                    help="Max number of commits to fetch")
    c1.add_argument("--out",  required=True, help="Path to output commits CSV")

    args = parser.parse_args()

    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

if __name__ == "__main__":
    main()
