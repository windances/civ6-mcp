"""Extract the text of a local PDF with nothing but the standard library.

There is no PDF library in this environment (`pypdf`, `pdfminer`, `pdfplumber`, `fitz` are all
absent), no `pdftotext`/`ghostscript`, and no outbound HTTPS from the shell to install one - so
turning a PDF the user has on disk into readable text needs a small extractor of our own.

How it works, in the order the file is read:
1. objects and streams are located by regex (accepting `\n`, `\r\n` **or `\r`** - the Civ VI
   manual is a linearized file that uses `\r` alone, which a `stream\r?\n` pattern misses
   entirely), and the FlateDecode streams are inflated with `zlib`;
2. every font object's `/ToUnicode` CMap is parsed (`beginbfchar` / `beginbfrange`) into its own
   table - **per font**, because one merged table mismaps: two subset fonts use the same byte for
   different letters, which is how "Intel" comes out as "fntel";
3. each page's own `/Resources /Font << /F1 12 0 R >>` maps the `Tf` operator's name to the right
   font for *that* page (resource names are page-local; using another page's table renders "The"
   as "("), and the content stream is walked in one pass: strings accumulate, `Tj`/`TJ` flush them
   through the current font's table, and a `Td`/`TD`/`T*`/`ET` with a real vertical move breaks the
   line. Glyphs the current font does not map fall back to the union of all tables, then to raw
   bytes - which is what keeps a `Th` ligature from silently vanishing.

    python .tools/pdf-text.py FILE.pdf [--max-streams N] [--raw] > out.txt

Limits, honestly: image-only/scanned pages have no text to find; a font with no usable
`ToUnicode` map comes out as mojibake (`--raw` shows the undecoded bytes, so it is visible rather
than silent); the layout is reconstructed from operator soup, so columns and tables are
approximate and reading order is the file's, not the page's; and it only reads files on this
machine - a PDF behind a URL has to be saved first.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_OBJECT = re.compile(rb"(\d+)\s+\d+\s+obj(.*?)endobj", re.DOTALL)
# An EOL before `endstream`, and any of the three EOL forms after `stream`: PDF 1.4 accepts \n,
# \r or \r\n, and this manual (a linearized 22 MB file) uses **\r alone** - which is why a
# `stream\r?\n` pattern found zero streams in it while `stream`/`endstream` were plainly there.
_STREAM = re.compile(rb"stream(?:\r\n|\n|\r)(.*?)(?:\r\n|\n|\r)endstream", re.DOTALL)
_FONT_DICT = re.compile(rb"/Type\s*/Font\b(.*?)(?:>>|endobj)", re.DOTALL)
_TO_UNICODE = re.compile(rb"/ToUnicode\s+(\d+)\s+\d+\s+R")
_FONT_RESOURCE = re.compile(rb"/Font\s*<<(.*?)>>", re.DOTALL)
_RESOURCE_ENTRY = re.compile(rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+\d+\s+R")
# Dictionary markers that mean "not a page content stream": images, colour profiles, metadata.
_SKIP_DICT = (
    b"/Image",
    b"/DCTDecode",
    b"/JPXDecode",
    b"/JBIG2Decode",
    b"/ICCBased",
    b"/Metadata",
    b"/XML",
    b"/EmbeddedFile",
)

# One pass over a content stream. Each alternative is a thing the walker reacts to; the string
# operands are the only ones with no capture group.
_ITEM = re.compile(
    rb"\((?:\\.|[^\\()])*\)"  # 0: literal string
    rb"|<[0-9A-Fa-f\s]*>"  # 1: hex string
    rb"|/([A-Za-z0-9_.+-]+)\s+[-\d.]+\s+Tf"  # 2: font select
    rb"|([-\d.]+)\s+([-\d.]+)\s+(?:Td|TD)"  # 3,4: position move (tx, ty)
    rb"|(?<![A-Za-z])(Tj|TJ|'|\"|T\*|ET)(?![A-Za-z])"  # 5: text / break operators
)


def inflate(chunk: bytes) -> bytes | None:
    """FlateDecode a stream body, tolerating the trailing whitespace PDF allows."""
    for candidate in (chunk, chunk.rstrip(b"\r\n"), chunk.strip()):
        try:
            return zlib.decompress(candidate)
        except zlib.error:
            continue
    try:  # a stream whose declared length was too long: take what decompresses
        return zlib.decompressobj().decompress(chunk)
    except zlib.error:
        return None


def _utf16_be(hex_text: bytes) -> str:
    raw = bytes.fromhex(hex_text.decode("ascii"))
    if len(raw) % 2 == 0:
        try:
            return raw.decode("utf-16-be")
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1", errors="replace")


def parse_cmap(body: bytes) -> dict[int, str]:
    """One ToUnicode CMap: code -> text."""
    table: dict[int, str] = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", body, re.DOTALL):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            table[int(src, 16)] = _utf16_be(dst)
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", body, re.DOTALL):
        for lo, hi, dst in re.findall(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block
        ):
            start, end, target = int(lo, 16), int(hi, 16), int(dst, 16)
            if end - start > 512:  # a runaway range is a parse error, not a font
                continue
            for offset in range(end - start + 1):
                table[start + offset] = chr(target + offset)
    return table


def font_tables(data: bytes, streams: dict[int, bytes]) -> tuple[dict[int, dict[int, str]],
                                                                 dict[bytes, dict[int, str]]]:
    """(font object -> CMap, resource name -> CMap)."""
    by_object: dict[int, dict[int, str]] = {}
    by_name: dict[bytes, dict[int, str]] = {}
    font_objects: list[int] = []
    for match in _OBJECT.finditer(data):
        obj_num = int(match.group(1))
        body = match.group(2)
        if not _FONT_DICT.search(body):
            continue
        font_objects.append(obj_num)
        to_unicode = _TO_UNICODE.search(body)
        if not to_unicode:
            continue
        cmap_body = streams.get(int(to_unicode.group(1)))
        if cmap_body and (b"beginbfchar" in cmap_body or b"beginbfrange" in cmap_body):
            by_object[obj_num] = parse_cmap(cmap_body)
    for resources in _FONT_RESOURCE.findall(data):
        for name, obj_num in _RESOURCE_ENTRY.findall(resources):
            table = by_object.get(int(obj_num))
            if table:
                by_name[name] = table
    return by_object, by_name


def decode_pdf_string(
    raw: bytes, cmap: dict[int, str] | None, merged: dict[int, str] | None = None
) -> str:
    """A PDF string operand: map it through the font's CMap when there is one, else read bytes.

    ``merged`` is the union of every font's table, used only as a second chance: a ligature or
    punctuation glyph that the current font does not map is often mapped by another one, and
    without that fallback those glyphs come out as raw bytes - which is how "The Basics" reads
    as "e Basics" (the `Th` ligature dropped) and stray \\xfe\\xff pairs appear in the text.
    """
    if not cmap and not merged:
        return raw.decode("latin-1", errors="replace")
    out: list[str] = []
    index = 0
    while index < len(raw):
        if index + 1 < len(raw):
            two = int.from_bytes(raw[index : index + 2], "big")
            if cmap and two in cmap:
                out.append(cmap[two])
                index += 2
                continue
            if merged and two in merged:
                out.append(merged[two])
                index += 2
                continue
        one = raw[index]
        char = None
        if cmap:
            char = cmap.get(one)
        if char is None and merged:
            char = merged.get(one)
        out.append(char if char is not None else bytes([one]).decode("latin-1", errors="replace"))
        index += 1
    return "".join(out)


def unescape_pdf(raw: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(raw):
        char = raw[i]
        if char != 0x5C:  # backslash
            out.append(char)
            i += 1
            continue
        i += 1
        if i >= len(raw):
            break
        nxt = raw[i]
        simple = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
        if nxt in simple:
            out.append(simple[nxt])
            i += 1
        elif 0x30 <= nxt <= 0x37:  # octal escape
            oct_digits = b""
            while i < len(raw) and len(oct_digits) < 3 and 0x30 <= raw[i] <= 0x37:
                oct_digits += bytes([raw[i]])
                i += 1
            out.append(int(oct_digits, 8) & 0xFF)
        else:
            out.append(nxt)
            i += 1
    return bytes(out)


def _operand(raw: bytes, cmap: dict[int, str] | None, raw_mode: bool, merged: dict[int, str] | None = None) -> str:
    if raw.startswith(b"<"):
        digits = re.sub(rb"\s", b"", raw[1:-1]).decode("ascii")
        if len(digits) % 2:
            digits += "0"
        data = bytes.fromhex(digits or "20")
    else:
        data = unescape_pdf(raw[1:-1])
    if raw_mode:
        return data.decode("latin-1", errors="replace")
    return decode_pdf_string(data, cmap, merged)


def content_text(body: bytes, by_name: dict[bytes, dict[int, str]], raw_mode: bool, merged: dict[int, str] | None = None) -> str:
    out: list[str] = []
    pending: list[str] = []
    cmap: dict[int, str] | None = None

    def flush() -> None:
        if pending:
            out.append("".join(pending))
            pending.clear()

    for match in _ITEM.finditer(body):
        if match.group(1) is not None:  # /F1 10 Tf
            flush()
            cmap = None if raw_mode else by_name.get(match.group(1))
            continue
        if match.group(2) is not None:  # tx ty Td
            try:
                ty = abs(float(match.group(3)))
            except ValueError:
                ty = 0.0
            if ty >= 1.5:  # a real vertical move is a new line; kerning is not
                flush()
                out.append("\n")
            continue
        operator = match.group(4)
        if operator in (b"Tj", b"TJ", b"'", b'"'):
            flush()
        elif operator in (b"T*", b"ET"):
            flush()
            out.append("\n")
        else:  # a string operand
            pending.append(_operand(match.group(0), cmap, raw_mode, merged))
    flush()
    return "".join(out)


def tidy(text: str) -> str:
    """Collapse the operator soup into readable lines without inventing structure."""
    text = text.replace("\ufeff", "")  # a CMap that maps a glyph to the BOM is a null map
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def page_fonts(data: bytes, objects: dict[int, bytes]) -> list[tuple[list[int], dict[bytes, int]]]:
    """Per page: its content stream object numbers in order, and its font-name -> font object map.

    The global `/Font <<...>>` scan is not good enough: resource names are page-local, so `/F1` on
    one page is a different font from `/F1` on the next, and using the wrong table renders "The"
    as "(" (the ligature code read through another font's map). Pages carry their own resources
    (or inherit them from `/Pages`), so they are read per page instead.
    """
    pages: list[tuple[list[int], dict[bytes, int]]] = []
    for body in objects.values():
        if not re.search(rb"/Type\s*/Page(?![A-Za-z])", body):
            continue
        contents: list[int] = []
        single = re.search(rb"/Contents\s+(\d+)\s+\d+\s+R", body)
        if single:
            contents.append(int(single.group(1)))
        array = re.search(rb"/Contents\s*\[(.*?)\]", body, re.DOTALL)
        if array:
            contents += [int(num) for num in re.findall(rb"(\d+)\s+\d+\s+R", array.group(1))]
        resources = body
        ref = re.search(rb"/Resources\s+(\d+)\s+\d+\s+R", body)
        if ref:
            resources = objects.get(int(ref.group(1)), b"")
        fonts: dict[bytes, int] = {}
        font_dict = re.search(rb"/Font\s*<<(.*?)>>", resources, re.DOTALL)
        if font_dict:
            for name, obj_num in re.findall(
                rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+\d+\s+R", font_dict.group(1)
            ):
                fonts[name] = int(obj_num)
        pages.append((contents, fonts))
    return pages


def extract(path: pathlib.Path, raw_mode: bool, max_streams: int) -> tuple[str, int, int]:
    """Return (text, inflated_streams, fonts_with_a_cmap)."""
    data = path.read_bytes()
    objects: dict[int, bytes] = {}
    streams: dict[int, bytes] = {}
    dicts: dict[int, bytes] = {}
    for match in _OBJECT.finditer(data):
        obj_num = int(match.group(1))
        body = match.group(2)
        objects[obj_num] = body
        chunk = _STREAM.search(body)
        if not chunk:
            continue
        inflated = inflate(chunk.group(1))
        if inflated is None:
            continue
        streams[obj_num] = inflated
        dicts[obj_num] = body[: chunk.start()]
    by_object, by_name = ({}, {}) if raw_mode else font_tables(data, streams)
    # Second chance for glyphs the current font does not map (ligatures, punctuation): the union
    # of every font's table, consulted only when the font's own table has no entry.
    merged = {} if raw_mode else {k: v for table in by_object.values() for k, v in table.items()}

    chunks: list[str] = []
    pages = [] if raw_mode else page_fonts(data, objects)
    if any(fonts for _, fonts in pages):
        # Page order, with each page's own fonts - the layout the reader expects.
        for contents, fonts in pages:
            page_map = {name: by_object[obj] for name, obj in fonts.items() if obj in by_object}
            for obj_num in contents:
                body = streams.get(obj_num)
                if body and b"BT" in body:
                    text = content_text(body, page_map, raw_mode, merged)
                    if text.strip():
                        chunks.append(text)
        return tidy("\n".join(chunks)), len(streams), len(by_object)

    shown = 0
    for obj_num, body in streams.items():
        if shown >= max_streams:
            break
        # A stream is a page's content only if its dictionary says nothing more exotic. Image
        # data can contain the bytes `Tj` by accident, which is how the first run put JPEG guts
        # at the top of the output.
        dictionary = dicts.get(obj_num, b"")
        if any(skip in dictionary for skip in _SKIP_DICT):
            continue
        if b"BT" not in body or (b"Tj" not in body and b"TJ" not in body):
            continue
        text = content_text(body, by_name, raw_mode, merged)
        if text.strip():
            chunks.append(text)
            shown += 1
    return tidy("\n".join(chunks)), len(streams), len(by_object)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf")
    ap.add_argument("--raw", action="store_true", help="skip the CMaps and show raw bytes")
    ap.add_argument("--max-streams", type=int, default=400)
    args = ap.parse_args()

    path = pathlib.Path(args.pdf)
    if not path.exists():
        print(f"missing: {path}")
        return 1
    text, streams, fonts = extract(path, args.raw, args.max_streams)
    print(
        f"# {path.name}: {path.stat().st_size:,} bytes, {streams} stream(s),"
        f" {fonts} font CMap(s)",
        file=sys.stderr,
    )
    if not text.strip():
        print(
            "# no text found - an image-only scan, or a font with no ToUnicode map"
            " (try --raw to see the undecoded bytes)",
            file=sys.stderr,
        )
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
