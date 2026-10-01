#!/usr/bin/env python3
"""
windwaker_pal_text.py
=====================

Swap the in-game text of a PAL (GZLP01) The Wind Waker disc into a USA
(GZLE01) disc, producing a hybrid ISO that the Wind Waker recompiler still
accepts as an unmodified USA revision 0 disc.

Why this works
--------------
All the dialogue / text of the game lives in a single archive,
``res/Msg/bmgres.arc``, which is a GameCube RARC archive holding
``color.bmc`` and ``zel_00.bmg`` (the message bank, plain ASCII text).

The USA disc has exactly ONE copy of that archive, sitting in a gap of the
filesystem that is sized for the US text.  The PAL disc ships FIVE copies of
it, one per language, at ``res/Msg/data0..data4``::

    data0 = English     data1 = German     data2 = French
    data3 = SPANISH     data4 = Italian

If the RARC of the language you want is *smaller than or equal to* the US
one, it fits in the US gap.  We simply overwrite it in place and zero-fill
the remainder.  ``main.dol`` and the filesystem table (FST) are never
touched, so the disc keeps its USA game code / revision and the recompiler
keeps accepting it.

Languages that fit today: French, Spanish, Italian (and English itself).
German does NOT fit -- its RARC is larger than the US one, so it would need
a full ISO rebuild (moving files and rewriting the FST), which this tool
does not do.

Requirements: Python 3, standard library only.  No external dependencies.

Usage
-----
List the dialogue archives found in a disc::

    python3 windwaker_pal_text.py --list --disc WindWaker-USA.iso
    python3 windwaker_pal_text.py --list --disc "PAL/Legend of Zelda.iso"

Patch a USA disc with the text of another language::

    python3 windwaker_pal_text.py USA.iso PAL.iso OUT.iso --language es

Use ``--language {en,de,fr,es,it}`` (default: ``es``) or ``--index N`` to
pick the Nth PAL dialogue archive (0-based, in the order they are found on
the disc) when you do not trust the automatic language detection.
"""

import argparse
import os
import re
import shutil
import struct
import sys
import unicodedata

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RARC_MAGIC = b"RARC"
RARC_SIZE_OFFSET = 4              # u32 big-endian: total RARC size
RARC_HEADER_SIZE = 8

# Marker that identifies the message archive among every RARC on the disc.
# Internal entry names live in the string table at the start of the archive.
DIALOGUE_MARKER = b"zel_00.bmg"
DIALOGUE_MARKER_SEARCH = 16 * 1024

# Sanity limits used to discard false positives when scanning for "RARC".
MAX_RARC_SIZE = 512 * 1024 * 1024
MIN_RARC_SIZE = RARC_HEADER_SIZE

# How much of the archive we read when we want to show a text sample.
SAMPLE_READ = 2 * 1024 * 1024
# Longest phrase shown to the user.
SAMPLE_PHRASE_CHARS = 90
# How many phrases we feed to the language guesser.
DETECT_PHRASES = 400

# Scan chunk size for the --list pass (spec asks for 4-8 MB).
SCAN_CHUNK = 6 * 1024 * 1024

# Longest "word" that may follow/precede a keyword; run detection handles this.
ASCII_RUN_RE = re.compile(rb"[\x20-\x7e]{25,}")

LANGUAGES = ("en", "de", "fr", "es", "it")

LANGUAGE_NAMES = {
    "en": "English",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
}

# Lower-cased, space-padded stop-words used to guess the language of a sample.
LANGUAGE_WORDS = {
    "en": (" the ", " you ", " and ", " with ", " that "),
    "de": (" und ", " nicht ", " der ", " das ", " ist "),
    "fr": (" vous ", " pour ", " avec ", " dans ", " est "),
    "es": (" que ", " para ", " pero ", " los ", " las ", " una "),
    "it": (" sono ", " della ", " questo ", " nella ", " anche "),
}


