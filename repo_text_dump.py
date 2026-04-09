#!/usr/bin/env python3
"""
repo_text_dump.py  (Enhanced Version)

✅ Color Output (built‑in ANSI colors)
✅ built‑in Progress Bar (no dependencies)
✅ Multi-threaded scanning (ThreadPoolExecutor)
✅ Excludes: repo_dump.txt, poetry.lock, repo_text_dump.py
"""

from __future__ import annotations
import argparse
import os
import sys
import fnmatch
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List, Set

# ------------------------------------------------------------------------------
# COLOR CONSTANTS
# ------------------------------------------------------------------------------
class Color:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"


# ------------------------------------------------------------------------------
# DEFAULT EXCLUSIONS (UPDATED)
# ------------------------------------------------------------------------------
DEFAULT_EXCLUDE_DIRS = {
    '.git', 'node_modules', 'venv', '.venv', '__pycache__',
    '.mypy_cache', '.pytest_cache', 'dist', 'build',
    '.idea', '.vscode', '.tox', '.eggs'
}

DEFAULT_EXCLUDE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp',
    '.ico', '.pdf', '.zip', '.gz', '.tar', '.xz', '.7z', '.rar',
    '.exe', '.dll', '.so', '.dylib', '.class', '.jar', '.wasm',
    '.mp3', '.wav', '.ogg', '.flac', '.mp4', '.mkv', '.mov', '.avi',
    '.ttf', '.otf', '.woff', '.woff2', '.eot'
}

DEFAULT_EXCLUDE_NAMES = {
    'package-lock.json',
    'yarn.lock',

    # ✅ Your requested exclusions
    'poetry.lock',
    'repo_dump.txt',
    'repo_text_dump.py',
}

DEFAULT_EXCLUDE_GLOBS = {
    '*.min.js', '*.bin', '*.lockb'
}


# ------------------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------------------
def to_set(csv: str | None, *, transform=lambda s: s) -> Set[str]:
    if not csv:
        return set()
    csv = csv.strip()
    if csv == "":
        return set()
    return {transform(s.strip()) for s in csv.split(',') if s.strip()}


def normalize_exts(exts: Iterable[str]) -> set[str]:
    out = set()
    for e in exts:
        e = e.strip()
        if not e:
            continue
        if not e.startswith('.'):
            e = "." + e
        out.add(e.lower())
    return out


def is_probably_binary(path: str, chunk_size: int = 2048) -> bool:
    """Detect if file is likely binary."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(chunk_size)
            if b"\x00" in chunk:
                return True
            try:
                chunk.decode("utf-8")
            except UnicodeDecodeError:
                return True
    except Exception:
        return True
    return False


def should_exclude_file(dirpath: str, filename: str,
                        exclude_exts: Set[str],
                        exclude_names: Set[str],
                        exclude_globs: Set[str]) -> bool:

    ext = os.path.splitext(filename)[1].lower()

    if filename in exclude_names:
        return True
    if ext and ext in exclude_exts:
        return True

    full = os.path.join(dirpath, filename)
    for pattern in exclude_globs:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(full, pattern):
            return True

    return False


# ------------------------------------------------------------------------------
# PROGRESS BAR (BUILT-IN)
# ------------------------------------------------------------------------------
def progress_bar(current: int, total: int, width: int = 40):
    percent = current / total
    filled = int(width * percent)
    bar = "=" * filled + "-" * (width - filled)
    sys.stderr.write(f"\r{Color.CYAN}[{bar}] {int(percent*100)}%{Color.RESET}")
    sys.stderr.flush()


# ------------------------------------------------------------------------------
# FILE PROCESSING WORKER (runs in threads)
# ------------------------------------------------------------------------------
def process_file(task):
    dirpath, fname, output_abspath, max_bytes = task

    fpath = os.path.join(dirpath, fname)

    if output_abspath and os.path.abspath(fpath) == output_abspath:
        return None

    if is_probably_binary(fpath):
        return None

    try:
        if max_bytes >= 0:
            with open(fpath, "rb") as f:
                data = f.read(max_bytes + 1)
            truncated = len(data) > max_bytes
            if truncated:
                data = data[:max_bytes]
        else:
            with open(fpath, "rb") as f:
                data = f.read()
            truncated = False

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1", errors="replace")

        return (dirpath, fname, text, truncated)

    except Exception:
        return None


# ------------------------------------------------------------------------------
# MAIN DUMP FUNCTION (MULTI-THREADED)
# ------------------------------------------------------------------------------
def dump_repo(root, output_path, exclude_dirs, exclude_exts, exclude_names,
              exclude_globs, max_bytes, follow_symlinks):

    to_stdout = output_path in (None, "-", "")
    out = sys.stdout if to_stdout else open(output_path, "w", encoding="utf-8")

    output_abspath = None
    if not to_stdout:
        output_abspath = os.path.abspath(output_path)

    # Collect file list (first pass)
    file_tasks = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fname in sorted(filenames):
            if should_exclude_file(dirpath, fname,
                                   exclude_exts=exclude_exts,
                                   exclude_names=exclude_names,
                                   exclude_globs=exclude_globs):
                continue
            file_tasks.append((dirpath, fname, output_abspath, max_bytes))

    total = len(file_tasks)
    if total == 0:
        print("No files to dump.")
        return 0

    processed = 0
    lock = threading.Lock()

    # Multi-threaded execution
    with ThreadPoolExecutor(max_workers=8) as exe:
        futures = {exe.submit(process_file, task): task for task in file_tasks}

        for fut in as_completed(futures):

            result = fut.result()
            with lock:
                processed += 1
                progress_bar(processed, total)

            if result is None:
                continue

            dirpath, fname, text, truncated = result

            print(f"\n{Color.GREEN}PATH: {dirpath}{Color.RESET}", file=out)
            print(f"{Color.BLUE}FILE: {fname}{Color.RESET}", file=out)
            out.write(text)
            if not text.endswith("\n"):
                out.write("\n")
            if truncated:
                out.write("[TRUNCATED]\n")
            out.write("\n" + "-"*80 + "\n")

    if out is not sys.stdout:
        out.close()

    sys.stderr.write("\n")
    return processed


# ------------------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="repo_dump.txt")
    parser.add_argument("--exclude-dir", default=",".join(sorted(DEFAULT_EXCLUDE_DIRS)))
    parser.add_argument("--exclude-ext", default=",".join(sorted(DEFAULT_EXCLUDE_EXTS)))
    parser.add_argument("--exclude-name", default=",".join(sorted(DEFAULT_EXCLUDE_NAMES)))
    parser.add_argument("--exclude-glob", default=",".join(sorted(DEFAULT_EXCLUDE_GLOBS)))
    parser.add_argument("--max-bytes", default=2_000_000, type=int)
    parser.add_argument("--follow-symlinks", action="store_true")
    args = parser.parse_args()

    exclude_dirs = to_set(args.exclude_dir)
    exclude_exts = normalize_exts(to_set(args.exclude_ext))
    exclude_names = to_set(args.exclude_name)
    exclude_globs = to_set(args.exclude_glob)

    files = dump_repo(
        root=args.root,
        output_path=args.output,
        exclude_dirs=exclude_dirs,
        exclude_exts=exclude_exts,
        exclude_names=exclude_names,
        exclude_globs=exclude_globs,
        max_bytes=args.max_bytes,
        follow_symlinks=args.follow_symlinks,
    )

    print(f"\nProcessed {files} files → {args.output}")


if __name__ == "__main__":
    main()