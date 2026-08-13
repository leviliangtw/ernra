import struct

import pytest
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from nightreign_relics.save.bnd4 import (
    BND4_ENTRY_MAGIC,
    BND4_HEADER_LEN,
    BND4_ENTRY_HEADER_LEN,
    BND4_MAGIC,
    DS2_KEY,
    Bnd4FormatError,
    decrypt_save,
    parse_bnd4_entries,
)


def _encrypt(plaintext: bytes, iv: bytes) -> bytes:
    encryptor = Cipher(algorithms.AES(DS2_KEY), modes.CBC(iv)).encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()


def _build_bnd4(entries_plaintext: dict[int, bytes]) -> bytes:
    entry_count = len(entries_plaintext)
    data_offset = BND4_HEADER_LEN + BND4_ENTRY_HEADER_LEN * entry_count

    header = bytearray(BND4_HEADER_LEN)
    header[0:4] = BND4_MAGIC
    struct.pack_into("<i", header, 12, entry_count)

    entry_headers = bytearray()
    payloads = bytearray()
    cursor = data_offset
    for index, plaintext in sorted(entries_plaintext.items()):
        iv = bytes([index + 1]) * 16
        payload = iv + _encrypt(plaintext, iv)
        entry_headers += BND4_ENTRY_MAGIC
        entry_headers += struct.pack("<iiiii", len(payload), 0, cursor, 0, 0)
        entry_headers += b"\x00" * (BND4_ENTRY_HEADER_LEN - 8 - 20)
        payloads += payload
        cursor += len(payload)

    return bytes(header) + bytes(entry_headers) + bytes(payloads)


def test_parse_bnd4_entries_recovers_layout():
    plaintext = b"hello relic data" * 2  # 32 bytes, AES block-aligned
    raw = _build_bnd4({0: plaintext})
    entries = parse_bnd4_entries(raw)
    assert len(entries) == 1
    assert entries[0].filename == "USERDATA_0"


def test_parse_bnd4_entries_rejects_bad_magic():
    with pytest.raises(Bnd4FormatError):
        parse_bnd4_entries(b"NOTB" + b"\x00" * 60)


def test_decrypt_save_recovers_exact_plaintext(tmp_path):
    plaintext0 = b"hello relic data" * 2  # 32 bytes, AES block-aligned
    plaintext1 = b"B" * 32
    raw = _build_bnd4({0: plaintext0, 1: plaintext1})

    save_path = tmp_path / "NR0000.sl2"
    save_path.write_bytes(raw)

    decrypted = decrypt_save(save_path)

    assert decrypted["USERDATA_0"] == plaintext0
    assert decrypted["USERDATA_1"] == plaintext1