# ---------------------------------------------------------------------------
# Low level helpers
# ---------------------------------------------------------------------------

def read_at(handle, offset, length):
    """Read exactly `length` bytes at `offset`, or as much as is available."""
    handle.seek(offset)
    return handle.read(length)


def u32be(data, offset):
    """Unpack a big-endian unsigned 32 bit integer, or None if out of range."""
    if offset + 4 > len(data):
        return None
    return struct.unpack_from(">I", data, offset)[0]


def strip_accents(text):
    """Fold accented Latin-1 letters onto their base ASCII letter.

    The Spanish / French / German strings keep their accents, so the ASCII
    keyword lists would not match without this.  The result is lower-case.
    """
    out = []
    for char in text:
        if "a" <= char <= "z" or char == " ":
            out.append(char)
            continue
        folded = unicodedata.normalize("NFD", char)
        stripped = "".join(c for c in folded if not unicodedata.combining(c))
        out.append(stripped.lower())
    return "".join(out)


def human_size(num):
    """Return a short human readable size, e.g. 640672 -> '625.6 KB'."""
    if num is None:
        return "?"
    if num < 1024:
        return "%d B" % num
    if num < 1024 * 1024:
        return "%.1f KB" % (num / 1024.0)
    return "%.1f MB" % (num / (1024.0 * 1024.0))


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

class Archive(object):
    """A RARC archive found inside an ISO."""

    def __init__(self, iso_path, offset, size, sample, language, score):
        self.iso_path = iso_path
        self.offset = offset
        self.size = size
        self.sample = sample      # short phrases shown to the user
        self.language = language  # guessed language code, or None
        self.score = score        # keyword hits behind the guess

    def __repr__(self):  # pragma: no cover - debug helper
        return "<Archive 0x%08X %d bytes lang=%s>" % (
            self.offset, self.size, self.language)


def scan_for_rarcs(iso_path, progress=False):
    """Return the offsets of every plausible RARC header in the ISO.

    The whole image is streamed in chunks; a candidate is kept only if the
    declared size is sane and the archive fits inside the image, which filters
    out the vast majority of accidental "RARC" matches inside other data.
    """
    iso_size = os.path.getsize(iso_path)
    needle = RARC_MAGIC
    overlap = len(needle) - 1
    hits = []

    # NOTE: two handles on purpose.  The scanner streams the image with
    # sequential reads while the validation step needs random access; using
    # the same handle for both would move the stream position and silently
    # skip chunks.
    with open(iso_path, "rb") as handle, open(iso_path, "rb") as prober:
        position = 0
        carry = b""
        carry_base = 0
        last_percent = -1
        while True:
            chunk = handle.read(SCAN_CHUNK)
            if not chunk:
                break
            buffer = carry + chunk
            base = carry_base
            at = 0
            while True:
                found = buffer.find(needle, at)
                if found < 0:
                    break
                absolute = base + found
                # Cheap filters first, then read the declared size.
                if 0 <= absolute <= iso_size - MIN_RARC_SIZE:
                    header = read_at(prober, absolute, 16)
                    declared = u32be(header, RARC_SIZE_OFFSET)
                    if (declared is not None
                            and MIN_RARC_SIZE <= declared <= MAX_RARC_SIZE
                            and absolute + declared <= iso_size):
                        hits.append((absolute, declared))
                at = found + 1
            # Keep the tail so a signature split across chunks is still found.
            carry = buffer[-overlap:] if overlap else b""
            carry_base = base + len(buffer) - len(carry)
            position += len(chunk)
            if progress and sys.stderr.isatty():
                percent = int(100.0 * min(position, iso_size) / iso_size)
                if percent != last_percent:
                    last_percent = percent
                    sys.stderr.write("\r  scanning... %3d%%" % percent)
                    sys.stderr.flush()

    if progress and sys.stderr.isatty():
        sys.stderr.write("\r" + " " * 30 + "\r")
        sys.stderr.flush()

    # A header can be reported twice if chunks overlapped; keep it unique.
    unique = []
    seen = set()
    for offset, declared in hits:
        if offset in seen:
            continue
        seen.add(offset)
        unique.append((offset, declared))
    unique.sort()
    return unique


