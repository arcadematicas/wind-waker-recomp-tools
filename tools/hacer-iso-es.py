#!/usr/bin/env python3
"""Crea un ISO USA (GZLE01) con el texto/dialogo ESPANOL del disco PAL (GZLP01) injertado.

Uso:  hacer-iso-es.py <USA.iso> <PAL.iso> <salida.iso>

Como funciona:
  - El dialogo vive en res/Msg/bmgres.arc (RARC con color.bmc + zel_00.bmg), el MISMO
    fichero en las dos versiones y con la misma estructura interna.
  - El disco PAL trae los textos por idioma en res/Msg/data0..data4:
      data0=ingles  data1=aleman  data2=frances  data3=ESPANOL  data4=italiano
  - El bmgres.arc espanol (data3) pesa menos que el americano, asi que cabe en su hueco.
  - Se localiza el fichero USA dentro del ISO por su firma (primeros 64 bytes) y se
    sobrescribe in-place, rellenando el resto con ceros.
  - main.dol y el FST quedan INTACTOS -> el recomp lo sigue aceptando como GZLE01 rev 0.

Requiere: dolphin-tool en el PATH.
"""
import os, shutil, struct, subprocess, sys, tempfile

SMALLER_OK = True


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("fallo: %s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def extract_one(iso, member, dest_dir):
    """Extrae un unico fichero del ISO (dolphin-tool -s RUTA)."""
    run(["dolphin-tool", "extract", "-i", iso, "-o", dest_dir, "-s", member])
    # dolphin-tool deja el arbol bajo <dest>/files/...
    path = os.path.join(dest_dir, "files", member)
    if not os.path.isfile(path):
        sys.exit("no se extrajo %s de %s" % (member, iso))
    return path


def find_in_iso(iso, needle):
    """Devuelve los offsets donde aparece `needle` en el ISO."""
    size = 8 * 1024 * 1024
    hits, prev = [], b""
    with open(iso, "rb") as f:
        pos = 0
        while True:
            buf = f.read(size)
            if not buf:
                break
            data = prev + buf
            base = pos - len(prev)
            at = 0
            while True:
                i = data.find(needle, at)
                if i < 0:
                    break
                hits.append(base + i)
                at = i + 1
            prev = data[-len(needle):]
            pos += len(buf)
    return hits


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    usa, pal, out = sys.argv[1:4]
    for p in (usa, pal):
        if not os.path.isfile(p):
            sys.exit("no existe: %s" % p)

    tmp = tempfile.mkdtemp(prefix="wwes-")
    try:
        print("== extrayendo el bmgres.arc del USA y del PAL ==")
        us_path = extract_one(usa, "res/Msg/bmgres.arc", os.path.join(tmp, "usa"))
        es_path = extract_one(pal, "res/Msg/data3/bmgres.arc", os.path.join(tmp, "pal"))
        us = open(us_path, "rb").read()
        es = open(es_path, "rb").read()
        print("   USA: %d bytes   ESPANOL: %d bytes" % (len(us), len(es)))
        if us[:4] != b"RARC" or es[:4] != b"RARC":
            sys.exit("alguno de los dos no es un RARC")
        if len(es) > len(us):
            sys.exit("el espanol NO cabe en el hueco del USA (%d > %d)" % (len(es), len(us)))

        print("== localizando el bmgres.arc del USA dentro del ISO ==")
        hits = find_in_iso(usa, us[:64])
        if len(hits) != 1:
            sys.exit("esperaba 1 coincidencia, encontre %d" % len(hits))
        off = hits[0]
        print("   offset = 0x%08X (RARC de %d bytes)" % (off, len(us)))

        print("== escribiendo %s ==" % out)
        if not os.path.exists(out):
            shutil.copyfile(usa, out)
        with open(out, "r+b") as f:
            f.seek(off)
            f.write(es)
            f.write(b"\x00" * (len(us) - len(es)))
        print("   hecho (%d bytes)" % os.path.getsize(out))

        print("== comprobando el resultado ==")
        print(run(["dolphin-tool", "header", "-i", out]).strip())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
