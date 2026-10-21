"""Configuration isolation for local evaluation; not an OS security sandbox."""
import os
from pathlib import Path


def isolated_environment(run_dir, auth_names=()):
    root = Path(run_dir).resolve() / "isolated-profile"
    root.mkdir(parents=True, exist_ok=True)
    # Preserve runtime essentials and explicit provider credentials, never ambient
    # agent configuration, plugins, MCP endpoints or Python import overrides.
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "LANG", "LC_ALL",
               "SSL_CERT_FILE", "SSL_CERT_DIR"} | set(auth_names)
    env = {k: v for k,v in os.environ.items() if k.upper() in allowed}
    for key, sub in {"HOME":"home", "USERPROFILE":"home", "CODEX_HOME":"codex",
                     "XDG_CONFIG_HOME":"config", "XDG_DATA_HOME":"data", "XDG_CACHE_HOME":"cache",
                     "APPDATA":"appdata", "LOCALAPPDATA":"localappdata", "TEMP":"tmp", "TMP":"tmp"}.items():
        dest = root / sub
        dest.mkdir(exist_ok=True)
        env[key] = str(dest)
    env["PYTHONUTF8"] = "1"
    return env


def require_fresh(path):
    if path.exists() and any(path.iterdir()):
        raise ValueError(f"Evaluation workdir is not empty; use a new iteration: {path}")


def reject_ambient_ancestors(workdir):
    for parent in Path(workdir).resolve().parents:
        if any((parent / name).exists() for name in ("AGENTS.md", ".agents", ".claude", ".codex")):
            raise ValueError(f"Ambient agent configuration in ancestor {parent}; choose an isolated workspace")
