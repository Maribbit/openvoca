"""
OpenVoca Portable Bundle Script
================================
Assembles a self-contained portable archive that can be extracted and run
without any prior Python or Node.js installation.

Usage:
    cd <repo-root>
    uv run python scripts/bundle.py

Output:
    dist/openvoca-{version}-win-x64.zip  (or .tar.gz on macOS/Linux)

    Windows bundle:
        openvoca.bat    -- Double-click entry point
        start.py        -- Cross-platform Python launcher
        openvoca.json   -- Runtime config

    macOS / Linux bundle:
        run.sh          -- Entry point; clears quarantine on macOS
        start.py        -- Cross-platform Python launcher
        openvoca.json   -- Runtime config

Python isolation strategy
-------------------------
Rather than copying the dev venv (which hard-codes the CI runner's Python path
in the shim/symlink), we bundle the UV-managed CPython interpreter itself
together with a fresh site-packages extracted from
``uv sync --frozen --no-dev --no-install-project``.
start.py passes ``PYTHONPATH=site-packages`` to the uvicorn subprocess, so no
venv activation is needed.  The bundle is fully self-contained and portable
across machines regardless of where Python is installed.
"""

import compileall
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------
_PLATFORM_MAP = {
    ("Windows", "AMD64"): "win-x64",
    ("Windows", "x86_64"): "win-x64",
    ("Darwin", "arm64"): "macos-arm64",
    ("Darwin", "x86_64"): "macos-x64",
    ("Linux", "x86_64"): "linux-x64",
}
_SYSTEM = platform.system()
_MACHINE = platform.machine()
PLATFORM_TAG = _PLATFORM_MAP.get((_SYSTEM, _MACHINE), f"{_SYSTEM.lower()}-{_MACHINE}")
IS_WINDOWS = _SYSTEM == "Windows"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"
VERSION = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
BUILD_DIR = REPO_ROOT / "build" / "openvoca"
VENV_WORK_DIR = REPO_ROOT / "build" / "_prod_venv"  # temp workspace for prod venv
DIST_DIR = REPO_ROOT / "dist"
ARCHIVE_STEM = f"openvoca-{VERSION}-{PLATFORM_TAG}"

