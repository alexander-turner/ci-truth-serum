"""Shared pytest fixtures for the shell-script tests."""

import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from tests._helpers import copy_script_to, git_env, init_test_repo


@pytest.fixture
def empty_git_repo(tmp_path: Path) -> Iterator[Path]:
    """Throwaway git repo with an initial empty commit (so HEAD exists)."""
    init_test_repo(tmp_path)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-q", "-m", "init"],
        cwd=tmp_path,
        env=git_env(),
        check=True,
    )
    yield tmp_path


@pytest.fixture
def copy_script() -> Callable[[str, Path], Path]:
    """Return a helper that copies a hook script into a sandbox dir."""
    return copy_script_to
