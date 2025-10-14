#!/usr/bin/env python3
# root_reader.py y --skip .venv .git .idea
# Reads a folder's structure and saves a out_dir_strucuture.txt (tree-style) with counts and sizes.
# Usage: python rootreader.py . --skip .venv .git .idea __pycache__

import os
import sys
import argparse
import datetime
from typing import List, Tuple

def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.2f} {units[i]}"

def safe_listdir(path: str) -> List[os.DirEntry]:
    try:
        with os.scandir(path) as it:
            return sorted(list(it), key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.lower()))
    except PermissionError:
        return []
    except FileNotFoundError:
        return []

def build_tree(root: str, skip_dirs: List[str]) -> Tuple[List[str], int, int, int]:
    """
    Returns (lines, file_count, dir_count, total_bytes)
    """
    lines: List[str] = []
    file_count = 0
    dir_count = 0
    total_bytes = 0
    skip_set = {s.lower() for s in skip_dirs}

    def rec(path: str, prefix: str):
        nonlocal file_count, dir_count, total_bytes
        entries = safe_listdir(path)
        last_index = len(entries) - 1

        for idx, entry in enumerate(entries):
            connector = "└── " if idx == last_index else "├── "
            next_prefix = prefix + ("    " if idx == last_index else "│   ")

            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except PermissionError:
                is_dir = False

            name = entry.name
            display = name

            if is_dir:
                if name.lower() in skip_set:
                    lines.append(prefix + connector + display + "/ [skipped]")
                    continue
                dir_count += 1
                lines.append(prefix + connector + display + "/")
                rec(os.path.join(path, name), next_prefix)
            else:
                try:
                    size = entry.stat(follow_symlinks=False).st_size
                except (PermissionError, FileNotFoundError, OSError):
                    size = 0
                total_bytes += size
                file_count += 1
                lines.append(prefix + connector + f"{display}  ({human_bytes(size)})")

    # Root header
    abs_root = os.path.abspath(root)
    root_label = os.path.basename(abs_root.rstrip(os.sep)) or abs_root
    lines.append(f"{root_label}/")
    rec(abs_root, "")

    return lines, file_count, dir_count, total_bytes

def main():
    parser = argparse.ArgumentParser(
        description="Read a folder structure and save a tree-style out_dir_strucuture.txt."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Root directory to scan (default: current directory)."
    )
    parser.add_argument(
        "-o", "--output",
        default="out_dir_strucuture.txt",
        help="Output file path (default: out_dir_strucuture.txt)"
    )
    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Directory names to skip (case-insensitive, e.g. --skip node_modules .git)"
    )
    args = parser.parse_args()

    root = args.path
    if not os.path.exists(root):
        print(f"Error: path not found: {root}", file=sys.stderr)
        sys.exit(1)

    lines, file_count, dir_count, total_bytes = build_tree(root, args.skip)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = [
        f"# Folder Structure Log",
        f"Scanned: {os.path.abspath(root)}",
        f"Date:    {timestamp}",
        f"Python:  {sys.version.split()[0]}",
        f"Skipped: {', '.join(args.skip) if args.skip else 'None'}",
        "",
    ]
    footer = [
        "",
        f"Summary: {dir_count} director{'y' if dir_count==1 else 'ies'}, "
        f"{file_count} file{'s' if file_count!=1 else ''}, "
        f"total size {human_bytes(total_bytes)}",
    ]

    out_path = args.output
    try:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(header + lines + footer) + "\n")
    except OSError as e:
        print(f"Error writing to {out_path}: {e}", file=sys.stderr)
        sys.exit(2)

    print(f"Results: {out_path}")

if __name__ == "__main__":
    main()
