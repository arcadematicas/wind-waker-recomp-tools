#!/usr/bin/env python3
"""Localiza un fichero dentro de un ISO de GameCube buscando su firma."""
import sys, os

iso_path = sys.argv[1]
needle_file = sys.argv[2]
needle = open(needle_file, "rb").read(64)

size = os.path.getsize(iso_path)
print("ISO: %s (%d bytes)" % (iso_path, size))
print("buscando firma de %d bytes: %s" % (len(needle), needle[:16].hex()))

found = []
CH = 8 * 1024 * 1024
with open(iso_path, "rb") as f:
    off = 0
    prev = b""
    while True:
        buf = f.read(CH)
        if not buf:
            break
        data = prev + buf
        base = off - len(prev)
        start = 0
        while True:
            i = data.find(needle, start)
            if i < 0:
                break
            found.append(base + i)
            start = i + 1
        prev = data[-len(needle):]
        off += len(buf)

print("coincidencias: %d" % len(found))
for o in found:
    # leer el tamano declarado por el RARC (offset 4, big-endian)
    import struct
    with open(iso_path, "rb") as f:
        f.seek(o)
        hdr = f.read(16)
    sz = struct.unpack_from(">I", hdr, 4)[0] if hdr[:4] == b"RARC" else None
    print("  offset=0x%08X  magic=%s  size_del_RARC=%s" % (o, hdr[:4], sz))
