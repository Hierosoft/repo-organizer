import shlex
import subprocess

# from typing import List


# def list_remote_branches(repo_path: str, name_only: bool) -> List[str]:
def list_remote_branches(repo_path, name_only=True, trunks=["origin"]):
    """List all remote branches in a local Git repository,
    including those not yet fetched.

    Args:
        repo_path (str): Path to the local Git repository.
        name_only (bool): Get the branch names only, no trunks included.
            - False example: ['origin/HEAD -> origin/main',
              'origin/main', 'upstream/HEAD -> upstream/main',
              'upstream/main', 'upstream/test'] (This is the format
              shown line by line from `git -C $path branch -r` after
              `git -C $path fetch --all`)
            - True example (same data as previous example): ['main',
              'test']
        trunks (list[str]): Trunks to use. None for all. Do *not*
            include upstream if you are trying to get branches already
            in your origin. The "upstream" is typically a different repo
            from which yours was forked. If you include it, you would
            have to get it yourself or show the user a warning if
            desired, by comparing the result of trunks=["origin"] and
            trunks=None

    Returns:
        List[str]: A list of remote branch names.
            Example where there is no local copy of "test" branch yet:
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
        names = set()
        for branch in branches:
            sides = branch.split()
            parts = sides[0].split("/")
            if len(parts) != 2:
                print("Warning: expected trunk/branch got {} in {}"
                      .format(repr(sides[0]), repr(branch)))
                continue
            trunk, branch = parts  # such as ["origin", "main"]
            #   (usually lists both origin and upstream copies of main)
            if trunks and trunk not in trunks:
                print("Skipped unknown trunk {} in {}"
                      .format(repr(trunk), repr(repo_path)))
                continue
            print("Using trunk {} in {}"
                  .format(repr(trunk), repr(repo_path)))
            if branch.upper() == "HEAD":
                # Not a visible branch, just represents what is checked out.
                continue
            names.add(branch)  # such as "main"
        if name_only:
            return list(names)
        return branches

    except subprocess.CalledProcessError as e:
        print("Error: {}".format(e.stderr.strip()))
        return []


def current_branch(repo_path):
    """Find out which branch is checked out at the given path."""
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "branch"],
            capture_output=True,
            text=True,
            check=True
        )

        # Clean and return branch names
        branches = [
            branch.strip() for branch in result.stdout.splitlines()
            if branch.strip()
        ]
        for branch in branches:
            if branch.startswith("*"):
                # such as "* main"
                return branch[1:].strip()
        return None

    except subprocess.CalledProcessError as e:
        print("Error: {}".format(e.stderr.strip()))
        return None


def switch_branch(repo_path, set_branch):
    """Find out which branch is checked out at the given path.

    Returns:
        dict: Information about checkout. If returns 'name' but not
            'trunk_and_branch', then it must be a local-only branch (not
            uploaded) and a warning will be shown. If ok, should have:
            - 'trunk_and_branch': such as "origin/main"
            - 'name': such as "main"
    """
    try:
        cmd_parts = ["git", "-C", repo_path, "switch", set_branch]
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            check=True
        )
        # Example (doesn't raise exception in Windows, somehow...):
        # fatal: cannot change to ''C:\Users\redacted\git\depot-launcher'': Invalid argument  # noqa:E501
        # C:\Users\redacted\git\Depot>echo %ERRORLEVEL%
        # 128

        # Example if already on branch:
        # Already on 'main'

        # Example Exception on incorrect branch:
        # fatal: invalid reference: main2

        print("Stderr: {}".format(result.stderr))
        print(shlex.join(cmd_parts).replace("'", '"'))
        # ^ Only double quote (") allowed for Command Prompt on Windows
        #   (Works fine in Terminal a.k.a. PowerShell)

        # Parse the result of switch.
        # Example (where two files were modified remotely):
        # M       README.md
        # M       repoorganizer/__init__.py
        # Switched to branch 'main'
        # Your branch is up to date with 'origin/main'.
        lines = [
            line.strip() for line in result.stdout.splitlines()
            if line.strip()
        ]
        err_lines = [  # Since may contain warning such as:
            # Already on 'main'
            # and not raise CalledProcessError
            line.strip() for line in result.stderr.splitlines()
            if line.strip()
        ]
        results = {}
        flags = {}
        flags['name'] = "Switched to branch"
        flags['name2'] = "Already on"
        flags['trunk_and_branch'] = "Your branch is up to date with"
        splits = {}
        for k, v in flags.items():
            splits[k] = v.split()
        for line in lines + err_lines:
            print("{}".format(line))
            parts = line.split()
            for key, expected in flags.items():
                exp_parts = splits[key]
                if parts[:len(exp_parts)] == exp_parts:
                    if len(parts) < len(exp_parts) + 1:
                        print(
                            "Warning: Expected a name after {} in {}"
                            .format(repr(expected), repr(line))
                        )
                    else:
                        results[key] = parts[len(exp_parts)].strip("'.")
                else:
                    pass
                    # print("{} is not like {}"
                    #       .format(parts[:len(exp_parts)], exp_parts))
        if 'name2' in results:
            # Simplify the alternate key.
            results['name'] = results['name2']
            del results['name2']
        if ('name' not in results) and ('trunk_and_branch' in results):
            parts = results['trunk_and_branch'].split("/")
            if len(parts) == 2:
                results['name'] = parts[1]  # such as "main" in "origin/main"
        if ('name' in results) and ('trunk_and_branch' not in results):
            print("Warning: {} appears to be a local-only branch."
                  .format(results['name']))
        return results

    except subprocess.CalledProcessError as e:
        print("CalledProcessError: {}".format(e.stderr.strip()))
        return None
