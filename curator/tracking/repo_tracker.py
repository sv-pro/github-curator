"""Git-native repository tracking for curation history."""

import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TrackingInfo:
    """Information about a tracked repository."""

    org: str
    repo: str
    local_path: Path
    remote_url: str
    last_updated: datetime
    curation_count: int


class RepoTracker:
    """Manages git-native tracking of curated repositories."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize repo tracker.

        Args:
            base_path: Base directory for tracked repos (default: ~/.github-curator/tracked)
        """
        if base_path is None:
            base_path = Path.home() / ".github-curator" / "tracked"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get_repo_path(self, org: str, repo: str) -> Path:
        """Get local path for a tracked repository."""
        return self.base_path / org / repo

    def is_tracked(self, org: str, repo: str) -> bool:
        """Check if a repository is already tracked."""
        repo_path = self.get_repo_path(org, repo)
        return repo_path.exists() and (repo_path / ".git").exists()

    def track(self, repo_url: str) -> TrackingInfo:
        """Start tracking a repository.

        Args:
            repo_url: GitHub repository URL (https://github.com/org/repo)

        Returns:
            TrackingInfo about the tracked repository

        Raises:
            ValueError: If URL is invalid or clone fails
        """
        # Parse org/repo from URL
        org, repo = self._parse_repo_url(repo_url)
        repo_path = self.get_repo_path(org, repo)

        if self.is_tracked(org, repo):
            logger.info(f"Repository {org}/{repo} already tracked at {repo_path}")
            return self._get_tracking_info(org, repo)

        # Clone the repository
        logger.info(f"Cloning {repo_url} to {repo_path}")
        repo_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            subprocess.run(
                ["git", "clone", repo_url, str(repo_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to clone repository: {e.stderr}") from None

        # Create curation branch
        self._run_git(repo_path, ["checkout", "-b", "curation"])

        # Create .curator directory for our files
        curator_dir = repo_path / ".curator"
        curator_dir.mkdir(exist_ok=True)

        # Initialize CURATION.md and REVIEW.md in .curator/
        curation_file = curator_dir / "CURATION.md"
        review_file = curator_dir / "REVIEW.md"

        curation_file.write_text(
            f"# Curation History: {org}/{repo}\n\n"
            f"This file tracks evaluation history using GitHub Curator.\n"
            f"Each evaluation is appended below with timestamp and results.\n\n"
            f"---\n\n"
        )

        review_file.write_text(
            f"# {repo}\n\n"
            f"> This review is auto-generated and updated by GitHub Curator.\n\n"
            f"*Not yet reviewed*\n"
        )

        # Initial commit
        self._run_git(repo_path, ["add", ".curator/CURATION.md", ".curator/REVIEW.md"])
        self._run_git(
            repo_path,
            [
                "commit",
                "-m",
                "chore: Initialize curation tracking\n\nAdded CURATION.md and REVIEW.md for evaluation history.",
            ],
        )

        logger.info(f"Successfully initialized tracking for {org}/{repo}")
        return self._get_tracking_info(org, repo)

    def update_from_upstream(self, org: str, repo: str) -> bool:
        """Pull latest changes from upstream repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            True if updates were pulled, False if already up-to-date

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        repo_path = self.get_repo_path(org, repo)

        # Switch to main/master branch
        try:
            self._run_git(repo_path, ["checkout", "main"])
        except subprocess.CalledProcessError:
            self._run_git(repo_path, ["checkout", "master"])

        # Pull latest changes
        result = self._run_git(repo_path, ["pull", "origin"])

        # Switch back to curation branch
        self._run_git(repo_path, ["checkout", "curation"])

        # Check if there were updates
        return "Already up to date" not in result.stdout

    def sync_all_branches(self, org: str, repo: str) -> dict[str, bool]:
        """Pull all branches from upstream repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Dict mapping branch names to whether they had updates

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        repo_path = self.get_repo_path(org, repo)
        updates = {}

        # Fetch all refs from origin
        self._run_git(repo_path, ["fetch", "--all", "--tags"])

        # Get list of remote branches
        result = self._run_git(repo_path, ["branch", "-r"])
        remote_branches = [
            line.strip().replace("origin/", "")
            for line in result.stdout.strip().split("\n")
            if "origin/" in line and "HEAD" not in line
        ]

        # Pull each branch
        for branch in remote_branches:
            try:
                # Skip curation branch (it's local only)
                if branch == "curation":
                    continue

                self._run_git(repo_path, ["checkout", branch])
                pull_result = self._run_git(repo_path, ["pull", "origin", branch])
                updates[branch] = "Already up to date" not in pull_result.stdout
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to pull branch {branch}: {e.stderr}")
                updates[branch] = False

        # Switch back to curation branch
        self._run_git(repo_path, ["checkout", "curation"])

        return updates

    def add_curation(
        self, org: str, repo: str, curation_content: str, review_content: str, theme: str
    ) -> str:
        """Add a new curation evaluation.

        Args:
            org: Organization name
            repo: Repository name
            curation_content: Content to append to CURATION.md
            review_content: Content to replace in REVIEW.md
            theme: Curation theme for commit message and tag

        Returns:
            Git tag name for this curation

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        repo_path = self.get_repo_path(org, repo)

        # Ensure we're on curation branch
        self._run_git(repo_path, ["checkout", "curation"])

        # Ensure .curator directory exists
        curator_dir = repo_path / ".curator"
        curator_dir.mkdir(exist_ok=True)

        # Append to .curator/CURATION.md
        curation_file = curator_dir / "CURATION.md"
        with curation_file.open("a") as f:
            f.write(curation_content)
            f.write("\n\n---\n\n")

        # Overwrite .curator/REVIEW.md
        review_file = curator_dir / "REVIEW.md"
        review_file.write_text(review_content)

        # Commit changes
        self._run_git(repo_path, ["add", ".curator/CURATION.md", ".curator/REVIEW.md"])

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        commit_msg = (
            f"curation: {theme}\n\n"
            f"Evaluated repository against theme: {theme}\n"
            f"Timestamp: {timestamp}\n"
            f"Updated CURATION.md (history) and REVIEW.md (latest review)"
        )

        self._run_git(repo_path, ["commit", "-m", commit_msg])

        # Create tag
        tag_name = self._generate_tag_name(repo_path)
        tag_msg = f"Curation: {theme}\n{timestamp}"
        self._run_git(repo_path, ["tag", "-a", tag_name, "-m", tag_msg])

        logger.info(f"Added curation for {org}/{repo} with tag {tag_name}")
        return tag_name

    def update_review(self, org: str, repo: str, review_content: str, theme: str) -> str:
        """Update review without appending to curation history.

        This is lighter than add_curation - only updates REVIEW.md without
        touching CURATION.md history.

        Args:
            org: Organization name
            repo: Repository name
            review_content: Content to replace in REVIEW.md
            theme: Review theme for commit message and tag

        Returns:
            Git tag name for this review

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        repo_path = self.get_repo_path(org, repo)

        # Ensure we're on curation branch
        self._run_git(repo_path, ["checkout", "curation"])

        # Ensure .curator directory exists
        curator_dir = repo_path / ".curator"
        curator_dir.mkdir(exist_ok=True)

        # Overwrite .curator/REVIEW.md
        review_file = curator_dir / "REVIEW.md"
        review_file.write_text(review_content)

        # Commit changes
        self._run_git(repo_path, ["add", ".curator/REVIEW.md"])

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        commit_msg = (
            f"review: {theme}\n\n"
            f"Updated review for theme: {theme}\n"
            f"Timestamp: {timestamp}\n"
            f"Updated REVIEW.md (curation history unchanged)"
        )

        self._run_git(repo_path, ["commit", "-m", commit_msg])

        # Create tag
        tag_name = self._generate_tag_name(repo_path, prefix="review")
        tag_msg = f"Review: {theme}\n{timestamp}"
        self._run_git(repo_path, ["tag", "-a", tag_name, "-m", tag_msg])

        logger.info(f"Updated review for {org}/{repo} with tag {tag_name}")
        return tag_name

    def get_curation_history(self, org: str, repo: str) -> str:
        """Get full curation history for a repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Contents of .curator/CURATION.md

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        curation_file = self.get_repo_path(org, repo) / ".curator" / "CURATION.md"
        return curation_file.read_text()

    def get_latest_review(self, org: str, repo: str) -> str:
        """Get latest review for a repository.

        Args:
            org: Organization name
            repo: Repository name

        Returns:
            Contents of .curator/REVIEW.md

        Raises:
            ValueError: If repository is not tracked
        """
        if not self.is_tracked(org, repo):
            raise ValueError(f"Repository {org}/{repo} is not tracked")

        review_file = self.get_repo_path(org, repo) / ".curator" / "REVIEW.md"
        return review_file.read_text()

    def list_tracked(self) -> list[TrackingInfo]:
        """List all tracked repositories.

        Returns:
            List of TrackingInfo for all tracked repositories
        """
        tracked: list[TrackingInfo] = []
        if not self.base_path.exists():
            return tracked

        for org_path in self.base_path.iterdir():
            if not org_path.is_dir():
                continue
            for repo_path in org_path.iterdir():
                if not repo_path.is_dir():
                    continue
                if (repo_path / ".git").exists():
                    org = org_path.name
                    repo = repo_path.name
                    tracked.append(self._get_tracking_info(org, repo))

        return tracked

    def _parse_repo_url(self, url: str) -> tuple[str, str]:
        """Parse org/repo from GitHub URL."""
        # Support: https://github.com/org/repo or https://github.com/org/repo.git
        if not url.startswith("https://github.com/"):
            raise ValueError(f"Invalid GitHub URL: {url}")

        parts = url.replace("https://github.com/", "").rstrip("/").replace(".git", "").split("/")

        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub URL format: {url}")

        return parts[0], parts[1]

    def _run_git(self, repo_path: Path, args: list[str]) -> subprocess.CompletedProcess:
        """Run git command in repository."""
        return subprocess.run(
            ["git", "-C", str(repo_path)] + args,
            check=True,
            capture_output=True,
            text=True,
        )

    def _generate_tag_name(self, repo_path: Path, prefix: str = "curation") -> str:
        """Generate unique tag name for curation or review.

        Args:
            repo_path: Path to repository
            prefix: Tag prefix (default: "curation", can be "review")

        Returns:
            Tag name like "curation-001-20251010" or "review-001-20251010"
        """
        # Count existing tags with this prefix
        result = self._run_git(repo_path, ["tag", "-l", f"{prefix}-*"])
        existing_tags = result.stdout.strip().split("\n") if result.stdout.strip() else []
        count = len(existing_tags) + 1

        timestamp = datetime.utcnow().strftime("%Y%m%d")
        return f"{prefix}-{count:03d}-{timestamp}"

    def _get_tracking_info(self, org: str, repo: str) -> TrackingInfo:
        """Get tracking info for a repository."""
        repo_path = self.get_repo_path(org, repo)

        # Get remote URL
        result = self._run_git(repo_path, ["remote", "get-url", "origin"])
        remote_url = result.stdout.strip()

        # Get last updated time (last commit on curation branch)
        self._run_git(repo_path, ["checkout", "curation"])
        result = self._run_git(repo_path, ["log", "-1", "--format=%cI"])
        last_updated_str = result.stdout.strip()
        last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))

        # Count curations (number of curation tags)
        result = self._run_git(repo_path, ["tag", "-l", "curation-*"])
        curation_count = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

        return TrackingInfo(
            org=org,
            repo=repo,
            local_path=repo_path,
            remote_url=remote_url,
            last_updated=last_updated,
            curation_count=curation_count,
        )