def extract_text(iso_path, offset, size, read_limit=SAMPLE_READ, max_phrases=None):
    """Collect the readable ASCII phrases stored inside the archive.

    The message bank stores its strings as plain ASCII, so runs of printable
    characters give a usable preview of the language.  Entries belonging to the
    RARC string table (file names, container magic tags) are skipped: they are
    the same in every language and would only skew the detection.
    """
    read_len = min(size, read_limit)
    with open(iso_path, "rb") as handle:
        blob = read_at(handle, offset, read_len)
    if not blob:
        return []

    phrases = []
    for match in ASCII_RUN_RE.finditer(blob):
        text = match.group().decode("ascii", "replace").strip()
        if len(text) < 25:
            continue
        # Must look like a sentence fragment: a few spaces and real words.
        if text.count(" ") < 3:
            continue
        # Drop the RARC header / string table / binary tags.
        lowered = text.lower()
        if ".bmg" in lowered or ".bmc" in lowered or "mgcl" in lowered:
            continue
        phrases.append(text[:SAMPLE_PHRASE_CHARS])
        if max_phrases and len(phrases) >= max_phrases:
            break
    return phrases


def detect_language(text):
    """Guess a language code from a chunk of text.  Returns (code, score).

    Scoring is deliberately simple: count the most frequent function words of
    each language.  Accents are folded to their base letters so the same word
    list works for the localised ISO.
    """
    if not text:
        return None, 0
    haystack = " " + strip_accents(text.lower()) + " "
    best_code, best_score = None, 0
    for code in LANGUAGES:
        score = sum(haystack.count(word) for word in LANGUAGE_WORDS[code])
        if score > best_score:
            best_code, best_score = code, score
    if best_score == 0:
        return None, 0
    return best_code, best_score


def find_dialogue_archives(iso_path, progress=False):
    """Find the dialogue (message) RARC archives inside an ISO.

    A RARC is considered a dialogue archive when the entry name
    ``zel_00.bmg`` shows up in the string table at the beginning of the
    archive, which is where RARC keeps its internal file names.
    """
    archives = []

    with open(iso_path, "rb") as handle:
        for offset, declared in scan_for_rarcs(iso_path, progress=progress):
            head = read_at(handle, offset, min(DIALOGUE_MARKER_SEARCH, declared))
            if DIALOGUE_MARKER not in head:
                continue
            phrases = extract_text(iso_path, offset, declared,
                                   max_phrases=DETECT_PHRASES)
            language, score = detect_language(" ".join(phrases))
            archives.append(Archive(iso_path, offset, declared,
                                    phrases[:2], language, score))

    return archives


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def describe(archive, title):
    """Print one archive entry in a stable, human friendly format."""
    print("")
    print("  %s" % title)
    print("    ISO          : %s" % archive.iso_path)
    print("    offset       : 0x%08X (%d)" % (archive.offset, archive.offset))
    print("    RARC size    : %d bytes (%s)" % (archive.size,
                                                 human_size(archive.size)))
    if archive.language:
        print("    language     : %s (%s) - %d keyword hits"
              % (archive.language, LANGUAGE_NAMES[archive.language],
                 archive.score))
    else:
        print("    language     : unknown (no keyword hits)")
    if archive.sample:
        for index, phrase in enumerate(archive.sample):
            print("    sample %d     : \"%s\"" % (index + 1, phrase))
    else:
        print("    sample       : <no readable text found>")


