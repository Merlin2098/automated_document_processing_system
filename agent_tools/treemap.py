#!/usr/bin/env python3
"""
Generate project tree map under agent/analysis/treemap.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import pathspec
except ImportError:
    print("Error: pathspec is not installed")
    print("Install with: pip install pathspec")
    sys.exit(1)

try:
    from agent_tools._repo_root import find_project_root
except ImportError:
    from _repo_root import find_project_root  # type: ignore


def load_gitignore(directory: Path) -> pathspec.PathSpec | None:
    gitignore_path = directory / ".gitignore"
    if not gitignore_path.exists():
        return None
    patterns = gitignore_path.read_text(encoding="utf-8").splitlines()
    patterns = [p for p in patterns if p.strip() and not p.startswith("#")]
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def generate_tree(
    directory: Path,
    *,
    prefix: str = "",
    excluded: set[str] | None = None,
    ignored_dirs: set[str] | None = None,
    gitignore_spec: pathspec.PathSpec | None = None,
    project_root: Path | None = None,
) -> list[str]:
    if excluded is None:
        excluded = set()
    if ignored_dirs is None:
        ignored_dirs = set()
    if project_root is None:
        project_root = directory

    try:
        items = sorted(directory.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        return []

    visible: list[Path] = []
    for path in items:
        name = path.name
        if name in excluded or name in ignored_dirs or name.endswith(".spec"):
            continue
        if gitignore_spec:
            rel_path = path.relative_to(project_root).as_posix()
            if gitignore_spec.match_file(rel_path):
                continue
            if path.is_dir() and gitignore_spec.match_file(rel_path + "/"):
                continue
        visible.append(path)

    output: list[str] = []
    for idx, path in enumerate(visible):
        is_last = idx == len(visible) - 1
        connector = "`-- " if is_last else "|-- "
        if path.is_dir():
            output.append(f"{prefix}{connector}{path.name}/")
            child_prefix = f"{prefix}{'    ' if is_last else '|   '}"
            output.extend(
                generate_tree(
                    path,
                    prefix=child_prefix,
                    excluded=excluded,
                    ignored_dirs=ignored_dirs,
                    gitignore_spec=gitignore_spec,
                    project_root=project_root,
                )
            )
        else:
            output.append(f"{prefix}{connector}{path.name}")
    return output


def write_treemap(project_root: Path, output_file: Path) -> None:
    current_script = Path(__file__).name
    excluded = {current_script}
    ignored_dirs = {".git"}
    gitignore_spec = load_gitignore(project_root)

    if gitignore_spec:
        print(".gitignore patterns loaded")
    else:
        print("Warning: .gitignore not found; processing all files")

    tree = generate_tree(
        project_root,
        excluded=excluded,
        ignored_dirs=ignored_dirs,
        gitignore_spec=gitignore_spec,
        project_root=project_root,
    )
    tree_output = "\n".join(tree)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    existed = output_file.exists()
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("## Project Structure\n\n```\n")
        f.write(tree_output)
        f.write("\n```\n\n")
        f.write("## Cache Artifacts\n\n")
        f.write("- path_cache.json: single runtime cache file\n")
        f.write("- Host-specific or suffixed cache files are not supported\n")
        f.write("- Any additional cache files should be considered accidental artifacts\n")

    if existed:
        print(f"Updated: {output_file}")
    else:
        print(f"Created: {output_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate project treemap markdown")
    parser.add_argument("--project-root", help="Optional project root override")
    parser.add_argument(
        "--output",
        help="Optional output path (default: agent/analysis/treemap.md under project root)",
    )
    args = parser.parse_args()

    root = Path(args.project_root).resolve() if args.project_root else find_project_root(Path(__file__).resolve().parent)
    output = Path(args.output).resolve() if args.output else (root / "agent" / "analysis" / "treemap.md")
    write_treemap(root, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
