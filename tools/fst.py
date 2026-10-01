#!/usr/bin/env python3
"""Lista el FST de un ISO de GameCube y localiza ficheros por patron."""
import struct, sys

path = sys.argv[1]
pat = (sys.argv[2].lower() if len(sys.argv) > 2 else "bmgres")

with open(path, "rb") as f:
    head = f.read(0x440)
    fst_off = struct.unpack_from(">I", head, 0x424)[0]
    fst_size = struct.unpack_from(">I", head, 0x428)[0]
    f.seek(fst_off)
    fst = f.read(fst_size)

total = struct.unpack_from(">I", fst, 0x08)[0]  # la entrada 0 (dir raiz) guarda el total
print("gameID   : %s" % head[0:6].decode("ascii", "replace"))
print("fstOffset: 0x%X   fstSize: 0x%X   entradas: %d" % (fst_off, fst_size, total))
print()

def entry(i):
    tn = struct.unpack_from(">I", fst, i * 0xC)[0]
    nameoff = tn & 0xFFFFFF
    isdir = (tn >> 24) == 1
    end = fst.index(b"\x00", nameoff)
    name = fst[nameoff:end].decode("ascii", "replace")
    nxt = struct.unpack_from(">I", fst, i * 0xC + 8)[0]
    off = struct.unpack_from(">I", fst, i * 0xC + 4)[0]
    return name, isdir, off, nxt

out = []
def walk(start, end, prefix, depth=0):
    i = start
    while i < end:
        name, isdir, off, nxt = entry(i)
        if isdir:
            walk(i + 1, nxt, prefix + name + "/", depth + 1)
            i = nxt
        else:
            full = prefix + name
            if pat in full.lower():
                out.append((full, off, nxt))
            i += 1

walk(1, total, "")

for full, off, size in out:
    print("%-38s offset=0x%08X  size=%9d" % (full, off, size))
print()
print("coincidencias de '%s': %d" % (pat, len(out)))
