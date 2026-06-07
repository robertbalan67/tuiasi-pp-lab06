"""
Analizatoare de tipuri fișiere prin conținut (nu extensie).

Ierarhie:
    FileAnalyzer (ABC)
    ├── AsciiAnalyzer   — text ASCII/UTF-8
    ├── UnicodeAnalyzer — text UTF-16 (cu octeți nuli)
    ├── BmpAnalyzer     — imagini BMP (magic bytes BM)
    └── BinaryAnalyzer  — binar generic (fallback)
"""

import struct
from abc import ABC, abstractmethod
from enum import Enum, auto


# ─── Enum tipuri ──────────────────────────────────────────────────────────────

class FileType(Enum):
    ASCII   = auto()
    UNICODE = auto()
    BINARY  = auto()
    BMP     = auto()
    UNKNOWN = auto()


# ─── Clasă abstractă de bază ──────────────────────────────────────────────────

class FileAnalyzer(ABC):
    """Interfață pentru toți analizatorii de fișiere."""

    @abstractmethod
    def analyze(self, content: bytes) -> FileType:
        """
        Analizează conținutul și returnează tipul detectat
        sau FileType.UNKNOWN dacă nu corespunde acestui analyzer.
        """
        ...


# ─── Implementări ─────────────────────────────────────────────────────────────

class AsciiAnalyzer(FileAnalyzer):
    """
    Detectează fișiere text ASCII / UTF-8.

    Criteriu: octeții din {9, 10, 13} ∪ {32..127} reprezintă ≥85% din conținut.
    Octeții de control ({0-8, 11, 12, 14-31}) și {128-255} reprezintă ≤15%.
    """

    # Setul octeților "text valid"
    _TEXT_BYTES: frozenset[int] = frozenset(range(32, 128)) | {9, 10, 13}

    def analyze(self, content: bytes) -> FileType:
        if not content:
            return FileType.UNKNOWN

        text_count = sum(1 for b in content if b in self._TEXT_BYTES)
        ratio = text_count / len(content)

        return FileType.ASCII if ratio >= 0.85 else FileType.UNKNOWN


class UnicodeAnalyzer(FileAnalyzer):
    """
    Detectează fișiere UTF-16.

    Criteriu: octetul 0x00 apare în ≥30% din conținut
    (UTF-16 LE are un byte nul pentru fiecare caracter ASCII).

    Exemplu: "Hello".encode("utf-16-le") = b'H\\x00e\\x00l\\x00l\\x00o\\x00'
    """

    def analyze(self, content: bytes) -> FileType:
        if not content:
            return FileType.UNKNOWN

        null_ratio = content.count(0x00) / len(content)
        return FileType.UNICODE if null_ratio >= 0.30 else FileType.UNKNOWN


class BmpAnalyzer(FileAnalyzer):
    """
    Detectează și parsează fișiere BMP.

    Criteriu: primii 2 octeți = 0x42 0x4D (ASCII 'BM').

    Header BMP (relevant):
        Offset  Size  Descriere
          0-1    2    Semnătură 'BM'
          2-5    4    Dimensiune fișier (uint32 LE)
          6-9    4    Rezervat
         10-13   4    Offset date pixel (uint32 LE)
         14-17   4    Dimensiune DIB header = 40 (uint32 LE)
         18-21   4    Lățime pixeli (int32 LE)
         22-25   4    Înălțime pixeli (int32 LE) — negativă = top-down
         26-27   2    Planuri culoare = 1 (uint16 LE)
         28-29   2    Biți per pixel (uint16 LE)
    """

    _MAGIC = b'BM'

    def analyze(self, content: bytes) -> FileType:
        if len(content) >= 2 and content[:2] == self._MAGIC:
            return FileType.BMP
        return FileType.UNKNOWN

    def get_bmp_info(self, content: bytes) -> dict[str, int]:
        """
        Parsează header-ul BMP și returnează dimensiunile și adâncimea de culoare.

        Returns:
            {'width': int, 'height': int, 'bits_per_pixel': int}

        Raises:
            ValueError: dacă conținutul e prea scurt sau nu e BMP valid.
        """
        if len(content) < 30:
            raise ValueError(f"Conținut prea scurt pentru header BMP ({len(content)} octeți)")
        if content[:2] != self._MAGIC:
            raise ValueError("Nu este un fișier BMP valid (magic bytes lipsă)")

        width  = struct.unpack_from('<i', content, 18)[0]
        height = struct.unpack_from('<i', content, 22)[0]
        bpp    = struct.unpack_from('<H', content, 28)[0]

        # Înălțimea negativă = bitmap top-down (valoarea absolută e înălțimea reală)
        return {
            'width':          width,
            'height':         abs(height),
            'bits_per_pixel': bpp,
        }


class BinaryAnalyzer(FileAnalyzer):
    """
    Fallback pentru fișiere binare generice.

    Returnează FileType.BINARY pentru orice conținut nevid care nu a fost
    recunoscut de niciun alt analyzer (BMP, ASCII, UNICODE).
    """

    def analyze(self, content: bytes) -> FileType:
        return FileType.BINARY if content else FileType.UNKNOWN
