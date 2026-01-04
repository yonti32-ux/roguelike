from __future__ import annotations
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "RESUME_PACK.md"

KEY_FILES = [
    "main.py",
    "engine/game.py",
    "ui/screens.py",
]

def run(cmd: list[str]) -> str:
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        out = (p.stdout or "") + (("\n" + p.stderr) if p.stderr else "")
        return out.strip()
    except Exception as e:
        return f"(failed to run {' '.join(cmd)}): {e}"

def read_file(rel: str, limit: int = 4000) -> str:
    path = ROOT / rel
    if not path.exists():
        return f"(missing: {rel})"
    txt = path.read_text(encoding="utf-8", errors="replace")
    if len(txt) > limit:
        return txt[:limit] + "\n\n... (truncated)\n"
    return txt

def main() -> None:
    parts: list[str] = []
    parts.append("# RESUME PACK\n")

    parts.append("## Repo status\n")
    parts.append("```")
    parts.append(run(["git", "status"]))
    parts.append("```\n")

    parts.append("## Branches\n")
    parts.append("```")
    parts.append(run(["git", "branch", "-vv"]))
    parts.append("```\n")

    parts.append("## Recent commits\n")
    parts.append("```")
    parts.append(run(["git", "log", "--oneline", "--decorate", "-n", "30"]))
    parts.append("```\n")

    parts.append("## Quick tree (top level)\n")
    parts.append("```")
    try:
        top = sorted([p.name for p in ROOT.iterdir() if p.name not in {'.git', '.venv', '__pycache__'}])
        parts.append("\n".join(top))
    except Exception as e:
        parts.append(f"(failed to list repo): {e}")
    parts.append("```\n")

    parts.append("## TODO/FIXME scan (first 200 hits)\n")
    parts.append("```")
    rg = run(["rg", "-n", "TODO|FIXME|HACK|BUG|@todo", ".", "-S", "--no-heading", "--color", "never"])
    lines = rg.splitlines()
    parts.append("\n".join(lines[:200]) if lines else "(no hits or rg not installed)")
    parts.append("```\n")

    parts.append("## Key files\n")
    for rel in KEY_FILES:
        parts.append(f"### {rel}\n")
        parts.append("```")
        parts.append(read_file(rel))
        parts.append("```\n")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT}")

if __name__ == "__main__":
    main()
