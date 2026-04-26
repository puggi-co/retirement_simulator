import os
import re
from pathlib import Path

# Root directory of your project
PROJECT_ROOT = Path("c:/Dev/retirement_simulator")

# Patterns to detect
TYPE_HINT_ISSUES = [
    (r"\blist\b(?!

\[)", "🔧 Suggest: list → list[Type]"),
    (r"\bdict\b(?!

\[)", "🔧 Suggest: dict → dict[KeyType, ValueType]"),
    (r"\bCallable\b(?!

\[)", "🔧 Suggest: Callable → Callable[[ArgType], ReturnType]"),
]

UNUSED_IMPORT_PATTERN = re.compile(r"^from typing import (.+)$")

def scan_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    suggestions = []

    for i, line in enumerate(lines):
        for pattern, message in TYPE_HINT_ISSUES:
            if re.search(pattern, line):
                suggestions.append((i + 1, line.strip(), message))

        match = UNUSED_IMPORT_PATTERN.match(line)
        if match:
            imported = match.group(1).split(",")
            for item in imported:
                item = item.strip()
                if item and not any(item in l for l in lines[i+1:]):
                    suggestions.append((i + 1, line.strip(), f"🧹 Unused import: {item}"))

    return suggestions

def scan_project(root: Path):
    for py_file in root.rglob("*.py"):
        suggestions = scan_file(py_file)
        if suggestions:
            print(f"\n📄 {py_file.relative_to(root)}")
            for line_num, line_text, msg in suggestions:
                print(f"  Line {line_num}: {msg}\n    → {line_text}")

if __name__ == "__main__":
    scan_project(PROJECT_ROOT)
