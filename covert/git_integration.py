"""Git integration module for Covert.

This module provides Git integration features:
- Create branches for updates
- Commit changes automatically
- Create Pull Requests
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from covert.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GitConfig:
    """Configuration for Git operations."""

    branch: Optional[str] = None
    commit: bool = False
    create_pr: bool = False
    commit_message: str = "chore: update dependencies"
    auto_merge: bool = False
    auto_merge_method: str = "squash"
    required_checks: Optional[List[str]] = None


class GitError(Exception):
    """Error during Git operations."""

    pass


def run_git_command(args: List[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a git command securely.

    Args:
        args: Git command arguments (without 'git').
        capture: Whether to capture output.

    Returns:
        CompletedProcess result.

    Raises:
        GitError: If command fails.
    """
    cmd = ["git"] + args
    logger.debug(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            check=False,
            shell=False,
        )
        if result.returncode != 0:
            raise GitError(f"Git command failed: {result.stderr}")
        return result
    except FileNotFoundError:
        raise GitError("Git not found. Is Git installed?")
    except Exception as e:
        raise GitError(f"Git command failed: {e}")


def is_git_repo(path: Optional[Path] = None) -> bool:
    """Check if path is a Git repository.

    Args:
        path: Path to check. Defaults to current directory.

    Returns:
        True if path is a Git repository.
    """
    try:
        run_git_command(["rev-parse", "--git-dir"], capture=True)
        return True
    except GitError:
        return False


def get_current_branch() -> str:
    """Get the current branch name.

    Returns:
        Current branch name.

    Raises:
        GitError: If not in a repo or on no branch.
    """
    result = run_git_command(["branch", "--show-current"])
    return result.stdout.strip()


def get_remote_url() -> Optional[str]:
    """Get the URL of the 'origin' remote.

    Returns:
        Remote URL or None if not available.
    """
    try:
        result = run_git_command(["remote", "get-url", "origin"])
        return result.stdout.strip()
    except GitError:
        return None


def create_branch(branch_name: str, checkout: bool = True) -> None:
    """Create a new Git branch.

    Args:
        branch_name: Name of the new branch.
        checkout: Whether to switch to the new branch after creation.

    Raises:
        GitError: If branch creation fails.
    """
    # Check if branch already exists
    try:
        run_git_command(["rev-parse", "--verify", branch_name])
        logger.info(f"Branch '{branch_name}' already exists, checking it out")
        if checkout:
            run_git_command(["checkout", branch_name])
    except GitError:
        # Branch doesn't exist, create it
        run_git_command(["branch", branch_name])
        logger.info(f"Created branch: {branch_name}")
        if checkout:
            run_git_command(["checkout", branch_name])
            logger.info(f"Switched to branch: {branch_name}")


def commit_changes(
    files: List[str],
    message: str,
    author: Optional[str] = None,
) -> str:
    """Commit changes to Git.

    Args:
        files: List of files to commit.
        message: Commit message.
        author: Optional author string (e.g., "Name <email>").

    Returns:
        Commit SHA.

    Raises:
        GitError: If commit fails.
    """
    # Add files
    run_git_command(["add"] + files)
    logger.info(f"Staged {len(files)} file(s)")

    # Build commit command
    cmd = ["commit", "-m", message]
    if author:
        cmd.extend(["--author", author])

    run_git_command(cmd)
    logger.info(f"Committed with message: {message}")

    # Get commit SHA
    result = run_git_command(["rev-parse", "HEAD"])
    return result.stdout.strip()[:8]


def push_branch(branch_name: str, remote: str = "origin", set_upstream: bool = True) -> None:
    """Push branch to remote.

    Args:
        branch_name: Name of branch to push.
        remote: Remote name (default: origin).
        set_upstream: Whether to set upstream branch.

    Raises:
        GitError: If push fails.
    """
    cmd = ["push", remote, branch_name]
    if set_upstream:
        cmd.append("--set-upstream")

    run_git_command(cmd)
    logger.info(f"Pushed branch '{branch_name}' to {remote}")


