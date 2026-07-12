"""
Simple markdown-aware chunker.

Strategy: split the note into paragraphs (blank-line separated blocks --
this naturally keeps headings glued to the text that follows them most of
the time), then greedily pack paragraphs into chunks up to `chunk_size`
characters, carrying a small character overlap into the next chunk so
semantic context isn't lost at chunk boundaries. Each chunk remembers its
start/end line numbers in the source file so the UI can link/scroll to it.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    start_line: int  # 1-indexed, inclusive
    end_line: int  # 1-indexed, inclusive


def _split_paragraphs(text: str) -> list[tuple[str, int, int]]:
    lines = text.split("\n")
    paragraphs: list[tuple[str, int, int]] = []
    buf: list[str] = []
    start = None
    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            if buf:
                paragraphs.append(("\n".join(buf), start, i - 1))
                buf = []
                start = None
        else:
            if start is None:
                start = i
            buf.append(line)
    if buf:
        paragraphs.append(("\n".join(buf), start, len(lines)))
    return paragraphs


def chunk_markdown(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[Chunk]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    cur_parts: list[str] = []
    cur_start_line: int | None = None
    cur_end_line: int | None = None
    cur_len = 0

    def flush():
        nonlocal cur_parts, cur_start_line, cur_end_line, cur_len
        if cur_parts:
            chunks.append(
                Chunk(
                    text="\n\n".join(cur_parts).strip(),
                    start_line=cur_start_line,
                    end_line=cur_end_line,
                )
            )
        cur_parts, cur_start_line, cur_end_line, cur_len = [], None, None, 0

    for para_text, p_start, p_end in paragraphs:
        # A single oversized paragraph gets flushed on its own rather than
        # dropped or silently truncated.
        if cur_len > 0 and cur_len + len(para_text) > chunk_size:
            flush()
            # carry a bit of overlap forward from the tail of the last chunk
            if chunks and overlap > 0:
                tail = chunks[-1].text[-overlap:]
                cur_parts = [tail]
                cur_len = len(tail)
                cur_start_line = chunks[-1].end_line

        if cur_start_line is None:
            cur_start_line = p_start
        cur_end_line = p_end
        cur_parts.append(para_text)
        cur_len += len(para_text)

    flush()
    return [c for c in chunks if c.text.strip()]
