import subprocess
from typing import List


# def list_remote_branches(repo_path: str) -> List[str]:
def list_remote_branches(repo_path):
    """List all remote branches in a local Git repository,
    including those not yet fetched.

    Args:
        repo_path (str): Path to the local Git repository.

    Returns:
        List[str]: A list of remote branch names.
    """
    try:
        # Fetch all updates from the remote repository
        subprocess.run(
            ["git", "-C", repo_path, "fetch", "--all"],
            capture_output=True,
            text=True,
            check=True
        )

        # List remote branches
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-r"],
            capture_output=True,
            text=True,
            check=True
        )

        # Clean and return branch names
        branches = [
            branch.strip() for branch in result.stdout.splitlines()
            if branch.strip()
        ]
        return branches

    except subprocess.CalledProcessError as e:
        print("Error: {}".format(e.stderr.strip()))
        return []