def create_pull_request(
    title: str,
    body: str,
    head: str,
    base: str = "main",
    remote: str = "origin",
) -> Optional[str]:
    """Create a Pull Request using GitHub CLI.

    Args:
        title: PR title.
        body: PR body/description.
        head: Branch name containing changes.
        base: Base branch to merge into.
        remote: Remote name.

    Returns:
        PR URL if successful, None otherwise.
    """
    # Check if gh CLI is available
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
            shell=False,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.warning("GitHub CLI (gh) not found. Cannot create PR.")
        logger.info("Install gh from https://cli.github.com/")
        return None

    try:
        result = subprocess.run(
            [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--head", head,
                "--base", base,
            ],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )

        if result.returncode == 0:
            pr_url = result.stdout.strip()
            logger.info(f"Created PR: {pr_url}")
            return pr_url
        else:
            logger.error(f"Failed to create PR: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        return None


def perform_git_actions(
    files: List[str],
    config: GitConfig,
    commit_message: Optional[str] = None,
) -> Optional[str]:
    """Perform Git actions based on configuration.

    Args:
        files: List of files to commit.
        config: Git configuration.
        commit_message: Custom commit message.

    Returns:
        PR URL if PR was created, None otherwise.
    """
    if not is_git_repo():
        logger.warning("Not in a Git repository. Skipping Git operations.")
        return None

    pr_url = None

    # Create branch if requested
    if config.branch:
        original_branch = get_current_branch()
        create_branch(config.branch, checkout=True)

        # Commit changes
        if config.commit:
            message = commit_message or config.commit_message
            commit_sha = commit_changes(files, message)
            logger.info(f"Changes committed: {commit_sha}")

            # Push branch
            push_branch(config.branch)

            # Create PR if requested
            if config.create_pr:
                remote_url = get_remote_url()
                if remote_url and "github.com" in remote_url:
                    pr_title = f"Update dependencies - {config.branch}"
                    pr_body = f"""## Summary

Automated dependency update by Covert.

### Changes

- Updated packages: {', '.join(files)}

### Testing

Please ensure all tests pass before merging.

---
*Generated by Covert*"""

                    pr_url = create_pull_request(
                        title=pr_title,
                        body=pr_body,
                        head=config.branch,
                    )

                    if pr_url:
                        logger.info(f"Pull Request created: {pr_url}")

                        # Auto-merge if requested
                        if config.auto_merge:
                            auto_merge_pr(pr_url, config.auto_merge_method, config.required_checks)
                else:
                    logger.warning("Remote is not GitHub. Cannot create PR automatically.")
                    logger.info("Push your branch manually and create a PR.")
        else:
            logger.info(f"Branch '{config.branch}' created. Commit and push manually.")

        return pr_url
    else:
        # No branch requested, just commit if asked
        if config.commit:
            message = commit_message or config.commit_message
            commit_sha = commit_changes(files, message)
            logger.info(f"Changes committed: {commit_sha}")

    return pr_url


def auto_merge_pr(
    pr_url: str,
    merge_method: str = "squash",
    required_checks: Optional[List[str]] = None,
) -> bool:
    """Auto-merge a pull request when checks pass (Dependabot style).

    Args:
        pr_url: URL of the pull request.
        merge_method: Merge method (squash, merge, rebase).
        required_checks: List of required checks that must pass.

    Returns:
        True if merge was successful or waiting for checks.
    """
    import time

    # Check if gh CLI is available
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True,
            shell=False,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.warning("GitHub CLI (gh) not found. Cannot auto-merge.")
        return False

    # Extract PR number from URL
    # URL format: https://github.com/owner/repo/pull/123
    pr_number = pr_url.split("/")[-1]

    try:
        # Wait for PR checks to pass
        if required_checks:
            logger.info(f"Waiting for required checks: {', '.join(required_checks)}")
            max_wait = 300  # 5 minutes max
            wait_interval = 10  # Check every 10 seconds

            for _ in range(max_wait // wait_interval):
                # Get PR status
                result = subprocess.run(
                    ["gh", "pr", "view", pr_number, "--json", "statusCheckRollup"],
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,
                )

                if result.returncode == 0:
                    import json

                    data = json.loads(result.stdout)
                    checks = data.get("statusCheckRollup", [])

                    # Check if all required checks passed
                    all_passed = True
                    for required in required_checks:
                        check_found = False
                        for check in checks:
                            if required.lower() in check.get("name", "").lower():
                                check_found = True
                                if check.get("conclusion") != "SUCCESS":
                                    all_passed = False
                                    break
                        if not check_found:
                            all_passed = False

                    if all_passed:
                        logger.info("All required checks passed!")
                        break
                    else:
                        logger.info("Checks still running, waiting...")
                        time.sleep(wait_interval)
                else:
                    time.sleep(wait_interval)

        # Merge the PR
        logger.info(f"Merging PR #{pr_number} using {merge_method} merge...")
        result = subprocess.run(
            ["gh", "pr", "merge", pr_number, f"--{merge_method}", "--auto"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )

        if result.returncode == 0:
            logger.info(f"PR #{pr_number} merged successfully!")
            return True
        else:
            logger.error(f"Failed to merge PR: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error during auto-merge: {e}")
        return False
