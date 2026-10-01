#!/usr/bin/env python3
"""Crea un ISO USA con el bmgres.arc espanol (data3 del PAL) injertado in-place.
El fichero espanol es mas pequeno, asi que se rellena con ceros.
Mantiene main.dol y el FST intactos -> el recomp lo sigue aceptando como GZLE01 rev 0.
"""
import shutil, os

SRC = "/home/fransis/wind-waker-recomp/WindWaker-USA.iso"
DST = "/home/fransis/wind-waker-recomp/WindWaker-ES.iso"
ES = "/home/fransis/wind-waker-recomp/pal-data/files/res/Msg/data3/bmgres.arc"
OFFSET = 0x564A13D0          # localizado por firma
OLD_SIZE = 640672            # tamano que declara el FST para el fichero USA

es = open(ES, "rb").read()
print("espanol: %d bytes" % len(es))
assert es[:4] == b"RARC"
assert len(es) <= OLD_SIZE, "no cabe!"

if not os.path.exists(DST):
    print("copiando ISO...")
    shutil.copyfile(SRC, DST)

with open(DST, "r+b") as f:
    f.seek(OFFSET)
    f.write(es)
    f.write(b"\x00" * (OLD_SIZE - len(es)))
    f.flush()
print("parche aplicado en %s (offset 0x%X)" % (DST, OFFSET))
print("tamano final:", os.path.getsize(DST))