def run_list(disc_path):
    """--list mode: report the dialogue archives of a disc.  Read only."""
    if not os.path.isfile(disc_path):
        sys.exit("error: disc not found: %s" % disc_path)

    print("Scanning %s" % disc_path)
    print("ISO size: %d bytes (%s)"
          % (os.path.getsize(disc_path),
             human_size(os.path.getsize(disc_path))))
    archives = find_dialogue_archives(disc_path, progress=True)

    if not archives:
        print("")
        print("No dialogue (bmgres.arc / RARC with zel_00.bmg) archive found.")
        print("Is this really a GameCube Wind Waker ISO?")
        return 1

    print("Dialogue archives found: %d" % len(archives))
    for index, archive in enumerate(archives):
        describe(archive, "candidate #%d" % index)
    print("")
    return 0


# ---------------------------------------------------------------------------
# Patching
# ---------------------------------------------------------------------------

def pick_single(archives, what):
    """Require exactly one archive, otherwise bail out with a clear message."""
    if len(archives) == 0:
        sys.exit("error: no dialogue archive found in the %s disc." % what)
    if len(archives) > 1:
        print("error: found %d dialogue archives in the %s disc, expected 1:"
              % (len(archives), what))
        for index, archive in enumerate(archives):
            describe(archive, "candidate #%d" % index)
        sys.exit("       cannot decide which one to patch; aborting.")
    return archives[0]


def pick_pal_archive(archives, language, index):
    """Choose the PAL archive for the requested language or explicit index."""
    if index is not None:
        if index < 0 or index >= len(archives):
            sys.exit("error: --index %d is out of range (0..%d)."
                     % (index, len(archives) - 1))
        print("Using PAL archive #%d (forced by --index)." % index)
        return archives[index]

    chosen = None
    for archive in archives:
        if archive.language == language:
            if chosen is None:
                chosen = archive
            else:
                # Two archives claim the same language -> ask the user.
                print("")
                print("error: ambiguous language detection: %d archives look "
                      "like '%s'." % (len([a for a in archives
                                           if a.language == language]),
                                      language))
                for number, candidate in enumerate(archives):
                    describe(candidate, "candidate #%d" % number)
                sys.exit("       please re-run with --index N to pick one.")
    if chosen is None:
        print("")
        print("error: no PAL archive was detected as '%s' (%s)."
              % (language, LANGUAGE_NAMES[language]))
        for number, candidate in enumerate(archives):
            describe(candidate, "candidate #%d" % number)
        sys.exit("       please re-run with --index N to pick one.")
    return chosen


