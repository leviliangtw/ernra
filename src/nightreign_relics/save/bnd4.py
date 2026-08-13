# Adapted from alfizari/Elden-Ring-Nightreign-Save-Editor (MIT License).
# See /THIRD_PARTY_NOTICES for the full license text.
"""Decrypt-only BND4 container parsing for PC/Steam Nightreign `.sl2` saves.

Only the read path is ported: this tool never repacks/re-encrypts a save.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

DS2_KEY = b"\x18\xf6\x32\x66\x05\xbd\x17\x8a\x55\x24\x52\x3a\xc0\xa0\xc6\x09"

BND4_MAGIC = b"BND4"
BND4_ENTRY_MAGIC = b"\x40\x00\x00\x00\xff\xff\xff\xff"

BND4_HEADER_LEN = 64
BND4_ENTRY_HEADER_LEN = 32

IV_SIZE = 16


class Bnd4FormatError(ValueError):
    """Raised when the save file doesn't look like a valid BND4 container."""


@dataclass(frozen=True)
class Bnd4Entry:
    index: int
    size: int
    data_offset: int
    encrypted: bytes
    """Raw bytes for this entry: 16-byte IV followed by the AES-CBC ciphertext."""

    @property
    def filename(self) -> str:
        return f"USERDATA_{self.index}"

    @property
    def iv(self) -> bytes:
        return self.encrypted[:IV_SIZE]

    @property
    def payload(self) -> bytes:
        return self.encrypted[IV_SIZE:]


def parse_bnd4_entries(raw: bytes) -> list[Bnd4Entry]:
    """Parse a raw `.sl2` file's BND4 container into its (still-encrypted) entries."""
    if raw[:4] != BND4_MAGIC:
        raise Bnd4FormatError(
            f"Not a BND4 container: expected magic {BND4_MAGIC!r}, got {raw[:4]!r}"
        )

    entry_count = struct.unpack_from("<i", raw, 12)[0]
    entries: list[Bnd4Entry] = []
    for i in range(entry_count):
        pos = BND4_HEADER_LEN + BND4_ENTRY_HEADER_LEN * i
        magic = raw[pos : pos + 8]
        if magic != BND4_ENTRY_MAGIC:
            raise Bnd4FormatError(
                f"BND4 entry magic mismatch at index {i}: "
                f"expected {BND4_ENTRY_MAGIC.hex()}, got {magic.hex()}"
            )
        size, _unused, data_offset, _name_offset, _footer_length = struct.unpack_from(
            "<i i i i i", raw, pos + 8
        )
        if size <= 0 or data_offset <= 0 or data_offset + size > len(raw):
            raise Bnd4FormatError(
                f"BND4 entry {i} has invalid size/bounds: "
                f"offset={data_offset}, size={size}, total_len={len(raw)}"
            )
        entries.append(
            Bnd4Entry(
                index=i,
                size=size,
                data_offset=data_offset,
                encrypted=bytes(raw[data_offset : data_offset + size]),
            )
        )
    return entries


def decrypt_entry(entry: Bnd4Entry) -> bytes:
    """AES-CBC decrypt a single BND4 entry's payload using the save's fixed key/IV."""
    cipher = Cipher(algorithms.AES(DS2_KEY), modes.CBC(entry.iv))
    decryptor = cipher.decryptor()
    return decryptor.update(entry.payload) + decryptor.finalize()


def decrypt_save(save_path: Path) -> dict[str, bytes]:
    """Read and decrypt a `.sl2` save file.

    Returns a mapping of entry filename (e.g. "USERDATA_0", "USERDATA_10") to
    its decrypted bytes. Never writes to disk and never touches `save_path`
    other than opening it for reading.
    """
    raw = save_path.read_bytes()
    entries = parse_bnd4_entries(raw)
    return {entry.filename: decrypt_entry(entry) for entry in entries}
