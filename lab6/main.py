"""
Entry point CLI pentru identificatorul de tipuri fișiere.

Utilizare:
    uv run python -m lab6.main /calea/directorului
"""

import sys

from lab6.directory_scanner import DirectoryScanner
from lab6.file_analyzer import FileType


def main() -> None:
    if len(sys.argv) < 2:
        print("Utilizare: python -m lab6.main <director>", file=sys.stderr)
        sys.exit(1)

    directory = sys.argv[1]
    scanner = DirectoryScanner()

    try:
        results = scanner.scan(directory)
    except FileNotFoundError:
        print(f"Eroare: directorul '{directory}' nu există.", file=sys.stderr)
        sys.exit(1)

    print(f"\nRezultate pentru directorul: {directory}\n")

    # Afișăm doar tipurile cu cel puțin un fișier
    found_any = False
    for file_type in FileType:
        paths = results.get(file_type, [])
        if not paths:
            continue
        found_any = True
        label = file_type.name
        count = len(paths)
        print(f"=== {label} ({count} {'fișier' if count == 1 else 'fișiere'}) ===")
        for p in sorted(paths):
            print(f"  {p}")
        print()

    if not found_any:
        print("Niciun fișier găsit.")


if __name__ == "__main__":
    main()
