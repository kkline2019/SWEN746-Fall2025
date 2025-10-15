import os
import argparse
import pandas as pd
from datetime import datetime, timezone
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

        
        author = commit.commit.author
        commit_data = commit.commit
    # 4) Normalize each commit into a record dict
    # TODO
    
        record = {
            "sha": commit.sha,
            "author": author.name,
            "email": author.email,
            "date": commit_data.author.date.isoformat(),
            "message": commit_data.message.split('\n')[0]
        }
        commits.append(record)
        i += 1

    # 5) Build DataFrame from records
    # TODO
    return pd.DataFrame(commits)

def fetch_issues(repo_full_name: str, state: str="all", max_issues: int=None) -> pd.DataFrame:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise EnvironmentError("GITHUB_TOKEN not found in environment variables.")
    
    # 2) Initialize GitHub client and get the repo
    # TODO
    git = Github(token)
    repo = git.get_repo(repo_full_name)

    # 3) Fetch commit objects (paginated by PyGitHub)
    # TODO
    issues = []
    i = 0

    for issue in repo.get_issues(state=state):
        if max_issues is not None and i >= max_issues:
            break
        
        if issue.state == "closed":
            duration = issue.closed_at - issue.created_at
            duration_days = duration.days
            closed_at = issue.closed_at.isoformat()
        else:
            closed_at = None
            created = datetime.fromisoformat(str(issue.created_at)).replace(tzinfo=timezone.utc)
            duration_days = datetime.now(timezone.utc) - created
        
        if issue.pull_request == None:
            record = {
                "id" : issue.id,
                "number" : issue.number,
                "title" : issue.title,
                "user" : issue.user,
                "state" : issue.state,
                "created_at" : issue.created_at.isoformat(),
                "closed_at" : closed_at,
                "open_duration_day" : duration_days,
                "comments" : issue.comments
            }

            issues.append(record)
            i += 1

    return pd.DataFrame(issues)
        
def merge_and_summarize(commits_df: pd.DataFrame, issues_df: pd.DataFrame) -> None:
    commiters = commits_df["author"].value_counts().head(5)

    print("Top 5 committers:")
    for issues, count in commiters.items():
        print(f"{issues}: {count} commits")

    num_issues = issues_df.shape[0]
    
    total_closed = (issues_df['state'] == 'closed').sum()

    closed_rate = total_closed / num_issues
    print(f"Issue close rate: {round(closed_rate, 2)}")

    created = pd.to_datetime(issues_df['created_at'])
    closed = pd.to_datetime(issues_df['closed_at'])

    durations = closed - created
    delta = pd.to_timedelta(durations)

    average_duration = delta.sum() / total_closed
    print(f"Avg. issue open duration: {average_duration}")

    

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

    # Sub-command: fetch-issues
    c2 = subparsers.add_parser("fetch-issues", help="Fetch issues and save to CSV")
    c2.add_argument("--repo",  required=True, help="Repository in owner/repo format")
    c2.add_argument("--state", choices=["all","open","closed"], default="all",
                    help="Filter issues by state")
    c2.add_argument("--max",   type=int, dest="max_issues",
                    help="Max number of issues to fetch")
    c2.add_argument("--out",   required=True, help="Path to output issues CSV")

    c3 = subparsers.add_parser("summarize", help="Summarize commits and issues")
    c3.add_argument("--commits", required=True, help="Path to commits CSV file")
    c3.add_argument("--issues",  required=True, help="Path to issues CSV file")

    args = parser.parse_args()


    # Dispatch based on selected command
    if args.command == "fetch-commits":
        df = fetch_commits(args.repo, args.max_commits)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} commits to {args.out}")

    elif args.command == "fetch-issues":
        df = fetch_issues(args.repo, args.state, args.max_issues)
        df.to_csv(args.out, index=False)
        print(f"Saved {len(df)} issues to {args.out}")
    elif args.command == "summarize":
        # Read CSVs into DataFrames
        commits_df = pd.read_csv(args.commits)
        issues_df  = pd.read_csv(args.issues)
        # Generate and print the summary
        merge_and_summarize(commits_df, issues_df)



if __name__ == "__main__":
    main()

def test_fetch_issues_basic(monkeypatch):
    now = datetime.now()
    issues = [
        DummyIssue(1, 101, "Issue A", "alice", "open", now, None, 0),
        DummyIssue(2, 102, "Issue B", "bob", "closed", now - timedelta(days=2), now, 2)
    ]
    gh_instance._repo = DummyRepo([], issues)
    df = fetch_issues("any/repo", state="all")
    assert {"id", "number", "title", "user", "state", "created_at", "closed_at", "comments"}.issubset(df.columns)
    assert len(df) == 2

