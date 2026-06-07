"""
Scanner recursiv de directoare care clasifică fișierele după conținut.

Ordinea de aplicare a analizoarelor (prioritate descrescătoare):
    BMP > ASCII > UNICODE > BINARY

BMP trebuie verificat primul deoarece un BMP poate fi recunoscut
și ca ASCII dacă conținut-ul e majoritar printabil.
"""

from pathlib import Path

from lab6.file_analyzer import (
    AsciiAnalyzer,
    BinaryAnalyzer,
    BmpAnalyzer,
    FileType,
    UnicodeAnalyzer,
)


class DirectoryScanner:
    """
    Parcurge recursiv un director și clasifică fiecare fișier după conținut.

    Exemplu:
        scanner = DirectoryScanner()
        results = scanner.scan("/home/user/documente")
        # {
        #     FileType.ASCII:   ["/home/user/documente/readme.txt"],
        #     FileType.BMP:     ["/home/user/documente/imagine.bmp"],
        #     FileType.BINARY:  ["/home/user/documente/data.bin"],
        #     FileType.UNICODE: [],
        #     FileType.UNKNOWN: [],
        # }
    """

    # Analizoarele în ordinea priorităților — BMP primul, BINARY ultimul
    _ANALYZERS = [
        BmpAnalyzer(),
        AsciiAnalyzer(),
        UnicodeAnalyzer(),
        BinaryAnalyzer(),
    ]

    def scan(self, directory: str) -> dict[FileType, list[str]]:
        """
        Parcurge recursiv directorul și returnează un dict {FileType: [căi absolute]}.

        - Sare peste directoare și fișiere inaccesibile (PermissionError etc.)
        - Toate căile din rezultat sunt absolute.
        - Toate cheile din FileType sunt prezente (liste goale dacă nu există).
        """
        result: dict[FileType, list[str]] = {ft: [] for ft in FileType}
        root = Path(directory)

        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                content = path.read_bytes()
                file_type = self._classify(content)
            except Exception:
                # Fișier inaccesibil sau eroare de citire → UNKNOWN
                file_type = FileType.UNKNOWN

            result[file_type].append(str(path.resolve()))

        return result

    # ── Privat ────────────────────────────────────────────────────────────────

    def _classify(self, content: bytes) -> FileType:
        """
        Aplică analizoarele în ordine și returnează primul tip recunoscut.
        Dacă niciun analyzer nu recunoaște conținutul → UNKNOWN.
        """
        for analyzer in self._ANALYZERS:
            ft = analyzer.analyze(content)
            if ft != FileType.UNKNOWN:
                return ft
        return FileType.UNKNOWN