# Runtime packages that must be importable via the bundled Python + site-packages
_REQUIRED_IMPORTS = ["fastapi", "uvicorn", "spacy", "sqlmodel", "httpx", "edge_tts"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    print(f"  $ {' '.join(str(c) for c in cmd)}", flush=True)
    # On Windows, pnpm/uv are .cmd wrappers; shell=True lets the OS find them.
    result = subprocess.run(cmd, cwd=cwd, shell=IS_WINDOWS)
    if result.returncode != 0:
        print(f"ERROR: command failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(result.returncode)


def _build_prod_venv(work_dir: Path) -> Path:
    """Create a production-only venv in a temporary workspace."""
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)
    shutil.copy2(BACKEND / "pyproject.toml", work_dir / "pyproject.toml")
    shutil.copy2(BACKEND / "uv.lock", work_dir / "uv.lock")
    _run(
        ["uv", "sync", "--frozen", "--no-dev", "--no-install-project"],
        cwd=work_dir,
    )
    return work_dir / ".venv"


def _find_python_root() -> Path:
    """Return the root dir of the UV-managed Python 3.12 installation."""
    raw = (
        subprocess.check_output(
            ["uv", "python", "find", "3.12"],
            shell=IS_WINDOWS,
        )
        .decode()
        .strip()
        .strip('"')
    )
    exe = Path(raw)
    # Windows: <root>/python.exe  --  Unix: <root>/bin/python3
    return exe.parent if IS_WINDOWS else exe.parent.parent


def _get_site_packages(venv: Path) -> Path:
    """Return the site-packages directory inside a uv venv."""
    if IS_WINDOWS:
        return venv / "Lib" / "site-packages"
    lib = venv / "lib"
    for child in sorted(lib.iterdir()):
        if child.name.startswith("python"):
            return child / "site-packages"
    raise RuntimeError(f"No pythonX.Y directory found in {lib}")


def _verify_bundle(bundle_dir: Path) -> None:
    """Verify all required runtime packages are importable in the bundled Python."""
    if IS_WINDOWS:
        python = bundle_dir / "python" / "python.exe"
    else:
        python = bundle_dir / "python" / "bin" / "python3"
    site_pkgs = bundle_dir / "site-packages"
    if not python.exists():
        print(f"  ERROR: bundled Python not found at {python}", file=sys.stderr)
        sys.exit(1)
    print("  Verifying runtime imports in bundled Python ...")
    failed: list[str] = []
    for pkg in _REQUIRED_IMPORTS:
        r = subprocess.run(
            [str(python), "-c", f"import {pkg}"],
            capture_output=True,
            shell=IS_WINDOWS,
            env={**os.environ, "PYTHONPATH": str(site_pkgs)},
        )
        if r.returncode == 0:
            print(f"    OK {pkg}")
        else:
            print(f"    FAIL {pkg}")
            failed.append(pkg)
    if failed:
        print(
            f"\nERROR: {len(failed)} package(s) failed to import: {', '.join(failed)}",
            file=sys.stderr,
        )
        sys.exit(1)


def _copy_tree(
    src: Path, dst: Path, *, exclude_dirs: frozenset[str] = frozenset()
) -> None:
    """Recursive copy that skips specific directory names."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.is_dir():
            if item.name in exclude_dirs:
                continue
            _copy_tree(item, dst / item.name, exclude_dirs=exclude_dirs)
        else:
            shutil.copy2(item, dst / item.name)


# ---------------------------------------------------------------------------
# Scripts written into the bundle
# ---------------------------------------------------------------------------

_START_PY = r'''
"""
OpenVoca launcher (start.py)
============================
Spawns the uvicorn backend, waits for it to become ready, then opens the
browser.  Works on Windows, macOS, and Linux.

Windows:  double-click openvoca.bat
macOS:    bash run.sh
Linux:    bash run.sh   (or: ./run.sh)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
DATA_DIR = ROOT / "data"
MAX_WAIT_SECONDS = 45

if sys.platform == "win32":
    PYTHON = ROOT / "python" / "python.exe"
else:
    PYTHON = ROOT / "python" / "bin" / "python3"
SITE_PACKAGES = ROOT / "site-packages"


def _read_config() -> dict:
    cfg_path = ROOT / "openvoca.json"
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def _build_env(cfg: dict) -> dict:
    """Build the environment for the uvicorn child process.

    The data directory is a default, not an assignment: a deployment may point
    OPENVOCA_DATA_DIR outside the bundle so that replacing the bundle directory
    does not delete the database. PYTHONPATH and the version are forced,
    because the bundle cannot start without the first and would misreport
    updates without the second.
    """
    env = dict(os.environ)
    env.setdefault("OPENVOCA_DATA_DIR", str(DATA_DIR))
    env["OPENVOCA_VERSION"] = cfg.get("version", "")
    env["PYTHONPATH"] = str(SITE_PACKAGES)
    return env


def main() -> None:
    cfg = _read_config()
    host: str = cfg.get("host", "127.0.0.1")
    port: int = cfg.get("port", 18099)
    log_level: str = cfg.get("log_level", "warning")
    open_browser: bool = cfg.get("open_browser", True)
    health_url = f"http://{host}:{port}/api/health"

    env = _build_env(cfg)
    # Create whichever directory will actually be used, not just the bundled one.
    Path(env["OPENVOCA_DATA_DIR"]).mkdir(parents=True, exist_ok=True)

    print(f"Starting OpenVoca {cfg.get('version', '')} on http://{host}:{port} ...")
    proc = subprocess.Popen(
        [
            str(PYTHON), "-m", "uvicorn", "src.main:app",
            "--host", host, "--port", str(port),
            "--log-level", log_level,
        ],
        cwd=str(BACKEND),
        env=env,
    )

    print(f"Waiting for server to be ready (up to {MAX_WAIT_SECONDS}s) ...", flush=True)
    ready = False
    for i in range(MAX_WAIT_SECONDS):
        time.sleep(1)
        if proc.poll() is not None:
            print("ERROR: Backend exited unexpectedly.", file=sys.stderr)
            sys.exit(1)
        try:
            with urllib.request.urlopen(health_url, timeout=1) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            pass
        if (i + 1) % 5 == 0:
            print(f"  Still waiting ... ({i + 1}s)", flush=True)

    if not ready:
        print("ERROR: Server did not become ready in time.", file=sys.stderr)
        proc.terminate()
        sys.exit(1)

    url = f"http://{host}:{port}"
    print(f"OpenVoca is ready at {url}")
    if open_browser:
        webbrowser.open(url)

    print("Press Ctrl+C or close this window to stop.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
    print("OpenVoca stopped.")


if __name__ == "__main__":
    main()
'''.lstrip("\n")

_OPENVOCA_BAT = (
    "@echo off\r\n"
    "title OpenVoca\r\n"
    'cd /d "%~dp0"\r\n'
    '"%~dp0python\\python.exe" "%~dp0start.py"\r\n'
    "if %errorlevel% neq 0 pause\r\n"
)

_RUN_SH = """\
#!/usr/bin/env bash
# OpenVoca launcher for macOS / Linux
# Usage:  bash run.sh
#
# On macOS, downloaded files are quarantined by Gatekeeper.
# This script removes the quarantine flag automatically, then launches OpenVoca.

set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

# Remove macOS quarantine attribute (no-op on Linux)
if command -v xattr >/dev/null 2>&1; then
    xattr -dr com.apple.quarantine "$DIR" 2>/dev/null || true
fi

exec "$DIR/python/bin/python3" "$DIR/start.py"
"""


# ---------------------------------------------------------------------------
# User-facing README written into the bundle (loaded from scripts/templates/)
# ---------------------------------------------------------------------------

_TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def _load_readme(is_windows: bool, locale: str = "en") -> str:
    """Read a README template and substitute the {version} placeholder."""
    platform_name = "Windows" if is_windows else "Unix"
    suffix = ".zh-CN.txt" if locale == "zh-CN" else ".txt"
    path = _TEMPLATES_DIR / f"README.{platform_name}{suffix}"
    return path.read_text(encoding="utf-8").replace("{version}", VERSION)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"\n=== OpenVoca Bundle Script  v{VERSION}  ({PLATFORM_TAG}) ===\n")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # Clean previous build
    if BUILD_DIR.exists():
        print("Cleaning previous build ...")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True)

    # ------------------------------------------------------------------ #
    # 1. Build frontend
    # ------------------------------------------------------------------ #
    print("\n[1/7] Building frontend ...")
    if not (FRONTEND / "node_modules").exists():
        _run(["pnpm", "install", "--frozen-lockfile"], cwd=FRONTEND)
    _run(["pnpm", "run", "build"], cwd=FRONTEND)

    # ------------------------------------------------------------------ #
    # 2. Build production-only venv (no dev deps, via uv lock-file)
    # ------------------------------------------------------------------ #
    print("\n[2/7] Building production venv (no dev deps) ...")
    print("  Using uv lock-file resolution -- no manual package filtering needed.")
    python_root = _find_python_root()
    print(f"  UV Python root: {python_root}")
    prod_venv = _build_prod_venv(VENV_WORK_DIR)

    # ------------------------------------------------------------------ #
    # 3. Sync host dev venv (needed so tests pass on the host machine)
    # ------------------------------------------------------------------ #
    print("\n[3/7] Syncing host dev venv ...")
    _run(["uv", "sync", "--frozen"], cwd=BACKEND)

    # ------------------------------------------------------------------ #
    # 4. Pre-compile Python source to bytecode
    # ------------------------------------------------------------------ #
    print("\n[4/7] Compiling Python source ...")
    compileall.compile_dir(str(BACKEND / "src"), force=True, quiet=1)

    # ------------------------------------------------------------------ #
    # 5. Assemble directory tree
    # ------------------------------------------------------------------ #
    print("\n[5/7] Assembling directory structure ...")

    # backend/src  (with __pycache__ pre-populated by step 4)
    print("  Copying backend source ...")
    _copy_tree(
        BACKEND / "src",
        BUILD_DIR / "backend" / "src",
        exclude_dirs=frozenset({".ruff_cache", ".pytest_cache", "node_modules"}),
    )

    # backend/data  (dictionary.db)
    (BUILD_DIR / "backend" / "data").mkdir(parents=True, exist_ok=True)
    dict_db = BACKEND / "data" / "dictionary.db"
    if dict_db.exists():
        shutil.copy2(dict_db, BUILD_DIR / "backend" / "data" / "dictionary.db")
    else:
        print("  [warn] dictionary.db not found; skipping.")

    # backend/assets
    if (BACKEND / "assets").exists():
        shutil.copytree(BACKEND / "assets", BUILD_DIR / "backend" / "assets")

    # Python interpreter (UV-managed, self-contained, no venv shims)
    print("  Copying Python interpreter ...")
    shutil.copytree(python_root, BUILD_DIR / "python", symlinks=True)

    # site-packages (runtime deps extracted from prod venv -- no activation needed)
    print("  Copying site-packages ...")
    site_pkgs_src = _get_site_packages(prod_venv)
    shutil.copytree(site_pkgs_src, BUILD_DIR / "site-packages")

    # frontend/dist
    print("  Copying frontend dist ...")
    shutil.copytree(FRONTEND / "dist", BUILD_DIR / "frontend" / "dist")

    # data/  (empty; created at runtime by start.py)
    (BUILD_DIR / "data").mkdir()

    # ------------------------------------------------------------------ #
    # 6. Write config + launcher scripts
    # ------------------------------------------------------------------ #
    print("\n[6/7] Writing openvoca.json + launcher scripts ...")
    config: dict = {
        "version": VERSION,
        "port": 18099,
        "host": "127.0.0.1",
        "open_browser": True,
        "log_level": "warning",
    }
    (BUILD_DIR / "openvoca.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    (BUILD_DIR / "start.py").write_text(_START_PY, encoding="utf-8")
    print("  Wrote start.py (cross-platform Python launcher)")

    if IS_WINDOWS:
        (BUILD_DIR / "openvoca.bat").write_text(_OPENVOCA_BAT, encoding="utf-8")
        print("  Wrote openvoca.bat")
    else:
        run_sh_path = BUILD_DIR / "run.sh"
        run_sh_path.write_text(_RUN_SH, encoding="utf-8")
        run_sh_path.chmod(0o755)
        print("  Wrote run.sh")

    readme_txt = _load_readme(IS_WINDOWS, "en")
    (BUILD_DIR / "README.txt").write_text(readme_txt, encoding="utf-8")
    print("  Wrote README.txt")

    readme_zh = _load_readme(IS_WINDOWS, "zh-CN")
    (BUILD_DIR / "README.zh-CN.txt").write_text(readme_zh, encoding="utf-8")
    print("  Wrote README.zh-CN.txt")

    # Verify bundled imports (fail-fast before archive)
    print()
    _verify_bundle(BUILD_DIR)

    # ------------------------------------------------------------------ #
    # 7. Create archive (.zip on Windows, .tar.gz on Unix)
    # ------------------------------------------------------------------ #
    if IS_WINDOWS:
        archive_name = f"{ARCHIVE_STEM}.zip"
        archive_path = DIST_DIR / archive_name
        print(f"\n[7/7] Creating {archive_name} ...")
        if archive_path.exists():
            archive_path.unlink()
        file_count = 0
        with zipfile.ZipFile(
            archive_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6
        ) as zf:
            for f in BUILD_DIR.rglob("*"):
                if f.is_file():
                    arc_name = Path("openvoca") / f.relative_to(BUILD_DIR)
                    zf.write(f, arc_name)
                    file_count += 1
    else:
        archive_name = f"{ARCHIVE_STEM}.tar.gz"
        archive_path = DIST_DIR / archive_name
        print(f"\n[7/7] Creating {archive_name} ...")
        if archive_path.exists():
            archive_path.unlink()
        file_count = 0
        with tarfile.open(archive_path, "w:gz", compresslevel=6) as tf:
            for f in BUILD_DIR.rglob("*"):
                if f.is_file():
                    arc_name = str(Path("openvoca") / f.relative_to(BUILD_DIR))
                    tf.add(f, arcname=arc_name)
                    file_count += 1

    mb = archive_path.stat().st_size / 1_048_576
    print(f"\nDone: {archive_path}  ({mb:.1f} MB, {file_count:,} files)")
    entry_point = "openvoca.bat" if IS_WINDOWS else "bash run.sh"
    print(
        f"\nTo test: extract the archive, run {entry_point}, "
        "and wait for the browser to open.\n"
    )


if __name__ == "__main__":
    main()