def patch(usa_path, pal_path, out_path, language, index):
    """Do the actual work: copy the USA disc and graft the PAL text in."""
    for path, label in ((usa_path, "USA"), (pal_path, "PAL")):
        if not os.path.isfile(path):
            sys.exit("error: %s disc not found: %s" % (label, path))

    print("== locating the dialogue archive of the USA disc ==")
    usa_archives = find_dialogue_archives(usa_path, progress=True)
    usa = pick_single(usa_archives, "USA")
    describe(usa, "USA dialogue archive")

    print("")
    print("== locating the dialogue archives of the PAL disc ==")
    pal_archives = find_dialogue_archives(pal_path, progress=True)
    if not pal_archives:
        sys.exit("error: no dialogue archive found in the PAL disc.")
    print("PAL dialogue archives found: %d" % len(pal_archives))
    for number, archive in enumerate(pal_archives):
        describe(archive, "candidate #%d" % number)

    print("")
    print("== selecting the source language ==")
    print("Requested language: %s (%s)"
          % (language, LANGUAGE_NAMES[language]))
    source = pick_pal_archive(pal_archives, language, index)
    describe(source, "selected source archive")

    if source.size > usa.size:
        sys.exit(
            "error: the %s text does NOT fit into the USA disc.\n"
            "       source RARC = %d bytes, USA RARC = %d bytes "
            "(%d bytes too big).\n"
            "       A language bigger than the US text needs a full ISO "
            "rebuild (re-laying\n"
            "       the filesystem and rewriting the FST), which this tool "
            "does not do.\n"
            "       Languages that fit: French, Spanish and Italian."
            % (LANGUAGE_NAMES[source.language or language], source.size,
               usa.size, source.size - usa.size))

    print("")
    print("== writing %s ==" % out_path)
    if os.path.abspath(out_path) == os.path.abspath(usa_path):
        sys.exit("error: refusing to write the output over the input USA disc.")

    if not os.path.exists(out_path):
        print("   copying %s -> %s" % (usa_path, out_path))
        shutil.copyfile(usa_path, out_path)
    else:
        print("   %s already exists, reusing it as the base" % out_path)

    with open(pal_path, "rb") as pal_handle:
        payload = read_at(pal_handle, source.offset, source.size)
    if len(payload) != source.size or payload[:4] != RARC_MAGIC:
        sys.exit("error: could not read the full source RARC "
                 "(%d of %d bytes, magic %r)."
                 % (len(payload), source.size, payload[:4]))

    padding = usa.size - source.size
    with open(out_path, "r+b") as out_handle:
        out_handle.seek(usa.offset)
        out_handle.write(payload)
        if padding:
            # Zero-fill in chunks so we never build a huge bytes object.
            block = b"\x00" * min(padding, 4 * 1024 * 1024)
            remaining = padding
            while remaining:
                step = min(remaining, len(block))
                out_handle.write(block[:step])
                remaining -= step
        out_handle.flush()
        os.fsync(out_handle.fileno())

    print("   wrote %d bytes at 0x%08X + %d zero bytes"
          % (source.size, usa.offset, padding))

    print("")
    print("== verifying the result ==")
    final_size = os.path.getsize(out_path)
    with open(out_path, "rb") as out_handle:
        magic = read_at(out_handle, usa.offset, 4)
        written_size = u32be(read_at(out_handle, usa.offset, 16),
                             RARC_SIZE_OFFSET)
    ok = (magic == RARC_MAGIC and written_size == source.size
          and final_size == os.path.getsize(usa_path))
    print("   magic at 0x%08X : %r %s"
          % (usa.offset, magic, "OK" if magic == RARC_MAGIC else "BAD"))
    print("   RARC size written: %d bytes (expected %d) %s"
          % (written_size, source.size,
             "OK" if written_size == source.size else "BAD"))
    print("   output size      : %d bytes %s"
          % (final_size, "OK" if final_size == os.path.getsize(usa_path)
             else "BAD"))
    if not ok:
        sys.exit("error: verification failed.")
    print("")
    print("Done. %s now carries the %s text."
          % (out_path, LANGUAGE_NAMES[source.language or language]))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Inject PAL (GZLP01) Wind Waker text into a USA "
                    "(GZLE01) disc.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Only languages whose message archive is smaller than or "
               "equal to the US one can be injected this way "
               "(English, French, Spanish, Italian).")
    parser.add_argument("iso", nargs="*",
                        help="USA.iso PAL.iso OUTPUT.iso")
    parser.add_argument("--list", action="store_true",
                        help="list the dialogue archives of a disc and exit "
                             "(read only, writes nothing)")
    parser.add_argument("--disc",
                        help="disc to inspect together with --list")
    parser.add_argument("--language", choices=LANGUAGES, default="es",
                        help="source language taken from the PAL disc "
                             "(default: es)")
    parser.add_argument("--index", type=int, default=None,
                        help="use this PAL archive index (0-based) instead of "
                             "the automatic language detection")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.list:
        disc = args.disc
        if disc is None and len(args.iso) == 1:
            disc = args.iso[0]
        if disc is None:
            sys.exit("error: --list needs a disc, e.g. --list --disc ISO "
                     "or --list ISO")
        return run_list(disc)

    if len(args.iso) != 3:
        build_parser().print_help(sys.stderr)
        sys.exit("error: expected USA.iso PAL.iso OUTPUT.iso")
    return patch(args.iso[0], args.iso[1], args.iso[2],
                 args.language, args.index)


if __name__ == "__main__":
    sys.exit(main())
