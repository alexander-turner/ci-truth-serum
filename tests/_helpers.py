"""Shared helpers for the ci-truth-serum test suite.

Lives in a regular module (not ``conftest.py``) so it can be imported directly.
The repo root is resolved via ``git rev-parse`` rather than walking ``__file__``'s
parents by a hardcoded depth, so moving a test file never silently breaks discovery.
"""

import importlib.util
import shutil
import subprocess
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(
    subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
)
HOOKS_DIR = REPO_ROOT / "hooks"


def load_hook(filename: str, modname: str) -> ModuleType:
    """Load a hook script by path and run its functions directly.

    The hooks live outside any importable package layout the tests share, so each
    is loaded from its file. ``modname`` is the (arbitrary) module name to register.
    """
    src = HOOKS_DIR / filename
    spec = importlib.util.spec_from_file_location(modname, src)
    assert spec and spec.loader, src
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def git_env() -> dict[str, str]:
    """Environment for running git in test sandboxes."""
    import os

    return {**os.environ, **GIT_IDENTITY_ENV}


def init_test_repo(path: Path) -> None:
    """Init a throwaway repo with signing/hooks disabled so fixtures can commit in
    any environment (including CI runners with enforced commit signing)."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    for k, v in [
        ("commit.gpgsign", "false"),
        ("tag.gpgsign", "false"),
        ("user.name", "t"),
        ("user.email", "t@t"),
        ("core.hooksPath", "/dev/null"),
    ]:
        subprocess.run(["git", "config", "--local", k, v], cwd=path, check=True)


def commit_all(repo: Path, message: str = "fixture") -> str:
    """Stage everything and create a commit; returns the resulting SHA."""
    env = git_env()
    subprocess.run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", message],
        cwd=repo,
        env=env,
        check=True,
    )
    sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return sha.stdout.strip()


def copy_script_to(script_name: str, dest_dir: Path) -> Path:
    """Copy a hook script into ``dest_dir``, preserving the executable bit."""
    src = HOOKS_DIR / script_name
    if not src.exists():
        raise FileNotFoundError(f"Could not find {script_name} in {HOOKS_DIR}")
    dest = dest_dir / script_name
    shutil.copy2(src, dest)
    dest.chmod(0o755)
    return dest
